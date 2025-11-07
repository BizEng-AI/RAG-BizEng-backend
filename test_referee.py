import requests
import json

BASE_URL = "http://localhost:8020"

print("=" * 60)
print("TESTING ROLEPLAY REFEREE - PROFANITY DETECTION")
print("=" * 60)
print()

# Test 1: Start a roleplay session
print("1. Starting a roleplay session...")
try:
    resp = requests.post(
        f"{BASE_URL}/roleplay/start",
        json={
            "scenario_id": "job_interview",
            "student_name": "TestUser"
        },
        timeout=15
    )
    result = resp.json()
    session_id = result.get('session_id')
    print(f"   ✅ Session created: {session_id[:20]}...")
    print(f"   Initial message: {result.get('initial_message', '')[:80]}...")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

print()

# Test 2: Send profanity - should be FLAGGED
print("2. Testing with PROFANITY (should be flagged as PRAGMATIC error)...")
try:
    resp = requests.post(
        f"{BASE_URL}/roleplay/turn",
        json={
            "session_id": session_id,
            "message": "fuck off"
        },
        timeout=20
    )
    result = resp.json()

    ai_msg = result.get('ai_message', '')
    correction = result.get('correction', {})

    print(f"   AI Response: {ai_msg[:80]}...")
    print()
    print(f"   Correction Details:")
    print(f"     - has_errors: {correction.get('has_errors')}")

    if correction.get('has_errors'):
        errors = correction.get('errors', [])
        if errors:
            err = errors[0]
            print(f"     - type: {err.get('type')}")
            print(f"     - incorrect: {err.get('incorrect')}")
            print(f"     - correct: {err.get('correct')}")
            print(f"     - explanation: {err.get('explanation')}")

        feedback = correction.get('feedback', '')
        print(f"     - feedback: {feedback}")

        # Check if it was properly flagged
        if correction.get('has_errors') and errors:
            error_type = errors[0].get('type', '')
            if error_type == 'pragmatic':
                print()
                print(f"   ✅ SUCCESS! Profanity correctly flagged as PRAGMATIC error")
            else:
                print()
                print(f"   ⚠️  WARNING: Flagged as '{error_type}' instead of 'pragmatic'")
        else:
            print()
            print(f"   ❌ FAILED: No error detected!")
    else:
        print()
        print(f"   ❌ FAILED: Profanity was NOT flagged as an error!")

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 3: Send professional message - should be OK
print("3. Testing with PROFESSIONAL message (should have no errors)...")
try:
    resp = requests.post(
        f"{BASE_URL}/roleplay/turn",
        json={
            "session_id": session_id,
            "message": "Thank you for this opportunity. I have five years of experience in marketing and I'm very excited about this position."
        },
        timeout=20
    )
    result = resp.json()

    ai_msg = result.get('ai_message', '')
    correction = result.get('correction', {})

    print(f"   AI Response: {ai_msg[:80]}...")
    print()
    print(f"   Correction Details:")
    print(f"     - has_errors: {correction.get('has_errors')}")

    if not correction.get('has_errors'):
        feedback = correction.get('feedback', '')
        print(f"     - feedback: {feedback}")
        print()
        print(f"   ✅ SUCCESS! Professional message accepted without errors")
    else:
        errors = correction.get('errors', [])
        if errors:
            err = errors[0]
            print(f"     - type: {err.get('type')}")
            print(f"     - explanation: {err.get('explanation')}")
        print()
        print(f"   ⚠️  Professional message flagged (may be too strict)")

except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# Test 4: Send casual slang - should be flagged as REGISTER error
print("4. Testing with CASUAL SLANG (should be flagged as REGISTER error)...")
try:
    resp = requests.post(
        f"{BASE_URL}/roleplay/turn",
        json={
            "session_id": session_id,
            "message": "Hey dude, I'm gonna be there at like 3pm or whatever"
        },
        timeout=20
    )
    result = resp.json()

    correction = result.get('correction', {})

    print(f"   Correction Details:")
    print(f"     - has_errors: {correction.get('has_errors')}")

    if correction.get('has_errors'):
        errors = correction.get('errors', [])
        if errors:
            err = errors[0]
            error_type = err.get('type', '')
            print(f"     - type: {error_type}")
            print(f"     - incorrect: {err.get('incorrect')}")
            print(f"     - explanation: {err.get('explanation')}")

            if error_type == 'register':
                print()
                print(f"   ✅ SUCCESS! Casual language correctly flagged as REGISTER error")
            else:
                print()
                print(f"   ⚠️  Flagged as '{error_type}' instead of 'register'")
    else:
        print()
        print(f"   ❌ FAILED: Casual language was NOT flagged!")

except Exception as e:
    print(f"   ❌ Error: {e}")

print()
print("=" * 60)
print("TESTING COMPLETE")
print("=" * 60)

