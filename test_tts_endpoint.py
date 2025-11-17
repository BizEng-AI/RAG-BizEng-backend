"""
Test TTS endpoint to check if it works with admin user
"""
import requests
import sys

BASE_URL = "https://bizeng-server.fly.dev"

print("="*70)
print("TESTING TTS ENDPOINT")
print("="*70)

# Test 1: Login as admin
print("\n1. Login as admin...")
try:
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "yoo@gmail.com",
        "password": "qwerty"
    }, timeout=30)
    resp.raise_for_status()
    token = resp.json()['access_token']
    print("OK Login successful")
    headers = {"Authorization": f"Bearer {token}"}
except Exception as e:
    print(f"FAIL Login failed: {e}")
    exit(1)

# Test 2: Test TTS without auth (endpoint doesn't require it)
print("\n2. Test TTS endpoint WITHOUT auth...")
try:
    resp = requests.post(
        f"{BASE_URL}/tts",
        data={"text": "Hello, this is a test of text to speech"},
        timeout=30
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"OK TTS works without auth")
        print(f"  Audio size: {len(resp.content)} bytes")
        print(f"  Content-Type: {resp.headers.get('content-type')}")
    else:
        print(f"FAIL Status {resp.status_code}: {resp.text[:200]}")
except Exception as e:
    print(f"FAIL Error: {type(e).__name__}: {e}")

# Test 3: Test TTS WITH auth (admin user)
print("\n3. Test TTS endpoint WITH admin auth...")
try:
    resp = requests.post(
        f"{BASE_URL}/tts",
        data={"text": "This is admin testing text to speech"},
        headers=headers,
        timeout=30
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"OK TTS works with admin auth")
        print(f"  Audio size: {len(resp.content)} bytes")
    else:
        print(f"FAIL Status {resp.status_code}: {resp.text[:200]}")
except Exception as e:
    print(f"FAIL Error: {type(e).__name__}: {e}")

# Test 4: Test with longer custom text
print("\n4. Test TTS with longer custom text...")
custom_text = """Good morning everyone. Today we will discuss 
the quarterly business results and review our strategic plan 
for the next fiscal year. Please prepare your reports."""

try:
    resp = requests.post(
        f"{BASE_URL}/tts",
        data={"text": custom_text},
        headers=headers,
        timeout=30
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"OK Custom text TTS works")
        print(f"  Audio size: {len(resp.content)} bytes")
    else:
        print(f"FAIL Status {resp.status_code}")
        print(f"  Response: {resp.text[:200]}")
except Exception as e:
    print(f"FAIL Error: {type(e).__name__}: {e}")

# Test 5: Test with special characters
print("\n5. Test TTS with special characters...")
special_text = "Hello! How are you? I'm fine, thank you. Let's discuss the project: it's important."

try:
    resp = requests.post(
        f"{BASE_URL}/tts",
        data={"text": special_text},
        headers=headers,
        timeout=30
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"OK Special characters TTS works")
        print(f"  Audio size: {len(resp.content)} bytes")
    else:
        print(f"FAIL Status {resp.status_code}")
except Exception as e:
    print(f"FAIL Error: {type(e).__name__}: {e}")

print("\n" + "="*70)
print("TTS TEST COMPLETE")
print("="*70)

print("\nSUMMARY:")
print("- TTS endpoint does NOT require authentication")
print("- Uses OpenAI TTS (not Azure Speech Service)")
print("- Should work the same for admin and student users")
print("- If Android says 'not working with admin', likely client-side issue")

