"""Simple endpoint test"""
import requests

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ5b29AZ21haWwuY29tIiwicm9sZXMiOlsiYWRtaW4iXSwiaWF0IjoxNzYzMzA1ODM4LCJleHAiOjE3NjMzMDY3MzgsInR5cGUiOiJhY2Nlc3MifQ.yF7BHeBfwU1aJb6YFIqupjIif3Jz1pk5rylOcNf7BwM"
headers = {'Authorization': f'Bearer {token}'}

print("Testing /admin/monitor/users_activity")
resp = requests.get('https://bizeng-server.fly.dev/admin/monitor/users_activity', headers=headers, timeout=20)
with open('users_activity_test.txt', 'w', encoding='utf-8') as f:
    f.write(f"Status: {resp.status_code}\n")
    f.write(f"Response: {resp.text}\n")
print(f"Status: {resp.status_code}")

print("\nTesting /admin/monitor/groups_activity")
resp = requests.get('https://bizeng-server.fly.dev/admin/monitor/groups_activity', headers=headers, timeout=20)
with open('groups_activity_test.txt', 'w', encoding='utf-8') as f:
    f.write(f"Status: {resp.status_code}\n")
    f.write(f"Response: {resp.text}\n")
print(f"Status: {resp.status_code}")

print("\nTesting /admin/monitor/user_activity/12")
resp = requests.get('https://bizeng-server.fly.dev/admin/monitor/user_activity/12', headers=headers, timeout=20)
with open('user_activity_test.txt', 'w', encoding='utf-8') as f:
    f.write(f"Status: {resp.status_code}\n")
    f.write(f"Response: {resp.text}\n")
print(f"Status: {resp.status_code}")

print("\nDone - check *_test.txt files")

