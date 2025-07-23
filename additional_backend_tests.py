#!/usr/bin/env python3
"""
Additional Backend Tests for Edge Cases and Data Validation
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://9730001b-7bd4-4ff2-85e2-0898283d86c7.preview.emergentagent.com/api"

async def test_data_validation():
    """Test data validation and edge cases"""
    session = aiohttp.ClientSession()
    
    try:
        print("🧪 Testing Data Validation and Edge Cases")
        print("=" * 50)
        
        # Test 1: Invalid patient data
        print("Testing invalid patient data...")
        invalid_patient = {
            "name": "",  # Empty name
            "age": -5,   # Invalid age
            "gender": "Invalid",
            "email": "not-an-email"
        }
        
        async with session.post(f"{BACKEND_URL}/patients", json=invalid_patient) as response:
            if response.status == 422:  # Validation error
                print("✅ Invalid patient data properly rejected")
            else:
                print(f"❌ Invalid patient data accepted (status: {response.status})")
        
        # Test 2: Diagnosis with invalid symptoms
        print("Testing diagnosis with invalid symptoms...")
        invalid_diagnosis = {
            "patient_id": "test-id",
            "symptoms": [
                {
                    "description": "",  # Empty description
                    "severity": 15,     # Invalid severity (>10)
                    "duration": ""      # Empty duration
                }
            ]
        }
        
        async with session.post(f"{BACKEND_URL}/diagnosis", json=invalid_diagnosis) as response:
            if response.status in [422, 404]:  # Validation error or patient not found
                print("✅ Invalid diagnosis data properly handled")
            else:
                print(f"❌ Invalid diagnosis data accepted (status: {response.status})")
        
        # Test 3: Empty chat message
        print("Testing empty chat message...")
        empty_chat = {
            "patient_id": "test-id",
            "message": ""
        }
        
        async with session.post(f"{BACKEND_URL}/chat", json=empty_chat) as response:
            if response.status in [422, 404]:
                print("✅ Empty chat message properly handled")
            else:
                print(f"❌ Empty chat message accepted (status: {response.status})")
                
        # Test 4: Large symptom list
        print("Testing diagnosis with multiple symptoms...")
        large_symptoms = []
        for i in range(5):
            large_symptoms.append({
                "description": f"Symptom {i+1}: Various pain and discomfort",
                "severity": i + 3,
                "duration": f"{i+1} days",
                "location": f"Location {i+1}"
            })
        
        # First create a valid patient for this test
        test_patient = {
            "name": "Test Patient Multiple Symptoms",
            "age": 45,
            "gender": "Male",
            "email": "test.multiple@email.com",
            "medical_history": ["Diabetes", "High blood pressure"]
        }
        
        async with session.post(f"{BACKEND_URL}/patients", json=test_patient) as response:
            if response.status == 200:
                patient_data = await response.json()
                patient_id = patient_data["id"]
                
                # Now test diagnosis with multiple symptoms
                multi_symptom_diagnosis = {
                    "patient_id": patient_id,
                    "symptoms": large_symptoms,
                    "additional_info": "Patient experiencing multiple concurrent symptoms"
                }
                
                async with session.post(f"{BACKEND_URL}/diagnosis", json=multi_symptom_diagnosis) as response:
                    if response.status == 200:
                        print("✅ Multiple symptoms diagnosis handled successfully")
                    else:
                        error_text = await response.text()
                        print(f"❌ Multiple symptoms diagnosis failed: {error_text}")
            else:
                print("❌ Could not create test patient for multiple symptoms test")
        
        print("\n✅ Data validation tests completed")
        
    except Exception as e:
        print(f"❌ Error in validation tests: {e}")
    finally:
        await session.close()

async def test_concurrent_requests():
    """Test system under concurrent load"""
    print("\n🚀 Testing Concurrent Requests")
    print("=" * 50)
    
    # Create multiple patients concurrently
    async def create_patient(session, patient_num):
        patient_data = {
            "name": f"Concurrent Patient {patient_num}",
            "age": 25 + patient_num,
            "gender": "Female" if patient_num % 2 == 0 else "Male",
            "email": f"patient{patient_num}@test.com",
            "medical_history": [f"History item {patient_num}"]
        }
        
        try:
            async with session.post(f"{BACKEND_URL}/patients", json=patient_data) as response:
                return response.status == 200
        except:
            return False
    
    session = aiohttp.ClientSession()
    try:
        # Create 5 patients concurrently
        tasks = [create_patient(session, i) for i in range(1, 6)]
        results = await asyncio.gather(*tasks)
        
        successful = sum(results)
        print(f"✅ Created {successful}/5 patients concurrently")
        
        if successful >= 4:  # Allow for 1 potential failure
            print("✅ Concurrent request handling working well")
        else:
            print("❌ Concurrent request handling needs improvement")
            
    except Exception as e:
        print(f"❌ Error in concurrent tests: {e}")
    finally:
        await session.close()

async def main():
    await test_data_validation()
    await test_concurrent_requests()

if __name__ == "__main__":
    asyncio.run(main())