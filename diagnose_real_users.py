"""
Diagnose why real users still aren't showing up after doing activities
"""
import requests

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ5b29AZ21haWwuY29tIiwicm9sZXMiOlsiYWRtaW4iXSwiaWF0IjoxNzYzMzA1ODM4LCJleHAiOjE3NjMzMDY3MzgsInR5cGUiOiJhY2Nlc3MifQ.yF7BHeBfwU1aJb6YFIqupjIif3Jz1pk5rylOcNf7BwM"
headers = {'Authorization': f'Bearer {token}'}

print("=" * 70)
print("DIAGNOSIS: Why aren't real users showing up after doing activities?")
print("=" * 70)

# Real user IDs
real_users = {
    4: "sanjarqodirjanov@gmail.com",
    9: "sanjarfortwirpx@gmail.com",
    11: "bbbn@gmail.com",
    12: "yoo@gmail.com",
    13: "sanji@gmail.com"
}

print("\n1. Checking each real user's exercise attempts...")
for user_id, email in real_users.items():
    url = f'https://bizeng-server.fly.dev/admin/monitor/user_activity/{user_id}'
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('items', [])
            print(f"\n✓ User {user_id} ({email})")
            print(f"  Exercise attempts: {len(items)}")
            if len(items) > 0:
                for item in items[:3]:  # Show first 3
                    print(f"    - {item.get('exercise_type')} at {item.get('started_at')}")
            else:
                print(f"  ⚠️  ZERO exercise attempts found!")
        else:
            print(f"\n✗ User {user_id}: HTTP {resp.status_code}")
            print(f"  {resp.text[:100]}")
    except Exception as e:
        print(f"\n✗ User {user_id}: Error - {e}")

print("\n" + "=" * 70)
print("2. Checking /users_activity to see who IS showing up...")
print("=" * 70)

resp = requests.get('https://bizeng-server.fly.dev/admin/monitor/users_activity', headers=headers, timeout=20)
if resp.status_code == 200:
    data = resp.json()
    print(f"\nTotal users in report: {len(data)}")

    user_ids = [u['user_id'] for u in data]
    print(f"User IDs showing: {sorted(user_ids)}")

    real_in_report = [uid for uid in real_users.keys() if uid in user_ids]
    real_missing = [uid for uid in real_users.keys() if uid not in user_ids]

    print(f"\n✓ Real users IN report: {real_in_report}")
    print(f"✗ Real users MISSING: {real_missing}")

    if real_missing:
        print(f"\n⚠️  {len(real_missing)} real users still have no exercise attempts!")

print("\n" + "=" * 70)
print("POSSIBLE CAUSES:")
print("=" * 70)
print("""
If real users still don't show up after doing activities:

1. ❌ Android app NOT calling /tracking/attempts endpoints
   - Check: Are the tracking endpoints wired in Android?
   - Fix: Ensure chat/roleplay/pronunciation call tracking API

2. ❌ Users logged in but didn't complete the exercise
   - Check: Did they only START but not FINISH the exercise?
   - Fix: Both start AND finish are needed for duration/score

3. ❌ Exercises were done MORE than 30 days ago
   - Check: Default query filters last 30 days only
   - Fix: Try ?days=90 or ?days=365 parameter

4. ❌ Database connection issue during tracking
   - Check: Server logs for tracking errors
   - Fix: Check Fly logs: fly logs -a bizeng-server

5. ❌ User authentication issue
   - Check: Are users properly authenticated when doing exercises?
   - Fix: Verify JWT token is valid and user_id is correct

IMMEDIATE ACTION:
- Check Android code to see if it calls POST /tracking/attempts
- Check server logs during user activity
- Try manually inserting one attempt to verify query works
""")

with open('user_diagnosis_detailed.txt', 'w', encoding='utf-8') as f:
    f.write("Detailed diagnosis saved\n")
    f.write(f"Real users checked: {list(real_users.keys())}\n")

print("\n✅ Diagnosis complete. Check output above for issues.")

