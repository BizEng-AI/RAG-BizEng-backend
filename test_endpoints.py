import requests
import json

BASE_URL = "http://localhost:8020"

print("=" * 60)
print("ENDPOINT TESTING SUITE")
print("=" * 60)
print()

# Test 1: Health Check
print("1. Testing /health endpoint...")
try:
    resp = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"   ✅ Status: {resp.status_code}")
    print(f"   Response: {resp.json()}")
except Exception as e:
    print(f"   ❌ Error: {e}")
print()

# Test 2: Version Check
print("2. Testing /version endpoint...")
try:
    resp = requests.get(f"{BASE_URL}/version", timeout=5)
    print(f"   ✅ Status: {resp.status_code}")
    print(f"   Response: {resp.json()}")
except Exception as e:
    print(f"   ❌ Error: {e}")
print()

# Test 3: Embedding Test (Azure UAE North)
print("3. Testing /debug/embed endpoint (Azure UAE North - Embeddings)...")
try:
    resp = requests.post(
        f"{BASE_URL}/debug/embed",
        json={"text": "test embedding"},
        timeout=10
    )
    print(f"   ✅ Status: {resp.status_code}")
    result = resp.json()
    print(f"   Embedding dimension: {result.get('dim')}")
    if result.get('dim') == 1536:
        print(f"   ✅ Correct dimension for text-embedding-3-small")
    else:
        print(f"   ⚠️  Expected 1536, got {result.get('dim')}")
except Exception as e:
    print(f"   ❌ Error: {e}")
print()

# Test 4: Chat Endpoint (Azure Sweden Central)
print("4. Testing /chat endpoint (Azure Sweden Central - gpt-35-turbo)...")
try:
    resp = requests.post(
        f"{BASE_URL}/chat",
        json={
            "messages": [
                {"role": "user", "content": "Say 'test successful' if you can hear me"}
            ]
        },
        timeout=15
    )
    print(f"   ✅ Status: {resp.status_code}")
    result = resp.json()
    answer = result.get('answer') or result.get('message', '')
    print(f"   Response: {answer[:100]}...")
    if 'test successful' in answer.lower() or len(answer) > 5:
        print(f"   ✅ Chat model responding correctly")
except Exception as e:
    print(f"   ❌ Error: {e}")
print()

# Test 5: RAG Search (Embeddings + Qdrant)
print("5. Testing /debug/search endpoint (RAG pipeline)...")
try:
    resp = requests.get(
        f"{BASE_URL}/debug/search",
        params={"q": "business meeting", "k": 3},
        timeout=10
    )
    print(f"   ✅ Status: {resp.status_code}")
    result = resp.json()
    items = result.get('items', [])
    print(f"   Found {len(items)} results")
    if items:
        print(f"   Top result score: {items[0].get('score', 0):.4f}")
        print(f"   ✅ RAG pipeline working")
    else:
        print(f"   ⚠️  No results found (Qdrant may be empty)")
except Exception as e:
    print(f"   ❌ Error: {e}")
print()

# Test 6: Roleplay Start
print("6. Testing /roleplay/start endpoint...")
try:
    resp = requests.post(
        f"{BASE_URL}/roleplay/start",
        json={
            "scenario_id": "job_interview",
            "student_name": "TestUser"
        },
        timeout=15
    )
    print(f"   ✅ Status: {resp.status_code}")
    result = resp.json()
    session_id = result.get('session_id', '')
    current_stage = result.get('current_stage', '')
    initial_msg = result.get('initial_message', '')
    print(f"   Session ID: {session_id[:20]}...")
    print(f"   Current Stage: {current_stage}")
    print(f"   Stage Type: {type(current_stage).__name__}")
    if isinstance(current_stage, str):
        print(f"   ✅ current_stage is string (matches Android)")
    else:
        print(f"   ❌ current_stage is {type(current_stage).__name__} (should be string!)")
    print(f"   Initial message: {initial_msg[:80]}...")

    # Test 7: Roleplay Turn
    if session_id:
        print()
        print("7. Testing /roleplay/turn endpoint...")
        try:
            resp = requests.post(
                f"{BASE_URL}/roleplay/turn",
                json={
                    "session_id": session_id,
                    "message": "Hello, I'm excited for this opportunity"
                },
                timeout=20
            )
            print(f"   ✅ Status: {resp.status_code}")
            result = resp.json()
            ai_msg = result.get('ai_message', '')
            correction = result.get('correction', {})
            current_stage_turn = result.get('current_stage', '')
            feedback = result.get('feedback')

            print(f"   AI Message: {ai_msg[:80]}...")
            print(f"   Current Stage: {current_stage_turn}")
            print(f"   Stage Type: {type(current_stage_turn).__name__}")
            if isinstance(current_stage_turn, str):
                print(f"   ✅ current_stage is string (matches Android)")
            else:
                print(f"   ❌ current_stage is {type(current_stage_turn).__name__} (should be string!)")

            # Check correction format
            if correction:
                has_errors = correction.get('has_errors')
                errors = correction.get('errors', [])
                corr_feedback = correction.get('feedback')
                print(f"   Correction format:")
                print(f"     - has_errors: {has_errors} (type: {type(has_errors).__name__})")
                print(f"     - errors: {len(errors) if errors else 0} items")
                print(f"     - feedback: {corr_feedback[:50] if corr_feedback else None}...")

                if isinstance(has_errors, bool) and isinstance(errors, list):
                    print(f"   ✅ Correction format matches Android expectations")
                else:
                    print(f"   ❌ Correction format doesn't match Android!")

            print(f"   Feedback field: {feedback}")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("TESTING COMPLETE")
print("=" * 60)

