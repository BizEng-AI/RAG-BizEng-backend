# 🧪 TESTING & DEPLOYMENT GUIDE - STEP BY STEP

**Status:** Ready to test  
**Date:** November 11, 2025

---

## ⚠️ IMPORTANT: Manual Testing Required

Due to terminal output limitations, please run these commands **manually** in PowerShell.

---

## 📦 STEP 1: VERIFY DEPENDENCIES

Open PowerShell in the server directory:
```powershell
cd C:\Users\sanja\rag-biz-english\server
```

Test imports:
```powershell
python -c "import passlib; import jose; import sqlalchemy; import psycopg; print('✅ Dependencies OK')"
```

**Expected:** `✅ Dependencies OK`

If you see an error, install:
```powershell
pip install passlib[bcrypt] python-jose[cryptography] sqlalchemy psycopg[binary] alembic
```

---

## 🗄️ STEP 2: TEST DATABASE CONNECTION

```powershell
python test_neon_sync.py
```

**Expected output:**
```
Testing connection to Neon PostgreSQL...
✅ SUCCESS! Connection working!
PostgreSQL version: PostgreSQL 17.2...
Test query result: hello world
```

If this fails:
- Check DATABASE_URL in `.env` file
- Verify Neon database is active
- Check your internet connection

---

## 🏗️ STEP 3: VERIFY IMPORTS

```powershell
python test_imports.py
```

**Expected output:**
```
Testing imports...
1. Testing settings...
   ✅ DATABASE_URL: postgresql+psycopg://...
   ✅ JWT_SECRET: set

2. Testing db...
   ✅ DB module imported

3. Testing models...
   ✅ Models imported

4. Testing security...
   ✅ Security module imported

5. Testing routers...
   ✅ All routers imported

6. Creating database tables...
   ✅ Tables created/verified

7. Testing app import...
   ✅ App imported successfully
```

If any step fails, check the error message and fix imports/dependencies.

---

## 🚀 STEP 4: START THE SERVER

```powershell
uvicorn app:app --reload --port 8020
```

**Expected output:**
```
[startup] app.py reloaded OK
[startup] ✅ Qdrant client initialized
[startup] ✅ Database tables created/verified
[startup] ✅ Default roles seeded
INFO:     Uvicorn running on http://0.0.0.0:8020
```

**Keep this terminal open** - the server is now running.

---

## 🧪 STEP 5: RUN AUTHENTICATION TESTS

**Open a NEW PowerShell window** (keep server running):

```powershell
cd C:\Users\sanja\rag-biz-english\server
python test_auth_system.py
```

**Expected output:**
```
======================================================================
TESTING AUTHENTICATION SYSTEM
======================================================================

1️⃣ Testing /health...
   Status: 200
   Response: {'status': 'ok', 'service': 'bizeng-server'}
   ✅ Server is running

2️⃣ Testing POST /auth/register...
   Status: 201
   ✅ Registration successful!
   Access token: eyJ...
   Refresh token: abc123...

3️⃣ Testing GET /me (authenticated)...
   Status: 200
   ✅ Profile retrieved!
   User ID: 1
   Email: student1@test.com
   Name: Test Student
   Group: A1
   Roles: ['student']

4️⃣ Testing POST /auth/refresh...
   Status: 200
   ✅ Token refresh successful!

5️⃣ Testing POST /tracking/events...
   Status: 201
   ✅ Event logged!

6️⃣ Testing POST /tracking/attempts...
   Status: 201
   ✅ Attempt started!

7️⃣ Testing PATCH /tracking/attempts/{id}...
   Status: 200
   ✅ Attempt completed!
   Score: 0.85
   Duration: 180s
   Passed: True

8️⃣ Testing GET /admin/dashboard (should be 403)...
   Status: 403
   ✅ Correctly blocked non-admin user

9️⃣ Testing POST /auth/logout...
   Status: 200
   ✅ Logout successful!

======================================================================
AUTHENTICATION TEST COMPLETE
======================================================================

Summary:
  ✅ Registration/Login working
  ✅ JWT tokens issued
  ✅ Token refresh working
  ✅ Profile endpoint working
  ✅ Activity tracking working
  ✅ Exercise attempts tracking working
  ✅ RBAC protection working
```

---

## 👤 STEP 6: CREATE ADMIN ACCOUNT

```powershell
python grant_admin.py student1@test.com
```

**Expected output:**
```
✅ Granted admin role to student1@test.com
   User ID: 1
   User now has roles: ['student', 'admin']
```

Now test admin endpoints by logging in again:

```powershell
# In test_auth_system.py, the new login will get admin token
# Or manually test:
curl -X POST http://localhost:8020/auth/login `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"student1@test.com\",\"password\":\"test1234\"}'

# Copy the access_token from response

curl http://localhost:8020/admin/dashboard `
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Expected:** Dashboard statistics (not 403 error)

---

## 🌐 STEP 7: DEPLOY TO FLY.IO

### Set Secrets
```powershell
fly secrets set `
  JWT_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" `
  JWT_ALG=HS256 `
  ACCESS_EXPIRES_MIN=15 `
  REFRESH_EXPIRES_DAYS=30 `
  --app bizeng-server
```

### Deploy
```powershell
fly deploy --app bizeng-server
```

**Wait 2-3 minutes** for deployment to complete.

### Test Production
```powershell
curl https://bizeng-server.fly.dev/health

curl https://bizeng-server.fly.dev/version
```

**Expected:**
```json
{"status":"ok","service":"bizeng-server"}
{"version":"1.0.0","features":["auth","roleplay","chat","pronunciation","admin_analytics"]}
```

---

## 🔍 STEP 8: TEST PRODUCTION ENDPOINTS

### Register in production:
```powershell
curl -X POST https://bizeng-server.fly.dev/auth/register `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"teacher@example.com\",\"password\":\"SecurePass123\",\"display_name\":\"Teacher Account\"}'
```

Save the tokens from response.

### Grant admin role in production:

**Option 1:** Use Neon console (SQL query):
```sql
-- Find user ID
SELECT id, email FROM users WHERE email = 'teacher@example.com';

-- Grant admin role
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id 
FROM users u, roles r 
WHERE u.email = 'teacher@example.com' AND r.name = 'admin'
ON CONFLICT DO NOTHING;
```

**Option 2:** SSH into Fly.io and run grant script:
```powershell
fly ssh console --app bizeng-server

# Inside the container:
cd /app
python grant_admin.py teacher@example.com
exit
```

### Test admin dashboard:
```powershell
# Login to get admin token
curl -X POST https://bizeng-server.fly.dev/auth/login `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"teacher@example.com\",\"password\":\"SecurePass123\"}'

# Use access_token to call admin endpoint
curl https://bizeng-server.fly.dev/admin/dashboard `
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## ✅ VERIFICATION CHECKLIST

After completing all steps, verify:

### Local Testing
- [ ] Dependencies installed
- [ ] Database connection works
- [ ] All imports successful
- [ ] Server starts without errors
- [ ] Health endpoint responds
- [ ] Registration creates user
- [ ] Login returns tokens
- [ ] Token refresh works
- [ ] Profile endpoint works
- [ ] Exercise tracking works
- [ ] Activity logging works
- [ ] Admin role assignment works
- [ ] Admin endpoints protected (403 for non-admin)
- [ ] Admin endpoints work (200 for admin)

### Production Testing
- [ ] Fly.io secrets set (JWT_SECRET, etc.)
- [ ] Deployment successful
- [ ] Health endpoint responds
- [ ] Version endpoint responds
- [ ] Can register new user
- [ ] Can login
- [ ] Can access protected endpoints
- [ ] Admin account created
- [ ] Admin dashboard works

---

## 🐛 TROUBLESHOOTING

### Server won't start
**Check:**
- DATABASE_URL in `.env`
- All dependencies installed
- Port 8020 not in use: `netstat -ano | findstr :8020`

**Fix:**
```powershell
# Kill process on port 8020
taskkill /PID <PID> /F

# Restart server
uvicorn app:app --reload --port 8020
```

### Import errors
**Check:**
- Virtual environment activated: `.venv\Scripts\activate`
- Dependencies installed in correct environment

**Fix:**
```powershell
pip install -r requirements.txt
```

### Database connection fails
**Check:**
- DATABASE_URL format: `postgresql+psycopg://...`
- Neon database is active (not hibernating)
- Internet connection

**Fix:**
- Wait for Neon to wake up (30 seconds)
- Check Neon dashboard: https://console.neon.tech

### 401 Unauthorized
**Reasons:**
- Token expired (15 min for access token)
- JWT_SECRET mismatch (local vs production)
- User not found in database

**Fix:**
- Login again to get fresh token
- Use refresh token endpoint
- Verify user exists in database

### 403 Forbidden
**Reasons:**
- User doesn't have required role
- Not an admin trying to access admin endpoint

**Fix:**
- Grant admin role: `python grant_admin.py <email>`
- Login again to get token with new roles

---

## 📊 EXPECTED DATABASE STATE

After successful testing, your database should have:

### Roles table:
- admin
- student

### Users table:
- student1@test.com (roles: student, admin)
- Any other registered users

### Exercise attempts:
- At least 1 from test script

### Activity events:
- At least 1 from test script

### Refresh tokens:
- Multiple tokens (some revoked)

**Check in Neon console:**
```sql
SELECT COUNT(*) FROM users;  -- Should be >= 1
SELECT COUNT(*) FROM roles;  -- Should be 2
SELECT COUNT(*) FROM user_roles;  -- Should be >= 1
SELECT COUNT(*) FROM exercise_attempts;  -- Should be >= 1
SELECT COUNT(*) FROM activity_events;  -- Should be >= 1
```

---

## 🎯 SUCCESS CRITERIA

You've successfully completed setup when:

1. ✅ All tests pass locally
2. ✅ Server runs without errors
3. ✅ Can register and login
4. ✅ Tokens work and refresh
5. ✅ Exercise tracking logs attempts
6. ✅ Admin account can access dashboard
7. ✅ Production deployment works
8. ✅ Production endpoints respond correctly

---

## 📞 NEXT ACTIONS

### Immediate:
1. Run through this guide step-by-step
2. Fix any errors that appear
3. Verify all tests pass

### This Week:
1. Share `ANDROID_AUTH_INTEGRATION.md` with Android team
2. Create your mom's admin account in production
3. Test admin dashboard with real data

### Next Week:
1. Android team implements authentication
2. Test with real students
3. Monitor analytics dashboard

---

**Run all these commands manually and check results!**  
**Document any errors you encounter.**  
**Status after completion: PRODUCTION READY** ✅

