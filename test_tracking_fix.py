"""
Quick test to verify tracking is working after deployment
"""
import requests
import time

BASE_URL = "https://bizeng-server.fly.dev"

print("="*70)
print("TESTING TRACKING FIX - Post Deployment")
print("="*70)

# Step 1: Login
print("\n1. Logging in as yoo@gmail.com...")
resp = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "yoo@gmail.com",
    "password": "qwerty"
})

if resp.status_code == 200:
    data = resp.json()
    token = data.get("access_token")
    print(f"✓ Login successful")
    print(f"  Token: {token[:50]}...")
else:
    print(f"✗ Login failed: {resp.status_code}")
    print(resp.text)
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# Step 2: Check current attempts count
print("\n2. Checking current attempts count...")
resp = requests.get(f"{BASE_URL}/admin/monitor/user_activity/12", headers=headers, timeout=30)
if resp.status_code == 200:
    before_count = len(resp.json().get('items', []))
    print(f"✓ Current attempts: {before_count}")
else:
    print(f"⚠️  Could not get count: {resp.status_code}")
    before_count = 0

# Step 3: Do a chat exercise
print("\n3. Testing CHAT endpoint with tracking...")
resp = requests.post(f"{BASE_URL}/chat", headers=headers, json={
    "messages": [{"role": "user", "content": "What is business email etiquette?"}]
}, timeout=30)

if resp.status_code == 200:
    print("✓ Chat completed successfully")
    answer = resp.json().get('answer', '')
    print(f"  Response: {answer[:80]}...")
else:
    print(f"✗ Chat failed: {resp.status_code}")
    print(resp.text[:200])

# Wait a moment for database to update
time.sleep(2)

# Step 4: Check if attempt was recorded
print("\n4. Verifying attempt was recorded...")
resp = requests.get(f"{BASE_URL}/admin/monitor/user_activity/12", headers=headers, timeout=30)

if resp.status_code == 200:
    items = resp.json().get('items', [])
    after_count = len(items)
    print(f"✓ Attempts now: {after_count}")

    if after_count > before_count:
        print(f"✅ SUCCESS! New attempt recorded (+{after_count - before_count})")
        print("\nMost recent attempts:")
        for item in items[:3]:
            print(f"  - {item.get('exercise_type')} at {item.get('started_at')} (duration: {item.get('duration_seconds')}s)")
    else:
        print("❌ FAILED! No new attempt recorded")
        print(f"   Before: {before_count}, After: {after_count}")
else:
    print(f"✗ Could not verify: {resp.status_code}")
    print(resp.text[:200])

# Step 5: Check overall statistics
print("\n5. Checking overall user activity stats...")
resp = requests.get(f"{BASE_URL}/admin/monitor/users_activity", headers=headers, timeout=30)

if resp.status_code == 200:
    users = resp.json()
    user_12 = next((u for u in users if u['user_id'] == 12), None)

    if user_12:
        print(f"✓ User 12 (yoo@gmail.com) found in stats:")
        print(f"  Total exercises: {user_12.get('total_exercises')}")
        print(f"  Chat: {user_12.get('chat_count')}")
        print(f"  Roleplay: {user_12.get('roleplay_count')}")
        print(f"  Pronunciation: {user_12.get('pronunciation_count')}")
        print(f"  Total time: {user_12.get('total_duration_seconds')}s")
    else:
        print("⚠️  User 12 not found in stats (might be filtered)")
else:
    print(f"✗ Stats failed: {resp.status_code}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)

print("""
SUMMARY:
- If you see "✅ SUCCESS! New attempt recorded" above, tracking is working!
- Chat exercises now create ExerciseAttempt records
- Next steps:
  1. Test pronunciation endpoint (needs audio file)
  2. Test roleplay endpoint (complete a scenario)
  3. Verify all 3 exercise types show in admin dashboard
  4. Test from Android app to ensure end-to-end works
""")

