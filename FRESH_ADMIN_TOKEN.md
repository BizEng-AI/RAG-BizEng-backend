# 🔐 FRESH ADMIN ACCESS TOKEN

**Generated:** November 16, 2025, 2:37 PM  
**User:** yoo@gmail.com  
**Roles:** ["admin"]  
**Expires:** 15 minutes from generation (standard JWT expiry)

---

## ✅ Access Token

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ5b29AZ21haWwuY29tIiwicm9sZXMiOlsiYWRtaW4iXSwiaWF0IjoxNzYzMzA1ODM4LCJleHAiOjE3NjMzMDY3MzgsInR5cGUiOiJhY2Nlc3MifQ.yF7BHeBfwU1aJb6YFIqupjIif3Jz1pk5rylOcNf7BwM
```

---

## 🧪 How to Test New Endpoints

### PowerShell Commands

```powershell
$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ5b29AZ21haWwuY29tIiwicm9sZXMiOlsiYWRtaW4iXSwiaWF0IjoxNzYzMzA1ODM4LCJleHAiOjE3NjMzMDY3MzgsInR5cGUiOiJhY2Nlc3MifQ.yF7BHeBfwU1aJb6YFIqupjIif3Jz1pk5rylOcNf7BwM"
$hdr = @{ Authorization = "Bearer $token" }

# Test users_activity
Invoke-RestMethod -Uri "https://bizeng-server.fly.dev/admin/monitor/users_activity?days=30" -Headers $hdr

# Test groups_activity
Invoke-RestMethod -Uri "https://bizeng-server.fly.dev/admin/monitor/groups_activity?days=30" -Headers $hdr

# Test user_activity for user ID 12 (yoo@gmail.com)
Invoke-RestMethod -Uri "https://bizeng-server.fly.dev/admin/monitor/user_activity/12?days=30" -Headers $hdr
```

### Python Test Script

```python
import requests

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ5b29AZ21haWwuY29tIiwicm9sZXMiOlsiYWRtaW4iXSwiaWF0IjoxNzYzMzA1ODM4LCJleHAiOjE3NjMzMDY3MzgsInR5cGUiOiJhY2Nlc3MifQ.yF7BHeBfwU1aJb6YFIqupjIif3Jz1pk5rylOcNf7BwM"
headers = {'Authorization': f'Bearer {token}'}

# Test users_activity
resp = requests.get('https://bizeng-server.fly.dev/admin/monitor/users_activity', headers=headers)
print(f"users_activity: {resp.status_code}")
print(resp.json()[:2] if resp.status_code == 200 else resp.text)

# Test groups_activity
resp = requests.get('https://bizeng-server.fly.dev/admin/monitor/groups_activity', headers=headers)
print(f"\ngroups_activity: {resp.status_code}")
print(resp.json() if resp.status_code == 200 else resp.text)

# Test user_activity/12
resp = requests.get('https://bizeng-server.fly.dev/admin/monitor/user_activity/12', headers=headers)
print(f"\nuser_activity/12: {resp.status_code}")
print(resp.json() if resp.status_code == 200 else resp.text)
```

### Curl Command

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ5b29AZ21haWwuY29tIiwicm9sZXMiOlsiYWRtaW4iXSwiaWF0IjoxNzYzMzA1ODM4LCJleHAiOjE3NjMzMDY3MzgsInR5cGUiOiJhY2Nlc3MifQ.yF7BHeBfwU1aJb6YFIqupjIif3Jz1pk5rylOcNf7BwM" \
  https://bizeng-server.fly.dev/admin/monitor/users_activity
```

---

## 📝 Expected Responses

### ✅ If Endpoints Are Deployed (Status 200)

**users_activity:**
```json
[
  {
    "user_id": 39,
    "email": "test+1415a786@example.com",
    "display_name": "SmokeTester",
    "group_name": null,
    "total_exercises": 1,
    "pronunciation_count": 0,
    "chat_count": 0,
    "roleplay_count": 1,
    "total_duration_seconds": 120,
    "avg_pronunciation_score": null
  }
]
```

**groups_activity:**
```json
[
  {
    "group_name": "Unassigned",
    "student_count": 39,
    "total_exercises": 10,
    "pronunciation_count": 0,
    "chat_count": 0,
    "roleplay_count": 10,
    "total_duration_seconds": 1200,
    "avg_pronunciation_score": null
  }
]
```

**user_activity/12:**
```json
{
  "user": {
    "id": 12,
    "email": "yoo@gmail.com",
    "display_name": null,
    "group_name": null
  },
  "items": []
}
```

### ❌ If Not Deployed (Status 404)

```json
{
  "detail": "Not Found"
}
```

---

## 🔄 How to Get Fresh Token (When This Expires)

```bash
cd C:\Users\sanja\rag-biz-english\server
python admin_fix_and_token.py yoo@gmail.com
# Token will be in admin_fix_result.json
```

---

## 📊 What We Know

1. ✅ **Code is deployed** - `fly deploy` completed successfully
2. ✅ **Local server works** - All endpoints tested locally with 200 OK
3. ⚠️ **Production verification blocked** - PowerShell is suppressing all python output
4. ✅ **Fresh token generated** - Valid for next 15 minutes

---

## 🎯 Next Action

**You need to run ONE of the test commands above** to verify the endpoints are live on production.

The simplest option is to copy-paste this into a **new PowerShell window**:

```powershell
$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ5b29AZ21haWwuY29tIiwicm9sZXMiOlsiYWRtaW4iXSwiaWF0IjoxNzYzMzA1ODM4LCJleHAiOjE3NjMzMDY3MzgsInR5cGUiOiJhY2Nlc3MifQ.yF7BHeBfwU1aJb6YFIqupjIif3Jz1pk5rylOcNf7BwM"
Invoke-RestMethod -Uri "https://bizeng-server.fly.dev/admin/monitor/users_activity" -Headers @{Authorization="Bearer $token"}
```

If you get JSON data back → ✅ Endpoints are deployed and working!  
If you get 404 → ❌ Need to troubleshoot deployment.

---

**Token expires at:** ~2:52 PM (15 min from 2:37 PM generation time)

