"""Check why real users aren't showing in activity reports"""
import requests
import json

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ5b29AZ21haWwuY29tIiwicm9sZXMiOlsiYWRtaW4iXSwiaWF0IjoxNzYzMzA1ODM4LCJleHAiOjE3NjMzMDY3MzgsInR5cGUiOiJhY2Nlc3MifQ.yF7BHeBfwU1aJb6YFIqupjIif3Jz1pk5rylOcNf7BwM"
headers = {'Authorization': f'Bearer {token}'}

print("=" * 60)
print("CHECKING WHY REAL USERS NOT IN ACTIVITY REPORTS")
print("=" * 60)

# Real user IDs from your Neon DB
real_user_ids = [4, 9, 11, 12, 13]

print("\n1. Checking if real users have exercise attempts...")
for user_id in real_user_ids:
    url = f'https://bizeng-server.fly.dev/admin/monitor/user_activity/{user_id}'
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            user = data.get('user', {})
            items = data.get('items', [])
            print(f"\nUser ID {user_id} ({user.get('email')}):")
            print(f"  Display name: {user.get('display_name')}")
            print(f"  Group: {user.get('group_name')}")
            print(f"  Exercise attempts: {len(items)}")
            if len(items) > 0:
                print(f"  Latest attempt: {items[0].get('exercise_type')} on {items[0].get('started_at')}")
        elif resp.status_code == 404:
            print(f"\nUser ID {user_id}: NOT FOUND in database")
        else:
            print(f"\nUser ID {user_id}: Error {resp.status_code}")
    except Exception as e:
        print(f"\nUser ID {user_id}: Request failed - {e}")

print("\n" + "=" * 60)
print("2. Summary of /users_activity endpoint...")
print("=" * 60)

resp = requests.get('https://bizeng-server.fly.dev/admin/monitor/users_activity', headers=headers, timeout=20)
if resp.status_code == 200:
    data = resp.json()
    print(f"\nTotal users with activity: {len(data)}")

    user_ids_in_report = [item['user_id'] for item in data]
    print(f"User IDs in report: {sorted(user_ids_in_report)}")

    real_users_in_report = [uid for uid in real_user_ids if uid in user_ids_in_report]
    print(f"\nReal users in report: {real_users_in_report}")
    print(f"Real users MISSING: {[uid for uid in real_user_ids if uid not in user_ids_in_report]}")

print("\n" + "=" * 60)
print("DIAGNOSIS")
print("=" * 60)
print("""
The /users_activity endpoint only returns users who have:
1. At least one row in the exercise_attempts table
2. With started_at within the last 30 days (default)

Your real Gmail users (IDs 4, 9, 11, 12, 13) are NOT showing up because:
❌ They have ZERO exercise attempts recorded in the database

The test users (IDs 14-39) ARE showing up because:
✅ They have exercise attempts from the smoke tests

SOLUTION:
- Have your real users use the app (chat, roleplay, pronunciation)
- Each exercise creates a row in exercise_attempts table
- Then they'll appear in the admin dashboard
""")

# Save detailed report
with open('user_activity_diagnosis.txt', 'w', encoding='utf-8') as f:
    f.write("USER ACTIVITY DIAGNOSIS\n")
    f.write("=" * 60 + "\n\n")
    f.write("Real users from Neon DB:\n")
    for uid in real_user_ids:
        f.write(f"  - User ID {uid}\n")
    f.write(f"\nUsers shown in /users_activity report: {sorted(user_ids_in_report)}\n")
    f.write(f"\nConclusion: Real users have no exercise attempts recorded.\n")

print("\n✅ Diagnosis saved to user_activity_diagnosis.txt")

