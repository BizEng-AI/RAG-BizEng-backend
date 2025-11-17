"""Test new admin endpoints with fresh token"""
import requests
import json
from pathlib import Path

# Load token
with open('admin_fix_result.json', 'r', encoding='utf-8') as f:
    token_data = json.load(f)

token = token_data['access_token']
headers = {'Authorization': f'Bearer {token}'}
base = 'https://bizeng-server.fly.dev'

print(f"✅ Using token for: {token_data['email']}")
print(f"Roles: {token_data['after_roles']}\n")

# Test the NEW endpoints
new_endpoints = [
    'users_activity',
    'groups_activity',
    'user_activity/12'  # Test with user ID 12 (yoo@gmail.com)
]

results = {}

for ep in new_endpoints:
    url = f"{base}/admin/monitor/{ep}"
    print(f"Testing: {url}")
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        status = resp.status_code
        print(f"  Status: {status}")

        if status == 200:
            data = resp.json()
            print(f"  ✅ SUCCESS - Response length: {len(json.dumps(data))} chars")
            if isinstance(data, list):
                print(f"  Items in response: {len(data)}")
            elif isinstance(data, dict):
                print(f"  Keys: {list(data.keys())}")
        else:
            print(f"  ❌ FAILED - {resp.text[:200]}")

        results[ep] = {'status': status, 'response': resp.text[:500]}
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        results[ep] = {'error': str(e)}
    print()

# Save results
with open('new_endpoints_test.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n✅ Results saved to new_endpoints_test.json")

# Summary
working = sum(1 for r in results.values() if r.get('status') == 200)
total = len(results)
print(f"\n{'='*60}")
print(f"SUMMARY: {working}/{total} new endpoints working")
print(f"{'='*60}")

