"""
Test that users_activity endpoint now returns ALL users
"""
import requests

BASE_URL = "http://localhost:8020"  # Test locally first

print("="*70)
print("TESTING users_activity ENDPOINT - Should Return ALL Users")
print("="*70)

# Login as admin
print("\n1. Logging in as admin...")
resp = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "yoo@gmail.com",
    "password": "qwerty"
})

if resp.status_code != 200:
    print(f"✗ Login failed: {resp.status_code}")
    print("Switch to production URL...")
    BASE_URL = "https://bizeng-server.fly.dev"

    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "yoo@gmail.com",
        "password": "qwerty"
    })

    if resp.status_code != 200:
        print(f"✗ Login failed on production too: {resp.status_code}")
        exit(1)

token = resp.json().get("access_token")
print(f"✓ Login successful")

headers = {"Authorization": f"Bearer {token}"}

# Get all users from admin endpoint
print("\n2. Fetching all users from /admin/students...")
resp = requests.get(f"{BASE_URL}/admin/students", headers=headers, timeout=30)

if resp.status_code == 200:
    all_users = resp.json().get('students', [])
    print(f"✓ Total registered users: {len(all_users)}")

    # Show sample
    print("\nSample registered users:")
    for user in all_users[:5]:
        print(f"  - {user.get('email')} (ID: {user.get('id')})")
else:
    print(f"✗ Failed to get users: {resp.status_code}")
    all_users = []

# Get users with activity
print("\n3. Fetching users_activity (should match registered users)...")
resp = requests.get(f"{BASE_URL}/admin/monitor/users_activity", headers=headers, timeout=30)

if resp.status_code == 200:
    activity_users = resp.json()
    print(f"✓ Users returned: {len(activity_users)}")

    # Count users with zero attempts
    zero_attempts = [u for u in activity_users if u.get('total_exercises', 0) == 0]
    with_attempts = [u for u in activity_users if u.get('total_exercises', 0) > 0]

    print(f"\n  Users with attempts: {len(with_attempts)}")
    print(f"  Users with ZERO attempts: {len(zero_attempts)}")

    # Show users with zero attempts (should now appear!)
    if zero_attempts:
        print(f"\n✅ SUCCESS! Users with zero attempts are now included:")
        for user in zero_attempts[:5]:
            print(f"    - {user.get('email')} (ID: {user.get('user_id')}) - {user.get('total_exercises')} exercises")
    else:
        print("\n⚠️  No users with zero attempts found (all users have done exercises)")

    # Show users with attempts
    if with_attempts:
        print(f"\n  Users with activity:")
        for user in with_attempts[:5]:
            print(f"    - {user.get('email')} (ID: {user.get('user_id')}) - {user.get('total_exercises')} exercises")

    # Compare counts
    if len(all_users) > 0:
        coverage = (len(activity_users) / len(all_users)) * 100
        print(f"\n  Coverage: {len(activity_users)}/{len(all_users)} users ({coverage:.1f}%)")

        if len(activity_users) == len(all_users):
            print("  ✅ PERFECT! All registered users are returned!")
        elif len(activity_users) < len(all_users):
            print(f"  ⚠️  Missing {len(all_users) - len(activity_users)} users")
        else:
            print("  ⚠️  More activity users than registered users (unexpected)")

else:
    print(f"✗ Failed: {resp.status_code}")
    print(resp.text[:200])

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)

