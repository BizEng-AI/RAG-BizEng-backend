"""
Test roleplay endpoints with admin user to diagnose issues
"""
import requests
import json
import time

BASE_URL = "https://bizeng-server.fly.dev"

print("="*70)
print("TESTING ROLEPLAY ENDPOINTS - ADMIN USER")
print("="*70)

# Test 1: Login as admin
print("\n1. Login as admin (yoo@gmail.com)...")
try:
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "yoo@gmail.com",
        "password": "qwerty"
    }, timeout=10)
    resp.raise_for_status()
    token = resp.json()['access_token']
    print(f"✓ Login successful")
    headers = {"Authorization": f"Bearer {token}"}
except Exception as e:
    print(f"✗ Login failed: {e}")
    exit(1)

# Test 2: Get available scenarios
print("\n2. Get available scenarios...")
try:
    resp = requests.get(f"{BASE_URL}/roleplay/scenarios", headers=headers, timeout=10)
    resp.raise_for_status()
    scenarios = resp.json()['scenarios']
    print(f"✓ Found {len(scenarios)} scenarios:")
    for s in scenarios:
        print(f"  - {s['id']}: {s['title']}")
except Exception as e:
    print(f"✗ Failed: {e}")
    scenarios = []

# Test 3: Start job_interview scenario
print("\n3. Start job_interview scenario...")
try:
    resp = requests.post(f"{BASE_URL}/roleplay/start", json={
        "scenario_id": "job_interview",
        "student_name": "Admin Test",
        "use_rag": True
    }, headers=headers, timeout=30)

    print(f"Status Code: {resp.status_code}")
    print(f"Response Headers: {dict(resp.headers)}")

    if resp.status_code == 200:
        data = resp.json()
        session_id = data.get('session_id')
        print(f"✓ Session started: {session_id}")
        print(f"  Initial message: {data.get('initial_message', '')[:80]}...")
    else:
        print(f"✗ Failed with status {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        session_id = None
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    session_id = None

if not session_id:
    print("\n❌ Cannot continue without session_id")
    exit(1)

# Test 4: Submit first turn
print(f"\n4. Submit turn to session {session_id}...")
try:
    resp = requests.post(f"{BASE_URL}/roleplay/turn", json={
        "session_id": session_id,
        "message": "Hello, I am excited about this opportunity"
    }, headers=headers, timeout=30)

    print(f"Status Code: {resp.status_code}")

    if resp.status_code == 200:
        data = resp.json()
        print(f"✓ Turn successful")
        print(f"  AI response: {data.get('ai_message', '')[:80]}...")
        has_errors = data.get('correction', {}).get('has_errors', False)
        print(f"  Has corrections: {has_errors}")
    elif resp.status_code == 404:
        print(f"✗ 404 Not Found - Endpoint doesn't exist or session not found")
        print(f"Response: {resp.text}")
    else:
        print(f"✗ Failed with status {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
except requests.exceptions.ConnectionError as e:
    print(f"✗ Connection Error: {e}")
    print("  → This is the 'unexpected end of stream' error!")
except requests.exceptions.Timeout as e:
    print(f"✗ Timeout: {e}")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Try client_meeting scenario
print("\n5. Start client_meeting scenario...")
try:
    resp = requests.post(f"{BASE_URL}/roleplay/start", json={
        "scenario_id": "client_meeting",
        "student_name": "Admin Test",
        "use_rag": True
    }, headers=headers, timeout=30)

    if resp.status_code == 200:
        data = resp.json()
        session_id2 = data.get('session_id')
        print(f"✓ Session started: {session_id2}")

        # Try a turn
        time.sleep(1)
        resp = requests.post(f"{BASE_URL}/roleplay/turn", json={
            "session_id": session_id2,
            "message": "Good morning, thank you for meeting with me"
        }, headers=headers, timeout=30)

        print(f"Turn Status: {resp.status_code}")
        if resp.status_code == 200:
            print("✓ Turn successful for client_meeting")
        else:
            print(f"✗ Turn failed: {resp.text[:200]}")
    else:
        print(f"✗ Failed to start: {resp.status_code}")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")

# Test 6: Check server logs endpoint
print("\n6. Check active sessions...")
try:
    resp = requests.get(f"{BASE_URL}/roleplay/sessions", headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        print(f"✓ Active sessions: {data.get('active_sessions', 0)}")
    else:
        print(f"Status: {resp.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
print("\nKey findings:")
print("1. Check if 'unexpected end of stream' happens during /turn")
print("2. Check if 404 happens for /turn endpoint")
print("3. Compare behavior between scenarios")
print("4. Note any connection reset errors")

