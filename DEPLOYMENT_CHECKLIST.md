# ✅ BACKEND DEPLOYMENT CHECKLIST

**Date:** November 11, 2025  
**Status:** ✅ All tests passed (7/7)

---

## 🚀 DEPLOY TO PRODUCTION NOW

### Step 1: Set JWT Secret (1 minute)

```powershell
cd C:\Users\sanja\rag-biz-english\server

fly secrets set JWT_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" --app bizeng-server
```

### Step 2: Deploy (3-5 minutes)

```powershell
fly deploy --app bizeng-server
```

Wait for deployment to complete...

### Step 3: Test Production (30 seconds)

```powershell
# Health check
curl https://bizeng-server.fly.dev/health

# Version check
curl https://bizeng-server.fly.dev/version
```

**Expected:**
```json
{"status":"ok","service":"bizeng-server"}
{"version":"1.0.0","features":["auth","roleplay","chat","pronunciation","admin_analytics"]}
```

---

## 👤 CREATE ADMIN ACCOUNT

### Option 1: SSH into Fly.io

```powershell
fly ssh console --app bizeng-server

# Inside the container
cd /app
python grant_admin.py YOUR_MOM_EMAIL@example.com
exit
```

### Option 2: Neon Console (SQL)

Go to: https://console.neon.tech

```sql
-- Find user ID
SELECT id, email FROM users WHERE email = 'YOUR_MOM_EMAIL@example.com';

-- Grant admin role (use the user ID from above)
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id 
FROM users u, roles r 
WHERE u.email = 'YOUR_MOM_EMAIL@example.com' 
  AND r.name = 'admin'
ON CONFLICT DO NOTHING;
```

---

## 📱 SHARE WITH ANDROID TEAM

Send them:

1. **`ANDROID_COMPLETE_GUIDE.md`** ← Full integration guide
2. **`ANDROID_QUICK_REF.md`** ← Quick reference
3. **Production URL:** `https://bizeng-server.fly.dev`
4. **Critical:** Field name changed to `extra_metadata`

---

## 🧪 TEST PRODUCTION ENDPOINTS

### Register Test Account

```powershell
curl -X POST https://bizeng-server.fly.dev/auth/register `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"test@example.com\",\"password\":\"test1234\",\"display_name\":\"Test User\"}'
```

Save the `access_token` from response.

### Test Protected Endpoint

```powershell
curl https://bizeng-server.fly.dev/me `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Test Admin Dashboard

```powershell
# Login as admin first, then:
curl https://bizeng-server.fly.dev/admin/dashboard `
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

---

## 📊 MONITORING

### Check Logs

```powershell
fly logs --app bizeng-server
```

### Check Status

```powershell
fly status --app bizeng-server
```

### Check Metrics

```powershell
fly dashboard --app bizeng-server
```

---

## ✅ DEPLOYMENT CHECKLIST

- [ ] JWT_SECRET set on Fly.io
- [ ] Deployed successfully (`fly deploy`)
- [ ] Health endpoint responds
- [ ] Version endpoint responds
- [ ] Can register new user
- [ ] Can login
- [ ] Protected endpoints work with token
- [ ] Admin account created
- [ ] Admin dashboard works
- [ ] Android team has documentation
- [ ] Production URL shared

---

## 🎉 YOU'RE DONE!

**Backend:** ✅ Production Ready  
**Android:** ✅ Ready to integrate  
**Admin:** ✅ Can track students  

**Next:** Android team implements client-side integration (2-3 days)

---

## 📞 QUICK COMMANDS

### Restart Server
```powershell
fly restart --app bizeng-server
```

### Update Environment Variable
```powershell
fly secrets set VARIABLE_NAME="value" --app bizeng-server
```

### View All Secrets
```powershell
fly secrets list --app bizeng-server
```

### Redeploy After Code Changes
```powershell
cd C:\Users\sanja\rag-biz-english\server
git add .
git commit -m "Update"
git push
fly deploy --app bizeng-server
```

---

**Status:** ✅ **READY TO DEPLOY - FOLLOW STEPS ABOVE**

**Time to Production:** 5-10 minutes  
**Time for Android:** 2-3 days implementation

