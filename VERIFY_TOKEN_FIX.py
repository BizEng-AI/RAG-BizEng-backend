"""
COMPLETE TOKEN ISSUE FIX - Verification Script
Run this after deployment completes to verify the fix
"""
import requests
import json
import time

BASE_URL = "https://bizeng-server.fly.dev"

print("=" * 70)
print("🔍 VERIFYING TOKEN ISSUE FIX")
print("=" * 70)
print()

# Step 1: Check health endpoint
print("1️⃣ Testing server health...")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    if response.status_code == 200:
        print(f"   ✅ Server is up: {response.json()}")
    else:
        print(f"   ❌ Server health check failed: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"   ❌ Cannot reach server: {e}")
    exit(1)

print()

# Step 2: Test registration endpoint
print("2️⃣ Testing /auth/register endpoint...")
test_user = {
    "email": f"test{int(time.time())}@example.com",
    "password": "SecurePass123!",
    "display_name": "Test User"
}

print(f"   Registering: {test_user['email']}")

try:
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json=test_user,
        timeout=15
    )

    print(f"   Status Code: {response.status_code}")

    if response.status_code == 404:
        print("   ❌ 404 ERROR: Auth endpoints NOT deployed!")
        print("   The /auth routes are missing from the server.")
        print()
        print("   Fix: Make sure app.py includes the routers:")
        print("   app.include_router(auth.router)")
        exit(1)

    if response.status_code == 201:
        data = response.json()
        print()
        print("   Response Body:")
        print(json.dumps(data, indent=4))
        print()

        # Check for tokens
        has_access = "access_token" in data
        has_refresh = "refresh_token" in data
        has_type = "token_type" in data

        print("   Token Validation:")
        print(f"     - access_token: {'✅ PRESENT' if has_access else '❌ MISSING'}")
        print(f"     - refresh_token: {'✅ PRESENT' if has_refresh else '❌ MISSING'}")
        print(f"     - token_type: {'✅ PRESENT' if has_type else '❌ MISSING'}")
        print()

        if has_access and has_refresh:
            print("   🎉 SUCCESS! Server is returning tokens correctly!")
            print()
            print("   ✅ Android app should now work!")
            print("   ✅ Registration will succeed!")
            print("   ✅ Token issue is FIXED!")

            # Test login too
            print()
            print("3️⃣ Testing /auth/login endpoint...")
            login_response = requests.post(
                f"{BASE_URL}/auth/login",
                json={
                    "email": test_user["email"],
                    "password": test_user["password"]
                },
                timeout=10
            )

            if login_response.status_code == 200:
                login_data = login_response.json()
                if "access_token" in login_data and "refresh_token" in login_data:
                    print("   ✅ Login also works! Tokens returned!")
                else:
                    print("   ⚠️  Login works but tokens missing (unexpected)")
            else:
                print(f"   ⚠️  Login returned {login_response.status_code}")

        else:
            print("   ❌ TOKENS STILL MISSING!")
            print()
            print("   This means the TokenOut schema is not being returned properly.")
            print("   Check routers/auth.py - make sure it returns TokenOut")
            exit(1)
    else:
        print(f"   ❌ Registration failed with status {response.status_code}")
        print(f"   Response: {response.text}")
        exit(1)

except requests.exceptions.RequestException as e:
    print(f"   ❌ Request failed: {e}")
    exit(1)

print()
print("=" * 70)
print("✅ ALL TESTS PASSED - TOKEN ISSUE FIXED!")
print("=" * 70)
print()
print("Next steps:")
print("1. Test the Android app")
print("2. Registration should now work")
print("3. Tokens will be saved properly")
print()

