#!/usr/bin/env python3
"""
Comprehensive Backend Testing for AI Enhanced Medical Diagnosis System
Tests all backend API endpoints and functionality
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend environment
BACKEND_URL = "https://9730001b-7bd4-4ff2-85e2-0898283d86c7.preview.emergentagent.com/api"

class MedicalSystemTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.created_patient_id = None
        self.diagnosis_session_id = None
        self.chat_session_id = None
        
    async def setup(self):
        """Setup test session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()
        
    async def test_health_check(self):
        """Test basic health check endpoint"""
        try:
            async with self.session.get(f"{BACKEND_URL.replace('/api', '')}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("Health Check", True, f"Status: {data.get('status', 'unknown')}")
                    return True
                else:
                    self.log_test("Health Check", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_test("Health Check", False, error=str(e))
            return False
            
    async def test_root_endpoint(self):
        """Test root API endpoint"""
        try:
            async with self.session.get(f"{BACKEND_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("Root Endpoint", True, f"Message: {data.get('message', 'N/A')}")
                    return True
                else:
                    self.log_test("Root Endpoint", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_test("Root Endpoint", False, error=str(e))
            return False

    async def test_create_patient(self):
        """Test patient creation"""
        patient_data = {
            "name": "Sarah Johnson",
            "age": 34,
            "gender": "Female",
            "email": "sarah.johnson@email.com",
            "phone": "+1-555-0123",
            "medical_history": ["Hypertension", "Seasonal allergies", "Previous appendectomy (2018)"]
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/patients",
                json=patient_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.created_patient_id = data.get("id")
                    self.log_test("Create Patient", True, f"Created patient ID: {self.created_patient_id}")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("Create Patient", False, f"HTTP {response.status}", error_text)
                    return False
        except Exception as e:
            self.log_test("Create Patient", False, error=str(e))
            return False

    async def test_get_patients(self):
        """Test getting all patients"""
        try:
            async with self.session.get(f"{BACKEND_URL}/patients") as response:
                if response.status == 200:
                    data = await response.json()
                    patient_count = len(data) if isinstance(data, list) else 0
                    self.log_test("Get All Patients", True, f"Retrieved {patient_count} patients")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("Get All Patients", False, f"HTTP {response.status}", error_text)
                    return False
        except Exception as e:
            self.log_test("Get All Patients", False, error=str(e))
            return False

    async def test_get_patient_by_id(self):
        """Test getting specific patient by ID"""
        if not self.created_patient_id:
            self.log_test("Get Patient By ID", False, "No patient ID available from creation test")
            return False
            
        try:
            async with self.session.get(f"{BACKEND_URL}/patients/{self.created_patient_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    patient_name = data.get("name", "Unknown")
                    self.log_test("Get Patient By ID", True, f"Retrieved patient: {patient_name}")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("Get Patient By ID", False, f"HTTP {response.status}", error_text)
                    return False
        except Exception as e:
            self.log_test("Get Patient By ID", False, error=str(e))
            return False

    async def test_ai_diagnosis(self):
        """Test AI medical diagnosis functionality"""
        if not self.created_patient_id:
            self.log_test("AI Medical Diagnosis", False, "No patient ID available")
            return False
            
        diagnosis_request = {
            "patient_id": self.created_patient_id,
            "symptoms": [
                {
                    "description": "Persistent headache with throbbing pain",
                    "severity": 7,
                    "duration": "3 days",
                    "location": "Frontal and temporal regions"
                },
                {
                    "description": "Nausea and sensitivity to light",
                    "severity": 6,
                    "duration": "2 days",
                    "location": "General"
                },
                {
                    "description": "Mild fever",
                    "severity": 4,
                    "duration": "1 day"
                }
            ],
            "additional_info": "Symptoms started after working long hours on computer. No recent travel or illness exposure."
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/diagnosis",
                json=diagnosis_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.diagnosis_session_id = data.get("session_id")
                    diagnosis_text = data.get("diagnosis", "")
                    severity = data.get("severity_assessment", "Unknown")
                    recommendations_count = len(data.get("recommendations", []))
                    
                    self.log_test("AI Medical Diagnosis", True, 
                                f"Diagnosis generated (Severity: {severity}, {recommendations_count} recommendations)")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("AI Medical Diagnosis", False, f"HTTP {response.status}", error_text)
                    return False
        except Exception as e:
            self.log_test("AI Medical Diagnosis", False, error=str(e))
            return False

    async def test_get_patient_diagnoses(self):
        """Test getting patient diagnosis history"""
        if not self.created_patient_id:
            self.log_test("Get Patient Diagnoses", False, "No patient ID available")
            return False
            
        try:
            async with self.session.get(f"{BACKEND_URL}/patients/{self.created_patient_id}/diagnoses") as response:
                if response.status == 200:
                    data = await response.json()
                    diagnosis_count = len(data) if isinstance(data, list) else 0
                    self.log_test("Get Patient Diagnoses", True, f"Retrieved {diagnosis_count} diagnoses")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("Get Patient Diagnoses", False, f"HTTP {response.status}", error_text)
                    return False
        except Exception as e:
            self.log_test("Get Patient Diagnoses", False, error=str(e))
            return False

    async def test_patient_chat(self):
        """Test patient-AI chat communication"""
        if not self.created_patient_id:
            self.log_test("Patient Chat", False, "No patient ID available")
            return False
            
        chat_request = {
            "patient_id": self.created_patient_id,
            "message": "I'm concerned about my headache symptoms. Should I be worried about the severity? What can I do to manage the pain while waiting to see a doctor?"
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/chat",
                json=chat_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.chat_session_id = data.get("session_id")
                    ai_response = data.get("ai_response", "")
                    response_length = len(ai_response)
                    
                    self.log_test("Patient Chat", True, 
                                f"AI response generated ({response_length} characters)")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("Patient Chat", False, f"HTTP {response.status}", error_text)
                    return False
        except Exception as e:
            self.log_test("Patient Chat", False, error=str(e))
            return False

    async def test_chat_history(self):
        """Test getting chat history"""
        if not self.chat_session_id:
            self.log_test("Chat History", False, "No chat session ID available")
            return False
            
        try:
            async with self.session.get(f"{BACKEND_URL}/chat/{self.chat_session_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    message_count = len(data) if isinstance(data, list) else 0
                    self.log_test("Chat History", True, f"Retrieved {message_count} messages")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("Chat History", False, f"HTTP {response.status}", error_text)
                    return False
        except Exception as e:
            self.log_test("Chat History", False, error=str(e))
            return False

    async def test_patient_chat_sessions(self):
        """Test getting all chat sessions for a patient"""
        if not self.created_patient_id:
            self.log_test("Patient Chat Sessions", False, "No patient ID available")
            return False
            
        try:
            async with self.session.get(f"{BACKEND_URL}/patients/{self.created_patient_id}/chats") as response:
                if response.status == 200:
                    data = await response.json()
                    session_count = len(data) if isinstance(data, list) else 0
                    self.log_test("Patient Chat Sessions", True, f"Retrieved {session_count} chat sessions")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("Patient Chat Sessions", False, f"HTTP {response.status}", error_text)
                    return False
        except Exception as e:
            self.log_test("Patient Chat Sessions", False, error=str(e))
            return False

    async def test_error_handling(self):
        """Test error handling with invalid requests"""
        tests_passed = 0
        total_tests = 3
        
        # Test 1: Invalid patient ID
        try:
            async with self.session.get(f"{BACKEND_URL}/patients/invalid-id") as response:
                if response.status == 404:
                    tests_passed += 1
                    print("✅ Invalid patient ID properly returns 404")
                else:
                    print(f"❌ Invalid patient ID returned {response.status} instead of 404")
        except Exception as e:
            print(f"❌ Error testing invalid patient ID: {e}")
            
        # Test 2: Diagnosis without patient
        try:
            invalid_diagnosis = {
                "patient_id": "non-existent-id",
                "symptoms": [{"description": "test", "severity": 5, "duration": "1 day"}]
            }
            async with self.session.post(f"{BACKEND_URL}/diagnosis", json=invalid_diagnosis) as response:
                if response.status == 404:
                    tests_passed += 1
                    print("✅ Diagnosis with invalid patient ID properly returns 404")
                else:
                    print(f"❌ Diagnosis with invalid patient ID returned {response.status} instead of 404")
        except Exception as e:
            print(f"❌ Error testing diagnosis with invalid patient: {e}")
            
        # Test 3: Chat with invalid patient
        try:
            invalid_chat = {
                "patient_id": "non-existent-id",
                "message": "test message"
            }
            async with self.session.post(f"{BACKEND_URL}/chat", json=invalid_chat) as response:
                if response.status == 404:
                    tests_passed += 1
                    print("✅ Chat with invalid patient ID properly returns 404")
                else:
                    print(f"❌ Chat with invalid patient ID returned {response.status} instead of 404")
        except Exception as e:
            print(f"❌ Error testing chat with invalid patient: {e}")
            
        success = tests_passed == total_tests
        self.log_test("Error Handling", success, f"Passed {tests_passed}/{total_tests} error handling tests")
        return success

    async def run_all_tests(self):
        """Run all backend tests"""
        print("🏥 Starting AI Medical Diagnosis Backend Tests")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print()
        
        await self.setup()
        
        try:
            # Core functionality tests
            test_functions = [
                self.test_health_check,
                self.test_root_endpoint,
                self.test_create_patient,
                self.test_get_patients,
                self.test_get_patient_by_id,
                self.test_ai_diagnosis,
                self.test_get_patient_diagnoses,
                self.test_patient_chat,
                self.test_chat_history,
                self.test_patient_chat_sessions,
                self.test_error_handling
            ]
            
            for test_func in test_functions:
                await test_func()
                await asyncio.sleep(0.5)  # Small delay between tests
                
        finally:
            await self.cleanup()
            
        # Print summary
        print("=" * 60)
        print("🏥 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print()
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['error'] or test['details']}")
        else:
            print("✅ ALL TESTS PASSED!")
            
        return passed == total

async def main():
    """Main test runner"""
    tester = MedicalSystemTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 All backend tests completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the details above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())