from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import BaseMessage
import google.generativeai as genai

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="AI Medical Diagnosis System")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database Models
class Patient(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    age: int
    gender: str
    email: str
    phone: Optional[str] = None
    medical_history: Optional[List[str]] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str
    email: str
    phone: Optional[str] = None
    medical_history: Optional[List[str]] = []

class Symptom(BaseModel):
    description: str
    severity: int = Field(ge=1, le=10, description="Severity from 1-10")
    duration: str
    location: Optional[str] = None

class DiagnosisRequest(BaseModel):
    patient_id: str
    symptoms: List[Symptom]
    additional_info: Optional[str] = None

class DiagnosisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    symptoms: List[Symptom]
    diagnosis: str
    recommendations: List[str]
    severity_assessment: str
    follow_up_needed: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: str

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    patient_id: str
    message: str
    sender: str  # "patient" or "doctor" or "ai"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    patient_id: str
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    session_id: str
    ai_response: str

class Doctor(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    specialty: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DoctorCreate(BaseModel):
    name: str
    specialty: str

class Appointment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    doctor_id: str
    appointment_time: datetime
    reason: str
    status: str  # e.g., "scheduled", "completed", "canceled"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AppointmentCreate(BaseModel):
    patient_id: str
    doctor_id: str
    appointment_time: datetime
    reason: str
    status: str = "scheduled"

# AI Medical Diagnosis System
class MedicalAI:
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Configure Google Generative AI
        genai.configure(api_key=self.api_key)
        
        # Initialize LangChain chat model
        self.chat_model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=self.api_key,
            temperature=0.7,
            max_tokens=2048
        )

    async def get_diagnosis(self, symptoms: List[Symptom], patient_age: int, patient_gender: str, medical_history: List[str], additional_info: str = None) -> Dict[str, Any]:
        """Get AI-powered medical diagnosis using Gemini 2.0 Flash"""
        
        # Create detailed symptom description
        symptom_details = []
        for symptom in symptoms:
            detail = f"- {symptom.description} (Severity: {symptom.severity}/10, Duration: {symptom.duration}"
            if symptom.location:
                detail += f", Location: {symptom.location}"
            detail += ")"
            symptom_details.append(detail)
        
        symptoms_text = "\n".join(symptom_details)
        history_text = ", ".join(medical_history) if medical_history else "None reported"
        
        # Create medical diagnosis prompt
        medical_prompt = f"""You are an experienced medical AI assistant specializing in differential diagnosis. Please analyze the following patient case and provide a comprehensive medical assessment.

Patient Information:
- Age: {patient_age}
- Gender: {patient_gender}
- Medical History: {history_text}

Current Symptoms:
{symptoms_text}

Additional Information: {additional_info if additional_info else "None provided"}

Please provide:
1. DIFFERENTIAL DIAGNOSIS: List 3-5 most likely diagnoses ranked by probability
2. DETAILED ANALYSIS: Explain the reasoning for each potential diagnosis
3. RECOMMENDATIONS: Specific medical recommendations including:
   - Immediate actions needed
   - Further tests or examinations required
   - Treatment suggestions
   - Lifestyle modifications
4. SEVERITY ASSESSMENT: Rate overall severity (Low/Moderate/High/Critical)
5. FOLLOW-UP: Whether immediate medical attention is needed

Important: This is for educational/informational purposes. Always recommend consulting with healthcare professionals for proper medical evaluation and treatment."""

        try:
            # Create system message
            system_message = SystemMessage(content="You are a professional medical AI assistant providing differential diagnosis and medical recommendations. Always emphasize the importance of professional medical consultation.")
            
            # Create human message
            human_message = HumanMessage(content=medical_prompt)
            
            # Get response from LangChain
            response = await self.chat_model.ainvoke([system_message, human_message])
            
            # Parse response for structured data
            diagnosis_text = response.content
            
            # Extract structured information
            recommendations = []
            if "RECOMMENDATIONS:" in diagnosis_text:
                rec_section = diagnosis_text.split("RECOMMENDATIONS:")[1]
                if "SEVERITY ASSESSMENT:" in rec_section:
                    rec_section = rec_section.split("SEVERITY ASSESSMENT:")[0]
                recommendations = [line.strip() for line in rec_section.split('\n') if line.strip() and not line.strip().startswith('-')]
            
            severity = "Moderate"
            if "SEVERITY ASSESSMENT:" in diagnosis_text:
                sev_section = diagnosis_text.split("SEVERITY ASSESSMENT:")[1]
                if "FOLLOW-UP:" in sev_section:
                    sev_section = sev_section.split("FOLLOW-UP:")[0]
                severity_line = sev_section.strip().split('\n')[0].strip()
                if any(word in severity_line.lower() for word in ['critical', 'high', 'severe']):
                    severity = "High"
                elif any(word in severity_line.lower() for word in ['low', 'mild']):
                    severity = "Low"
            
            follow_up_needed = True
            if "immediate medical attention" in diagnosis_text.lower() or "emergency" in diagnosis_text.lower() or "critical" in severity.lower():
                follow_up_needed = True
            
            return {
                "diagnosis": diagnosis_text,
                "recommendations": recommendations if recommendations else ["Consult with a healthcare professional", "Monitor symptoms closely", "Follow up if symptoms worsen"],
                "severity_assessment": severity,
                "follow_up_needed": follow_up_needed,
                "session_id": str(uuid.uuid4())
            }
            
        except Exception as e:
            logger.error(f"Error in AI diagnosis: {str(e)}")
            raise HTTPException(status_code=500, detail=f"AI diagnosis failed: {str(e)}")

    async def chat_with_patient(self, message: str, patient_id: str, session_id: str = None) -> Dict[str, str]:
        """Handle patient communication with AI medical assistant"""
        
        if not session_id:
            session_id = str(uuid.uuid4())
            
        # Get patient info for context
        patient_doc = await db.patients.find_one({"id": patient_id})
        if not patient_doc:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        patient = Patient(**patient_doc)
        
        # Get recent chat history for better context
        recent_messages = await db.chat_messages.find(
            {"session_id": session_id, "patient_id": patient_id}
        ).sort("timestamp", -1).limit(10).to_list(10)
        
        # Build context from chat history
        chat_context = ""
        if recent_messages:
            chat_context = "\n\nRecent conversation context:\n"
            for msg in reversed(recent_messages):
                sender = msg["sender"]
                content = msg["message"]
                chat_context += f"{sender}: {content}\n"
        
        medical_chat_prompt = f"""You are a compassionate medical AI assistant helping patients understand their health concerns. 

Patient Information:
- Name: {patient.name}
- Age: {patient.age}
- Gender: {patient.gender}
- Medical History: {', '.join(patient.medical_history) if patient.medical_history else 'None reported'}

{chat_context}

Current patient message: {message}

Please provide a helpful, empathetic response that:
1. Addresses their concerns professionally
2. Provides general health information when appropriate
3. Always recommends consulting healthcare professionals for medical advice
4. Asks relevant follow-up questions to better understand their condition
5. Maintains a warm, supportive tone

Remember: You are providing informational support, not medical diagnosis or treatment."""

        try:
            # Create system message
            system_message = SystemMessage(content="You are a helpful medical AI assistant focused on patient communication and support. Always recommend professional medical consultation.")
            
            # Create human message
            human_message = HumanMessage(content=medical_chat_prompt)
            
            # Get response from LangChain
            response = await self.chat_model.ainvoke([system_message, human_message])
            
            return {
                "response": response.content,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error in patient chat: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

# Initialize AI system
medical_ai = MedicalAI()

# API Endpoints

@api_router.get("/")
async def root():
    return {"message": "AI Medical Diagnosis System", "status": "active"}

# Patient Management
@api_router.post("/patients", response_model=Patient)
async def create_patient(patient_data: PatientCreate):
    """Create a new patient record"""
    try:
        patient = Patient(**patient_data.dict())
        await db.patients.insert_one(patient.dict())
        return patient
    except Exception as e:
        logger.error(f"Error creating patient: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create patient")

@api_router.get("/patients", response_model=List[Patient])
async def get_patients():
    """Get all patient records"""
    try:
        patients = await db.patients.find().to_list(100)
        return [Patient(**patient) for patient in patients]
    except Exception as e:
        logger.error(f"Error fetching patients: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch patients")

@api_router.get("/patients/{patient_id}", response_model=Patient)
async def get_patient(patient_id: str):
    """Get specific patient by ID"""
    try:
        patient_doc = await db.patients.find_one({"id": patient_id})
        if not patient_doc:
            raise HTTPException(status_code=404, detail="Patient not found")
        return Patient(**patient_doc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching patient: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch patient")

# Medical Diagnosis
@api_router.post("/diagnosis", response_model=DiagnosisResult)
async def get_medical_diagnosis(request: DiagnosisRequest):
    """Get AI-powered medical diagnosis"""
    try:
        # Get patient info
        patient_doc = await db.patients.find_one({"id": request.patient_id})
        if not patient_doc:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        patient = Patient(**patient_doc)
        
        # Get AI diagnosis
        ai_result = await medical_ai.get_diagnosis(
            symptoms=request.symptoms,
            patient_age=patient.age,
            patient_gender=patient.gender,
            medical_history=patient.medical_history,
            additional_info=request.additional_info
        )
        
        # Create diagnosis record
        diagnosis = DiagnosisResult(
            patient_id=request.patient_id,
            symptoms=request.symptoms,
            diagnosis=ai_result["diagnosis"],
            recommendations=ai_result["recommendations"],
            severity_assessment=ai_result["severity_assessment"],
            follow_up_needed=ai_result["follow_up_needed"],
            session_id=ai_result["session_id"]
        )
        
        # Save to database
        await db.diagnoses.insert_one(diagnosis.dict())
        
        return diagnosis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in diagnosis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")

@api_router.get("/patients/{patient_id}/diagnoses", response_model=List[DiagnosisResult])
async def get_patient_diagnoses(patient_id: str):
    """Get all diagnoses for a patient"""
    try:
        diagnoses = await db.diagnoses.find({"patient_id": patient_id}).sort("created_at", -1).to_list(50)
        return [DiagnosisResult(**diagnosis) for diagnosis in diagnoses]
    except Exception as e:
        logger.error(f"Error fetching diagnoses: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch diagnoses")

# Patient Communication
@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """Chat with AI medical assistant"""
    try:
        # Verify patient exists
        patient_doc = await db.patients.find_one({"id": request.patient_id})
        if not patient_doc:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get AI response
        ai_result = await medical_ai.chat_with_patient(
            message=request.message,
            patient_id=request.patient_id,
            session_id=request.session_id
        )
        
        session_id = ai_result["session_id"]
        
        # Save patient message
        patient_message = ChatMessage(
            session_id=session_id,
            patient_id=request.patient_id,
            message=request.message,
            sender="patient"
        )
        await db.chat_messages.insert_one(patient_message.dict())
        
        # Save AI response
        ai_message = ChatMessage(
            session_id=session_id,
            patient_id=request.patient_id,
            message=ai_result["response"],
            sender="ai"
        )
        await db.chat_messages.insert_one(ai_message.dict())
        
        return ChatResponse(
            message=request.message,
            session_id=session_id,
            ai_response=ai_result["response"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@api_router.get("/chat/{session_id}", response_model=List[ChatMessage])
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    try:
        messages = await db.chat_messages.find({"session_id": session_id}).sort("timestamp", 1).to_list(100)
        return [ChatMessage(**message) for message in messages]
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch chat history")

@api_router.get("/patients/{patient_id}/chats")
async def get_patient_chat_sessions(patient_id: str):
    """Get all chat sessions for a patient"""
    try:
        # Get unique session IDs for this patient
        pipeline = [
            {"$match": {"patient_id": patient_id}},
            {"$group": {
                "_id": "$session_id",
                "last_message": {"$max": "$timestamp"},
                "message_count": {"$sum": 1}
            }},
            {"$sort": {"last_message": -1}}
        ]
        sessions = await db.chat_messages.aggregate(pipeline).to_list(50)
        return sessions
    except Exception as e:
        logger.error(f"Error fetching chat sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch chat sessions")

# Doctor Management
@api_router.post("/doctors", response_model=Doctor)
async def create_doctor(doctor_data: DoctorCreate):
    """Create a new doctor record"""
    try:
        doctor = Doctor(**doctor_data.dict())
        await db.doctors.insert_one(doctor.dict())
        return doctor
    except Exception as e:
        logger.error(f"Error creating doctor: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create doctor")

@api_router.get("/doctors", response_model=List[Doctor])
async def get_doctors():
    """Get all doctor records"""
    try:
        doctors = await db.doctors.find().to_list(100)
        return [Doctor(**doctor) for doctor in doctors]
    except Exception as e:
        logger.error(f"Error fetching doctors: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch doctors")

@api_router.get("/doctors/{doctor_id}", response_model=Doctor)
async def get_doctor(doctor_id: str):
    """Get specific doctor by ID"""
    try:
        doctor_doc = await db.doctors.find_one({"id": doctor_id})
        if not doctor_doc:
            raise HTTPException(status_code=404, detail="Doctor not found")
        return Doctor(**doctor_doc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching doctor: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch doctor")

# Appointment Management
@api_router.post("/appointments", response_model=Appointment)
async def create_appointment(appointment_data: AppointmentCreate):
    """Create a new appointment"""
    try:
        # Verify patient and doctor exist
        patient_doc = await db.patients.find_one({"id": appointment_data.patient_id})
        if not patient_doc:
            raise HTTPException(status_code=404, detail=f"Patient with id {appointment_data.patient_id} not found")

        doctor_doc = await db.doctors.find_one({"id": appointment_data.doctor_id})
        if not doctor_doc:
            raise HTTPException(status_code=404, detail=f"Doctor with id {appointment_data.doctor_id} not found")

        appointment = Appointment(**appointment_data.dict())
        await db.appointments.insert_one(appointment.dict())
        return appointment
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Error creating appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create appointment")

@api_router.get("/appointments", response_model=List[Appointment])
async def get_appointments():
    """Get all appointments"""
    try:
        appointments = await db.appointments.find().to_list(100)
        return [Appointment(**appointment) for appointment in appointments]
    except Exception as e:
        logger.error(f"Error fetching appointments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch appointments")

@api_router.get("/appointments/{appointment_id}", response_model=Appointment)
async def get_appointment(appointment_id: str):
    """Get specific appointment by ID"""
    try:
        appointment_doc = await db.appointments.find_one({"id": appointment_id})
        if not appointment_doc:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return Appointment(**appointment_doc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch appointment")

@api_router.put("/appointments/{appointment_id}", response_model=Appointment)
async def update_appointment(appointment_id: str, appointment_data: AppointmentCreate):
    """Update an appointment"""
    try:
        # Verify patient and doctor exist
        patient_doc = await db.patients.find_one({"id": appointment_data.patient_id})
        if not patient_doc:
            raise HTTPException(status_code=404, detail=f"Patient with id {appointment_data.patient_id} not found")

        doctor_doc = await db.doctors.find_one({"id": appointment_data.doctor_id})
        if not doctor_doc:
            raise HTTPException(status_code=404, detail=f"Doctor with id {appointment_data.doctor_id} not found")

        updated_appointment = await db.appointments.find_one_and_update(
            {"id": appointment_id},
            {"$set": appointment_data.dict()},
            return_document=True
        )
        if not updated_appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return Appointment(**updated_appointment)
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Error updating appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update appointment")

@api_router.delete("/appointments/{appointment_id}", response_model=dict)
async def delete_appointment(appointment_id: str):
    """Delete an appointment"""
    try:
        result = await db.appointments.delete_one({"id": appointment_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return {"message": "Appointment deleted successfully"}
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Error deleting appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete appointment")


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI Medical Diagnosis System"}