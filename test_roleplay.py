import requests
import json

# Test the roleplay endpoints
BASE_URL = "http://localhost:8020"

print("=" * 60)
print("TESTING ROLEPLAY FEATURE")
print("=" * 60)

# 1. List scenarios
print("\n1. Testing GET /roleplay/scenarios")
try:
    response = requests.get(f"{BASE_URL}/roleplay/scenarios")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Available scenarios: {len(data['scenarios'])}")
        for scenario in data['scenarios']:
            print(f"  - {scenario['title']} ({scenario['difficulty']}) - {scenario['stages']} stages")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# 2. Start a session
print("\n2. Testing POST /roleplay/start")
try:
    response = requests.post(
        f"{BASE_URL}/roleplay/start",
        json={"scenario_id": "customer_complaint", "student_name": "Test User"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        session_id = data['session_id']
        print(f"Session created: {session_id}")
        print(f"Scenario: {data['scenario_title']}")
        print(f"Your role: {data['student_role']}")
        print(f"AI role: {data['ai_role']}")
        print(f"AI's opening: {data['initial_message'][:100]}...")

        # 3. Submit a turn
        print("\n3. Testing POST /roleplay/turn")
        response = requests.post(
            f"{BASE_URL}/roleplay/turn",
            json={
                "session_id": session_id,
                "message": "Hello, I'm calling about a defective product I received yesterday. The item arrived damaged and I'd like to get a replacement or refund."
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"AI response: {data['ai_message'][:150]}...")
            if data['correction']:
                print(f"Correction: {data['correction']['explanation']}")
            print(f"Stage: {data['stage_info']['stage_name']} ({data['stage_info']['stage_number']}/{data['stage_info']['total_stages']})")
            print(f"Stage advanced: {data['stage_advanced']}")
        else:
            print(f"Error: {response.text}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Testing complete!")
print("=" * 60)

