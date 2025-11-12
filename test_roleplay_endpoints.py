"""
Test roleplay endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8020"

print("=" * 70)
print("TESTING ROLEPLAY ENDPOINTS")
print("=" * 70)
print()

# Test 1: Start roleplay session
print("1️⃣ Testing POST /roleplay/start...")
try:
    payload = {
        "scenario_id": "job_interview",
        "student_name": "TestUser"
    }
    r = requests.post(f"{BASE_URL}/roleplay/start", json=payload, timeout=30)
    print(f"   Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        session_id = data.get('session_id')
        print(f"   Session ID: {session_id}")
        print(f"   Scenario: {data.get('scenario_title')}")
        print(f"   Stage: {data.get('current_stage')}")
        print(f"   Initial message: {data.get('initial_message', '')[:100]}...")
        print("   ✅ Roleplay start working!")
        
        # Test 2: Submit turn
        print()
        print("2️⃣ Testing POST /roleplay/turn...")
        try:
            turn_payload = {
                "session_id": session_id,
                "message": "Hello, I'm very excited for this job opportunity"
            }
            r2 = requests.post(f"{BASE_URL}/roleplay/turn", json=turn_payload, timeout=30)
            print(f"   Status: {r2.status_code}")
            
            if r2.status_code == 200:
                turn_data = r2.json()
                print(f"   AI message: {turn_data.get('ai_message', '')[:100]}...")
                print(f"   Has errors: {turn_data.get('correction', {}).get('has_errors', False)}")
                print(f"   Current stage: {turn_data.get('current_stage')}")
                print(f"   Completed: {turn_data.get('is_completed')}")
                print("   ✅ Roleplay turn working!")
                
                # Show full response structure
                print()
                print("   Full response structure:")
                print(json.dumps(turn_data, indent=4)[:600])
            else:
                print(f"   ❌ Failed: {r2.text}")
                
        except Exception as e:
            print(f"   ❌ Turn failed: {e}")
    else:
        print(f"   ❌ Failed: {r.text}")
        
except Exception as e:
    print(f"   ❌ Start failed: {e}")

print()

# Test 3: List scenarios
print("3️⃣ Testing GET /roleplay/scenarios...")
try:
    r = requests.get(f"{BASE_URL}/roleplay/scenarios", timeout=10)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        scenarios = data.get('scenarios', [])
        print(f"   Found {len(scenarios)} scenarios")
        for s in scenarios:
            print(f"     - {s.get('id')}: {s.get('title')} ({s.get('difficulty')})")
        print("   ✅ Scenarios endpoint working!")
    else:
        print(f"   ❌ Failed: {r.text}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

print()
print("=" * 70)
print("ROLEPLAY TESTS COMPLETE")
print("=" * 70)

