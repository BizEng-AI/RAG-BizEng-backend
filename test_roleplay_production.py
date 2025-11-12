"""
Test roleplay on production
"""
import requests
import json

PROD_URL = "https://bizeng-server.fly.dev"

print("=" * 70)
print("TESTING ROLEPLAY ON PRODUCTION")
print("=" * 70)
print()

# Test 1: List scenarios
print("1️⃣ GET /roleplay/scenarios")
try:
    r = requests.get(f"{PROD_URL}/roleplay/scenarios", timeout=15)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"✅ Found {len(data['scenarios'])} scenarios")
    else:
        print(f"❌ Failed: {r.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 2: Start session
print("2️⃣ POST /roleplay/start")
try:
    payload = {"scenario_id": "job_interview", "student_name": "ProductionTest"}
    r = requests.post(f"{PROD_URL}/roleplay/start", json=payload, timeout=30)
    print(f"Status: {r.status_code}")

    if r.status_code == 200:
        data = r.json()
        session_id = data.get('session_id')
        print(f"✅ Session created: {session_id[:20]}...")
        print(f"   Initial message: {data.get('initial_message', '')[:80]}...")

        # Test 3: Submit turn
        print()
        print("3️⃣ POST /roleplay/turn")
        turn_payload = {
            "session_id": session_id,
            "message": "Hello, I am excited about this opportunity"
        }
        r2 = requests.post(f"{PROD_URL}/roleplay/turn", json=turn_payload, timeout=30)
        print(f"Status: {r2.status_code}")

        if r2.status_code == 200:
            turn_data = r2.json()
            print(f"✅ AI responded: {turn_data.get('ai_message', '')[:80]}...")
            print(f"   Has errors: {turn_data.get('correction', {}).get('has_errors', False)}")
            print(f"   Stage: {turn_data.get('current_stage')}")
        else:
            print(f"❌ Turn failed: {r2.text}")
    else:
        print(f"❌ Start failed: {r.text}")

except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=" * 70)
print("PRODUCTION ROLEPLAY TEST COMPLETE")
print("=" * 70)

