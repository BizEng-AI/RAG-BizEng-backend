"""
Final verification - Check roles and users_activity endpoint
"""
import requests

BASE_URL = "https://bizeng-server.fly.dev"

print("="*70)
print("FINAL VERIFICATION")
print("="*70)

# Login
resp = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "yoo@gmail.com",
    "password": "qwerty"
})
resp.raise_for_status()
token = resp.json()['access_token']
headers = {"Authorization": f"Bearer {token}"}

print("\n✅ Logged in as yoo@gmail.com")

# Check yoo's roles
resp = requests.get(f"{BASE_URL}/me", headers=headers)
resp.raise_for_status()
me_data = resp.json()
print(f"\nyoo@gmail.com roles: {me_data.get('roles', [])}")
if 'admin' in me_data.get('roles', []) and 'student' in me_data.get('roles', []):
    print("  ⚠️  Has BOTH admin and student roles")
    print("  → This is OK, but yoo shows up in student list AND has admin access")
elif 'admin' in me_data.get('roles', []):
    print("  ✓ Admin only (good)")
else:
    print("  ✓ Student only")

# Get all registered students
resp = requests.get(f"{BASE_URL}/admin/students", headers=headers)
resp.raise_for_status()
students = resp.json()
print(f"\n/admin/students: {len(students)} students")

# Get users_activity
resp = requests.get(f"{BASE_URL}/admin/monitor/users_activity", headers=headers)
resp.raise_for_status()
activity = resp.json()
print(f"/admin/monitor/users_activity: {len(activity)} users")

zero_attempts = [u for u in activity if u.get('total_exercises', 0) == 0]
with_attempts = [u for u in activity if u.get('total_exercises', 0) > 0]

print(f"\n  Users with 0 attempts: {len(zero_attempts)}")
print(f"  Users with >0 attempts: {len(with_attempts)}")

if len(zero_attempts) > 0:
    print("\n✅ SUCCESS! Users with zero attempts are included:")
    for u in zero_attempts[:5]:
        print(f"    - {u.get('email')} (ID: {u.get('user_id')})")

if len(with_attempts) > 0:
    print("\n  Users with activity:")
    for u in with_attempts[:5]:
        print(f"    - {u.get('email')} (ID: {u.get('user_id')}) - {u.get('total_exercises')} exercises")

# Compare counts
print(f"\n📊 Summary:")
print(f"  Registered students: {len(students)}")
print(f"  In users_activity: {len(activity)}")

if len(activity) == len(students):
    print("  ✅ PERFECT MATCH!")
elif len(activity) == len(students) + 1:
    print("  ℹ️  One extra user (likely yoo@gmail.com who is admin+student)")
else:
    print(f"  ⚠️  Mismatch: {len(activity) - len(students)} difference")

print("\n" + "="*70)
print("VERIFICATION COMPLETE")
print("="*70)

