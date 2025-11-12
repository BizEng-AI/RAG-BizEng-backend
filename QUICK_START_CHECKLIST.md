# ✅ QUICK START CHECKLIST - DO THIS NOW

**Time Required:** 15-20 minutes  
**Prerequisites:** PowerShell open in server directory

---

## 🚀 EXECUTE THESE COMMANDS IN ORDER

### 1️⃣ Navigate to Server Directory
```powershell
cd C:\Users\sanja\rag-biz-english\server
```

---

### 2️⃣ Verify Dependencies
```powershell
# Install all dependencies (including email-validator and upgraded bcrypt)
pip install -r requirements.txt --upgrade

# Test imports
python -c "import passlib; import jose; import pydantic; from pydantic import EmailStr; print('✅ All dependencies OK')"
```
✅ If you see "✅ All dependencies OK", continue  
❌ If error, check the error message and install missing packages

---

### 3️⃣ Test Database
```powershell
python test_neon_sync.py
```
✅ Should see: "✅ SUCCESS! Connection working!" and PostgreSQL version  
❌ If error, check DATABASE_URL in `.env` file

---

### 4️⃣ Verify All Imports
```powershell
python test_system_verification.py
```
✅ All 7 tests should pass  
❌ If any fail, check the error message and fix

**This comprehensive test checks:**
- Environment variables
- Dependencies installed
- Database connection
- Models defined
- Security functions
- API routers
- FastAPI app

---

### 5️⃣ Start Server (New Terminal)
```powershell
uvicorn app:app --reload --port 8020
```
✅ Should see: "Uvicorn running on http://0.0.0.0:8020"  
❌ If error, check for port conflicts

**Keep this terminal open!**

---

### 6️⃣ Run Tests (In ANOTHER Terminal)
```powershell
cd C:\Users\sanja\rag-biz-english\server
python test_auth_system.py
```
✅ Should see 9 tests pass  
❌ If error, check server is running

---

### 7️⃣ Create Admin Account
```powershell
python grant_admin.py student1@test.com
```
✅ Should see: "Granted admin role to student1@test.com"

---

### 8️⃣ Test Admin Access
Login again to get admin token, then:
```powershell
# Manual test or re-run test_auth_system.py
# Admin endpoints should now return 200, not 403
```

---

### 9️⃣ Deploy to Production
```powershell
# Set secrets
fly secrets set JWT_SECRET="your-very-long-random-string-at-least-32-chars" --app bizeng-server

# Deploy
fly deploy --app bizeng-server
```
✅ Wait 2-3 minutes for deployment  
❌ If error, check Fly.io logs: `fly logs --app bizeng-server`

---

### 🔟 Test Production
```powershell
curl https://bizeng-server.fly.dev/health
```
✅ Should see: `{"status":"ok"}`

---

## 📋 COPY-PASTE COMPLETE SEQUENCE

```powershell
# Terminal 1: Start Server
cd C:\Users\sanja\rag-biz-english\server
uvicorn app:app --reload --port 8020
```

```powershell
# Terminal 2: Run Tests
cd C:\Users\sanja\rag-biz-english\server
python test_neon_sync.py
python test_imports.py
python test_auth_system.py
python grant_admin.py student1@test.com
```

```powershell
# Terminal 3: Deploy
cd C:\Users\sanja\rag-biz-english\server
fly secrets set JWT_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" --app bizeng-server
fly deploy --app bizeng-server
curl https://bizeng-server.fly.dev/health
```

---

## ✅ DONE!

When all commands complete successfully:
1. ✅ Local server is running
2. ✅ All tests pass
3. ✅ Admin account exists
4. ✅ Production is deployed
5. ✅ Production endpoints respond

**You're ready for Android integration!**

---

## 📱 SHARE WITH ANDROID TEAM

Send these files:
1. `ANDROID_AUTH_INTEGRATION.md` - Complete implementation guide
2. `AUTH_SYSTEM_COMPLETE.md` - API reference
3. Production URL: `https://bizeng-server.fly.dev`

---

## 🎯 YOUR STATUS RIGHT NOW

- ✅ Code: Complete (20+ files, 3000+ lines)
- ✅ Documentation: Complete (6 comprehensive guides)
- ✅ Tests: Written and ready
- ⏳ **Testing:** Run the commands above
- ⏳ **Deployment:** Follow step 9
- ⏳ **Android:** Share documentation

**Next action: Execute the commands in this checklist!**

