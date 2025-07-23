import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentView, setCurrentView] = useState('home');
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [diagnosisResult, setDiagnosisResult] = useState(null);
  const [chatSession, setChatSession] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Patient Registration Form State
  const [patientForm, setPatientForm] = useState({
    name: '',
    age: '',
    gender: 'male',
    email: '',
    phone: '',
    medical_history: []
  });

  // Diagnosis Form State
  const [diagnosisForm, setDiagnosisForm] = useState({
    symptoms: [{ description: '', severity: 5, duration: '', location: '' }],
    additional_info: ''
  });

  // Chat State
  const [chatInput, setChatInput] = useState('');

  // Load patients on component mount
  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    try {
      const response = await axios.get(`${API}/patients`);
      setPatients(response.data);
    } catch (error) {
      console.error('Error loading patients:', error);
    }
  };

  const handlePatientSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const formData = {
        ...patientForm,
        age: parseInt(patientForm.age),
        medical_history: patientForm.medical_history.filter(h => h.trim())
      };
      
      const response = await axios.post(`${API}/patients`, formData);
      setPatients([...patients, response.data]);
      setPatientForm({ name: '', age: '', gender: 'male', email: '', phone: '', medical_history: [] });
      setCurrentView('patients');
      alert('Patient registered successfully!');
    } catch (error) {
      console.error('Error creating patient:', error);
      alert('Error registering patient. Please try again.');
    }
    setIsLoading(false);
  };

  const handleDiagnosisSubmit = async (e) => {
    e.preventDefault();
    if (!selectedPatient) {
      alert('Please select a patient first');
      return;
    }
    
    setIsLoading(true);
    try {
      const formData = {
        patient_id: selectedPatient.id,
        symptoms: diagnosisForm.symptoms.map(s => ({
          ...s,
          severity: parseInt(s.severity)
        })),
        additional_info: diagnosisForm.additional_info
      };
      
      const response = await axios.post(`${API}/diagnosis`, formData);
      setDiagnosisResult(response.data);
      setCurrentView('diagnosis-result');
    } catch (error) {
      console.error('Error getting diagnosis:', error);
      alert('Error getting diagnosis. Please try again.');
    }
    setIsLoading(false);
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || !selectedPatient) return;
    
    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/chat`, {
        patient_id: selectedPatient.id,
        message: chatInput,
        session_id: chatSession
      });
      
      setChatSession(response.data.session_id);
      setChatMessages([
        ...chatMessages,
        { sender: 'patient', message: chatInput, timestamp: new Date() },
        { sender: 'ai', message: response.data.ai_response, timestamp: new Date() }
      ]);
      setChatInput('');
    } catch (error) {
      console.error('Error in chat:', error);
      alert('Error sending message. Please try again.');
    }
    setIsLoading(false);
  };

  const addSymptom = () => {
    setDiagnosisForm({
      ...diagnosisForm,
      symptoms: [...diagnosisForm.symptoms, { description: '', severity: 5, duration: '', location: '' }]
    });
  };

  const updateSymptom = (index, field, value) => {
    const newSymptoms = [...diagnosisForm.symptoms];
    newSymptoms[index][field] = value;
    setDiagnosisForm({ ...diagnosisForm, symptoms: newSymptoms });
  };

  const removeSymptom = (index) => {
    const newSymptoms = diagnosisForm.symptoms.filter((_, i) => i !== index);
    setDiagnosisForm({ ...diagnosisForm, symptoms: newSymptoms });
  };

  const addMedicalHistory = () => {
    setPatientForm({
      ...patientForm,
      medical_history: [...patientForm.medical_history, '']
    });
  };

  const updateMedicalHistory = (index, value) => {
    const newHistory = [...patientForm.medical_history];
    newHistory[index] = value;
    setPatientForm({ ...patientForm, medical_history: newHistory });
  };

  const removeMedicalHistory = (index) => {
    const newHistory = patientForm.medical_history.filter((_, i) => i !== index);
    setPatientForm({ ...patientForm, medical_history: newHistory });
  };

  const renderNavigation = () => (
    <nav className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 shadow-lg">
      <div className="container mx-auto">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">🏥 AI Medical Diagnosis System</h1>
          <div className="space-x-4">
            <button 
              onClick={() => setCurrentView('home')}
              className={`px-4 py-2 rounded-lg transition-all ${currentView === 'home' ? 'bg-white text-blue-600' : 'hover:bg-blue-500'}`}
            >
              Home
            </button>
            <button 
              onClick={() => setCurrentView('register')}
              className={`px-4 py-2 rounded-lg transition-all ${currentView === 'register' ? 'bg-white text-blue-600' : 'hover:bg-blue-500'}`}
            >
              Register Patient
            </button>
            <button 
              onClick={() => setCurrentView('patients')}
              className={`px-4 py-2 rounded-lg transition-all ${currentView === 'patients' ? 'bg-white text-blue-600' : 'hover:bg-blue-500'}`}
            >
              Patients
            </button>
            <button 
              onClick={() => setCurrentView('diagnosis')}
              className={`px-4 py-2 rounded-lg transition-all ${currentView === 'diagnosis' ? 'bg-white text-blue-600' : 'hover:bg-blue-500'}`}
            >
              Diagnosis
            </button>
            <button 
              onClick={() => setCurrentView('chat')}
              className={`px-4 py-2 rounded-lg transition-all ${currentView === 'chat' ? 'bg-white text-blue-600' : 'hover:bg-blue-500'}`}
            >
              Chat
            </button>
          </div>
        </div>
      </div>
    </nav>
  );

  const renderHome = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="container mx-auto px-4 py-12">
        <div className="text-center">
          <h2 className="text-5xl font-bold text-gray-800 mb-6">AI-Enhanced Medical Diagnosis</h2>
          <p className="text-xl text-gray-600 mb-12 max-w-3xl mx-auto">
            Advanced AI-powered medical diagnosis and patient communication system using Gemini 2.0 Flash technology. 
            Get comprehensive medical assessments and maintain seamless communication with patients.
          </p>
          
          <div className="grid md:grid-cols-3 gap-8 mb-12">
            <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition-all">
              <div className="text-4xl mb-4">🔬</div>
              <h3 className="text-xl font-semibold mb-4">AI Diagnosis</h3>
              <p className="text-gray-600">Advanced differential diagnosis using state-of-the-art AI technology for accurate medical assessments.</p>
            </div>
            
            <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition-all">
              <div className="text-4xl mb-4">💬</div>
              <h3 className="text-xl font-semibold mb-4">Patient Communication</h3>
              <p className="text-gray-600">Seamless AI-powered chat system for patient support and medical guidance.</p>
            </div>
            
            <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition-all">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-xl font-semibold mb-4">Medical Records</h3>
              <p className="text-gray-600">Comprehensive patient record management with diagnosis history and tracking.</p>
            </div>
          </div>
          
          <div className="space-x-4">
            <button 
              onClick={() => setCurrentView('register')}
              className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all"
            >
              Register New Patient
            </button>
            <button 
              onClick={() => setCurrentView('diagnosis')}
              className="bg-white text-blue-600 border-2 border-blue-600 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-50 transition-all"
            >
              Start Diagnosis
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderPatientRegistration = () => (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h2 className="text-3xl font-bold text-gray-800 mb-8">Register New Patient</h2>
        
        <form onSubmit={handlePatientSubmit} className="bg-white p-8 rounded-xl shadow-lg">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Full Name *</label>
              <input
                type="text"
                required
                value={patientForm.name}
                onChange={(e) => setPatientForm({ ...patientForm, name: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter patient name"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Age *</label>
              <input
                type="number"
                required
                min="0"
                max="150"
                value={patientForm.age}
                onChange={(e) => setPatientForm({ ...patientForm, age: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter age"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Gender *</label>
              <select
                value={patientForm.gender}
                onChange={(e) => setPatientForm({ ...patientForm, gender: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email *</label>
              <input
                type="email"
                required
                value={patientForm.email}
                onChange={(e) => setPatientForm({ ...patientForm, email: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter email address"
              />
            </div>
          </div>
          
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
            <input
              type="tel"
              value={patientForm.phone}
              onChange={(e) => setPatientForm({ ...patientForm, phone: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter phone number (optional)"
            />
          </div>
          
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Medical History</label>
            {patientForm.medical_history.map((history, index) => (
              <div key={index} className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={history}
                  onChange={(e) => updateMedicalHistory(index, e.target.value)}
                  className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter medical condition"
                />
                <button
                  type="button"
                  onClick={() => removeMedicalHistory(index)}
                  className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
                >
                  Remove
                </button>
              </div>
            ))}
            <button
              type="button"
              onClick={addMedicalHistory}
              className="mt-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
            >
              Add Medical History
            </button>
          </div>
          
          <div className="mt-8">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50"
            >
              {isLoading ? 'Registering...' : 'Register Patient'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  const renderPatients = () => (
    <div className="container mx-auto px-4 py-8">
      <h2 className="text-3xl font-bold text-gray-800 mb-8">Patient Records</h2>
      
      <div className="grid gap-6">
        {patients.map((patient) => (
          <div key={patient.id} className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-xl font-semibold text-gray-800">{patient.name}</h3>
                <p className="text-gray-600">Age: {patient.age} | Gender: {patient.gender}</p>
                <p className="text-gray-600">Email: {patient.email}</p>
                {patient.phone && <p className="text-gray-600">Phone: {patient.phone}</p>}
                {patient.medical_history && patient.medical_history.length > 0 && (
                  <p className="text-gray-600">Medical History: {patient.medical_history.join(', ')}</p>
                )}
              </div>
              <div className="space-x-2">
                <button
                  onClick={() => {
                    setSelectedPatient(patient);
                    setCurrentView('diagnosis');
                  }}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                >
                  Diagnose
                </button>
                <button
                  onClick={() => {
                    setSelectedPatient(patient);
                    setChatMessages([]);
                    setChatSession(null);
                    setCurrentView('chat');
                  }}
                  className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
                >
                  Chat
                </button>
              </div>
            </div>
          </div>
        ))}
        
        {patients.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No patients registered yet.</p>
            <button
              onClick={() => setCurrentView('register')}
              className="mt-4 px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              Register First Patient
            </button>
          </div>
        )}
      </div>
    </div>
  );

  const renderDiagnosis = () => (
    <div className="container mx-auto px-4 py-8">
      <h2 className="text-3xl font-bold text-gray-800 mb-8">AI Medical Diagnosis</h2>
      
      {!selectedPatient && (
        <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg mb-6">
          <p className="text-yellow-800">Please select a patient first from the Patients page.</p>
        </div>
      )}
      
      {selectedPatient && (
        <div className="max-w-4xl mx-auto">
          <div className="bg-blue-50 p-4 rounded-lg mb-6">
            <h3 className="font-semibold">Selected Patient: {selectedPatient.name}</h3>
            <p className="text-sm text-gray-600">Age: {selectedPatient.age} | Gender: {selectedPatient.gender}</p>
          </div>
          
          <form onSubmit={handleDiagnosisSubmit} className="bg-white p-8 rounded-xl shadow-lg">
            <h3 className="text-xl font-semibold mb-6">Symptom Assessment</h3>
            
            {diagnosisForm.symptoms.map((symptom, index) => (
              <div key={index} className="border border-gray-200 p-4 rounded-lg mb-4">
                <div className="flex justify-between items-center mb-4">
                  <h4 className="font-medium">Symptom {index + 1}</h4>
                  {diagnosisForm.symptoms.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeSymptom(index)}
                      className="text-red-500 hover:text-red-700"
                    >
                      Remove
                    </button>
                  )}
                </div>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Description *</label>
                    <input
                      type="text"
                      required
                      value={symptom.description}
                      onChange={(e) => updateSymptom(index, 'description', e.target.value)}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Describe the symptom"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Severity (1-10) *</label>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={symptom.severity}
                      onChange={(e) => updateSymptom(index, 'severity', e.target.value)}
                      className="w-full"
                    />
                    <div className="text-center text-sm text-gray-600 mt-1">
                      Level: {symptom.severity}/10
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Duration *</label>
                    <input
                      type="text"
                      required
                      value={symptom.duration}
                      onChange={(e) => updateSymptom(index, 'duration', e.target.value)}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="e.g., 2 days, 1 week"
                    />
                  </div>
                  
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Location (optional)</label>
                    <input
                      type="text"
                      value={symptom.location}
                      onChange={(e) => updateSymptom(index, 'location', e.target.value)}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="e.g., chest, abdomen, head"
                    />
                  </div>
                </div>
              </div>
            ))}
            
            <button
              type="button"
              onClick={addSymptom}
              className="mb-6 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
            >
              Add Another Symptom
            </button>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Additional Information</label>
              <textarea
                value={diagnosisForm.additional_info}
                onChange={(e) => setDiagnosisForm({ ...diagnosisForm, additional_info: e.target.value })}
                rows="4"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Any additional information about the symptoms or condition"
              />
            </div>
            
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50"
            >
              {isLoading ? 'Getting AI Diagnosis...' : 'Get AI Diagnosis'}
            </button>
          </form>
        </div>
      )}
    </div>
  );

  const renderDiagnosisResult = () => (
    <div className="container mx-auto px-4 py-8">
      <h2 className="text-3xl font-bold text-gray-800 mb-8">AI Diagnosis Result</h2>
      
      {diagnosisResult && (
        <div className="max-w-4xl mx-auto">
          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="mb-6">
              <h3 className="text-xl font-semibold mb-2">Patient: {selectedPatient?.name}</h3>
              <p className="text-gray-600">Diagnosis Date: {new Date(diagnosisResult.created_at).toLocaleDateString()}</p>
            </div>
            
            <div className="mb-6">
              <h4 className="text-lg font-semibold mb-3">Reported Symptoms:</h4>
              <div className="space-y-2">
                {diagnosisResult.symptoms.map((symptom, index) => (
                  <div key={index} className="bg-gray-50 p-3 rounded-lg">
                    <p><strong>Description:</strong> {symptom.description}</p>
                    <p><strong>Severity:</strong> {symptom.severity}/10 | <strong>Duration:</strong> {symptom.duration}</p>
                    {symptom.location && <p><strong>Location:</strong> {symptom.location}</p>}
                  </div>
                ))}
              </div>
            </div>
            
            <div className="mb-6">
              <h4 className="text-lg font-semibold mb-3">AI Medical Assessment:</h4>
              <div className="bg-blue-50 p-4 rounded-lg">
                <pre className="whitespace-pre-wrap text-sm">{diagnosisResult.diagnosis}</pre>
              </div>
            </div>
            
            <div className="mb-6">
              <h4 className="text-lg font-semibold mb-3">Recommendations:</h4>
              <ul className="list-disc list-inside space-y-1">
                {diagnosisResult.recommendations.map((rec, index) => (
                  <li key={index} className="text-gray-700">{rec}</li>
                ))}
              </ul>
            </div>
            
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-yellow-50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">Severity Assessment:</h4>
                <p className={`font-medium ${diagnosisResult.severity_assessment === 'High' ? 'text-red-600' : 
                  diagnosisResult.severity_assessment === 'Moderate' ? 'text-yellow-600' : 'text-green-600'}`}>
                  {diagnosisResult.severity_assessment}
                </p>
              </div>
              
              <div className="bg-purple-50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">Follow-up Needed:</h4>
                <p className={`font-medium ${diagnosisResult.follow_up_needed ? 'text-red-600' : 'text-green-600'}`}>
                  {diagnosisResult.follow_up_needed ? 'Yes - Please consult a healthcare professional' : 'Monitor symptoms'}
                </p>
              </div>
            </div>
            
            <div className="mt-8 flex space-x-4">
              <button
                onClick={() => setCurrentView('diagnosis')}
                className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              >
                New Diagnosis
              </button>
              <button
                onClick={() => {
                  setChatMessages([]);
                  setChatSession(null);
                  setCurrentView('chat');
                }}
                className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600"
              >
                Chat with AI
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderChat = () => (
    <div className="container mx-auto px-4 py-8">
      <h2 className="text-3xl font-bold text-gray-800 mb-8">AI Medical Assistant Chat</h2>
      
      {!selectedPatient && (
        <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg mb-6">
          <p className="text-yellow-800">Please select a patient first from the Patients page.</p>
        </div>
      )}
      
      {selectedPatient && (
        <div className="max-w-4xl mx-auto">
          <div className="bg-blue-50 p-4 rounded-lg mb-6">
            <h3 className="font-semibold">Chatting with AI Assistant for: {selectedPatient.name}</h3>
            <p className="text-sm text-gray-600">Get medical guidance and support</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg">
            <div className="h-96 overflow-y-auto p-6 border-b">
              {chatMessages.length === 0 && (
                <div className="text-center text-gray-500 py-12">
                  <p>Start a conversation with the AI medical assistant</p>
                  <p className="text-sm mt-2">Ask about symptoms, medical questions, or health concerns</p>
                </div>
              )}
              
              {chatMessages.map((message, index) => (
                <div key={index} className={`mb-4 ${message.sender === 'patient' ? 'flex justify-end' : 'flex justify-start'}`}>
                  <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.sender === 'patient' 
                      ? 'bg-blue-500 text-white' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    <p className="text-sm">{message.message}</p>
                    <p className="text-xs mt-1 opacity-70">
                      {message.sender === 'patient' ? 'You' : 'AI Assistant'} • {new Date(message.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
            
            <form onSubmit={handleChatSubmit} className="p-6">
              <div className="flex gap-4">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Ask the AI assistant about your health concerns..."
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading || !chatInput.trim()}
                  className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Sending...' : 'Send'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {renderNavigation()}
      
      {currentView === 'home' && renderHome()}
      {currentView === 'register' && renderPatientRegistration()}
      {currentView === 'patients' && renderPatients()}
      {currentView === 'diagnosis' && renderDiagnosis()}
      {currentView === 'diagnosis-result' && renderDiagnosisResult()}
      {currentView === 'chat' && renderChat()}
    </div>
  );
}

export default App;