"""Quick script to get fresh admin token"""
import requests
import sys

try:
    resp = requests.post(
        'https://bizeng-server.fly.dev/auth/login',
        json={'email': 'yoo@gmail.com', 'password': 'qwerty'},
        timeout=20
    )
    print(f"Status: {resp.status_code}")

    if resp.status_code == 200:
        data = resp.json()
        print(f"\n✅ Login successful!")
        print(f"\nAccess Token:\n{data.get('access_token')}")
        print(f"\nRefresh Token:\n{data.get('refresh_token')}")
        print(f"\nUser: {data.get('user', {}).get('email')}")
        print(f"Roles: {data.get('user', {}).get('roles', [])}")

        # Save to file for easy copy
        with open('admin_token.txt', 'w', encoding='utf-8') as f:
            f.write(data.get('access_token', ''))
        print(f"\n✅ Token saved to admin_token.txt")
    else:
        print(f"\n❌ Login failed: {resp.text}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

