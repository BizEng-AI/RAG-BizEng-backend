"""
Test the /auth/register endpoint to see what it actually returns
"""
import requests
import json

# Try to register a new user
url = "https://bizeng-server.fly.dev/auth/register"
payload = {
    "email": "testuser123@example.com",
    "password": "Test123!",
    "display_name": "Test User"
}

print("Testing /auth/register endpoint...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print()

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print()
    print("Response Body:")
    print(json.dumps(response.json(), indent=2))
    print()
    
    # Check if tokens are present
    data = response.json()
    print("Token Check:")
    print(f"  - access_token present: {'access_token' in data}")
    print(f"  - refresh_token present: {'refresh_token' in data}")
    print(f"  - token_type present: {'token_type' in data}")
    
    if 'access_token' in data and 'refresh_token' in data:
        print("\n✅ SUCCESS: Tokens are present in response!")
    else:
        print("\n❌ FAILURE: Tokens are MISSING from response!")
        print("This is the SERVER ISSUE that needs fixing.")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")
except json.JSONDecodeError as e:
    print(f"❌ Response is not JSON: {e}")
    print(f"Raw response: {response.text}")

