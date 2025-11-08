import requests
import json

BASE_URL = "http://localhost:8020"

print("=" * 60)
print("CHAT ENDPOINT DIAGNOSTIC TEST")
print("=" * 60)
print()

# Test 1: Simple chat message (what Android should send)
print("1. Testing /chat with simple message...")
try:
    payload = {
        "messages": [
            {"role": "user", "content": "Hello, can you help me with business English?"}
        ]
    }
    
    print(f"   Request payload: {json.dumps(payload, indent=2)}")
    
    resp = requests.post(
        f"{BASE_URL}/chat",
        json=payload,
        timeout=15
    )
    
    print(f"   ✅ Status: {resp.status_code}")
    
    if resp.status_code == 200:
        result = resp.json()
        print(f"   Answer: {result.get('answer', '')[:150]}...")
        print(f"   Sources: {result.get('sources', [])}")
        print(f"   ✅ Chat endpoint working perfectly!")
    else:
        print(f"   ❌ Error response: {resp.text}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 2: Chat with conversation history
print("2. Testing /chat with conversation history...")
try:
    payload = {
        "messages": [
            {"role": "user", "content": "What is a professional email greeting?"},
            {"role": "assistant", "content": "A professional email greeting typically starts with 'Dear' followed by the recipient's name."},
            {"role": "user", "content": "Can you give me an example?"}
        ]
    }
    
    resp = requests.post(
        f"{BASE_URL}/chat",
        json=payload,
        timeout=15
    )
    
    print(f"   ✅ Status: {resp.status_code}")
    
    if resp.status_code == 200:
        result = resp.json()
        print(f"   Answer: {result.get('answer', '')[:150]}...")
        print(f"   ✅ Multi-turn conversation working!")
    else:
        print(f"   ❌ Error: {resp.text}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# Test 3: Edge cases that might cause Android issues
print("3. Testing edge cases...")

test_cases = [
    {
        "name": "Empty message",
        "payload": {"messages": [{"role": "user", "content": ""}]}
    },
    {
        "name": "Very long message",
        "payload": {"messages": [{"role": "user", "content": "a" * 5000}]}
    },
    {
        "name": "Special characters",
        "payload": {"messages": [{"role": "user", "content": "Hello! How are you? 😊 I'm learning English."}]}
    },
    {
        "name": "Missing role field",
        "payload": {"messages": [{"content": "Hello"}]}
    },
    {
        "name": "Wrong role value",
        "payload": {"messages": [{"role": "person", "content": "Hello"}]}
    }
]

for test in test_cases:
    try:
        print(f"\n   Testing: {test['name']}")
        resp = requests.post(
            f"{BASE_URL}/chat",
            json=test['payload'],
            timeout=15
        )
        
        if resp.status_code == 200:
            print(f"   ✅ Status: 200 - Handled successfully")
        else:
            print(f"   ⚠️  Status: {resp.status_code}")
            print(f"   Response: {resp.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")

print()
print("=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
print()
print("🔍 WHAT ANDROID SHOULD SEND:")
print()
print("POST /chat")
print("Content-Type: application/json")
print()
print(json.dumps({
    "messages": [
        {"role": "user", "content": "Your message here"}
    ]
}, indent=2))
print()
print("Expected Response (200 OK):")
print(json.dumps({
    "answer": "AI response here",
    "sources": []
}, indent=2))

