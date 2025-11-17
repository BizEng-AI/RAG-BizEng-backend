# 🐛 ADMIN ROLEPLAY ISSUES - DIAGNOSIS & FIX

## 🎯 REPORTED ISSUES

1. **"Unexpected end of stream" error** in roleplay or chat
2. **404 "endpoint not found" for `/roleplay/turn`** when admin uses job_interview or client_meeting
3. **Sometimes it works, sometimes it doesn't** (intermittent)
4. **Azure TTS doesn't work well with admin**
5. **Admin stuff in general may not be well wired**

---

## 🔍 POTENTIAL ROOT CAUSES

### Issue 1: "Unexpected end of stream" 

This is a **connection reset/timeout error** from OkHttp (Android HTTP client). Possible causes:

1. **Server timeout** - Server takes too long to respond (>30s)
2. **Azure OpenAI timeout** - Azure API calls timing out
3. **Database query timeout** - Slow queries blocking response
4. **Memory/resource exhaustion** - Server running out of resources
5. **Network issues** - Fly.io or Azure connectivity problems

### Issue 2: 404 for `/roleplay/turn` (Intermittent)

This shouldn't happen if the endpoint exists. Possible causes:

1. **Session not being saved properly** - Session exists but can't be loaded
2. **Race condition** - Multiple requests interfering
3. **Router not mounted** - Roleplay router not included (but unlikely if it works sometimes)
4. **Path mismatch** - Android sending wrong path

### Issue 3: Admin-specific problems

Possible causes:

1. **Admin doesn't create ExerciseAttempt** - May cause tracking errors
2. **Admin role checks failing** - Dependency injection issues
3. **Different code path for admin** - Admin using different endpoints
4. **TTS integration missing admin user** - Not passing user to TTS endpoint

---

## 🧪 DIAGNOSTIC TESTS

### Test 1: Check server response times

```bash
# Time each endpoint
time curl https://bizeng-server.fly.dev/health
time curl https://bizeng-server.fly.dev/auth/login -X POST -H "Content-Type: application/json" -d '{"email":"yoo@gmail.com","password":"qwerty"}'
time curl https://bizeng-server.fly.dev/roleplay/scenarios -H "Authorization: Bearer <token>"
```

**Expected:** < 5 seconds for each
**If >30s:** Server timeout issue

### Test 2: Check roleplay endpoint registration

```bash
curl https://bizeng-server.fly.dev/docs
```

Look for `/roleplay/turn` in the OpenAPI docs.

### Test 3: Check Fly logs during failure

```bash
fly logs -a bizeng-server --tail
```

Do a roleplay turn and watch for:
- Timeout errors
- Azure API errors
- Database errors
- Memory warnings

### Test 4: Check session persistence

```python
# Start session
session_id = start_roleplay()

# Wait 5 minutes
time.sleep(300)

# Try to use session - does it still exist?
submit_turn(session_id, "test")
```

---

## 🔧 LIKELY FIXES

### Fix 1: Increase timeout for Azure OpenAI calls

**File: `roleplay_engine.py` or wherever Azure client is used**

```python
# Current (if no timeout set)
response = oai.chat.completions.create(
    model=model_name,
    messages=messages
)

# Fixed (with timeout)
response = oai.chat.completions.create(
    model=model_name,
    messages=messages,
    timeout=60  # 60 second timeout
)
```

### Fix 2: Add retry logic for Azure API

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def call_azure_chat(messages):
    return oai.chat.completions.create(
        model=model_name,
        messages=messages,
        timeout=60
    )
```

### Fix 3: Ensure roleplay router is mounted AFTER auth middleware

**File: `app.py`**

```python
# Make sure order is correct
app.include_router(auth.router)
app.include_router(roleplay_router)  # After auth

# NOT
app.include_router(roleplay_router)  # Before auth might cause issues
app.include_router(auth.router)
```

### Fix 4: Make admin users work with tracking

**Issue:** Admin users might not have ExerciseAttempt records created properly.

**File: `routers/tracking.py`** - Already fixed in our previous changes, but verify:

```python
def create_attempt_internal(db, user_id, exercise_type, ...):
    # Should work for ANY user_id, regardless of role
    attempt = ExerciseAttempt(user_id=user_id, ...)
```

### Fix 5: Add session validation in /turn endpoint

**File: `roleplay_api.py`**

```python
@router.post("/turn", response_model=TurnResponse)
def submit_turn(req: TurnRequest, user = Depends(get_optional_user), db = Depends(get_db)):
    try:
        # Add more detailed logging
        print(f"[roleplay/turn] Request from user: {user.id if user else 'anonymous'}", flush=True)
        print(f"[roleplay/turn] Session ID: {req.session_id}", flush=True)
        
        # Load session
        session = load_session(req.session_id)
        if not session:
            print(f"[roleplay/turn] ❌ Session not found: {req.session_id}", flush=True)
            raise HTTPException(status_code=404, detail=f"Session not found: {req.session_id}")
        
        print(f"[roleplay/turn] ✓ Session loaded, processing turn...", flush=True)
        
        # ... rest of logic
```

---

## 🚨 IMMEDIATE ACTIONS

### 1. Check Fly logs RIGHT NOW

```bash
fly logs -a bizeng-server --tail
```

Look for:
- Any errors during roleplay/turn
- Azure API timeout errors
- Session not found errors
- Memory/CPU warnings

### 2. Add comprehensive logging

The intermittent nature suggests race conditions or timeouts. Add logging to see exactly what's happening:

**Locations to add logging:**
1. `/roleplay/start` - Log session creation
2. `/roleplay/turn` - Log session loading, Azure calls, response
3. `roleplay_engine.py` - Log Azure API calls and responses
4. `roleplay_session.py` - Log session save/load operations

### 3. Test with different timeout values

Android's OkHttp might be timing out before server responds. 

**Android side** (if you have access):
```kotlin
val client = OkHttpClient.Builder()
    .readTimeout(60, TimeUnit.SECONDS)  // Increase from default 30s
    .writeTimeout(60, TimeUnit.SECONDS)
    .connectTimeout(30, TimeUnit.SECONDS)
    .build()
```

### 4. Check session storage mechanism

**File: `roleplay_session.py`**

Are sessions being saved to disk/database properly? Check:
- File permissions
- Disk space
- Session expiry logic

---

## 📋 TESTING CHECKLIST

After implementing fixes:

- [ ] Start roleplay as admin
- [ ] Submit 5 turns in a row without errors
- [ ] Wait 2 minutes, submit another turn (session persistence)
- [ ] Try different scenarios (job_interview, client_meeting)
- [ ] Check Fly logs for any errors
- [ ] Test from Android app
- [ ] Test as student user (compare behavior)
- [ ] Verify TTS works for admin

---

## 🔍 DEBUG COMMANDS

### Get session file location

```python
# In roleplay_session.py or where sessions are stored
import os
print(f"Session dir: {os.path.abspath(session_storage_path)}")
print(f"Sessions: {os.listdir(session_storage_path)}")
```

### Check if admin user has proper roles

```bash
curl https://bizeng-server.fly.dev/me \
  -H "Authorization: Bearer <admin_token>"
```

Should return:
```json
{
  "id": 12,
  "email": "yoo@gmail.com",
  "roles": ["admin"]
}
```

### Manually test roleplay flow

```bash
# 1. Login
TOKEN=$(curl -X POST https://bizeng-server.fly.dev/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"yoo@gmail.com","password":"qwerty"}' \
  | jq -r '.access_token')

# 2. Start session
SESSION=$(curl -X POST https://bizeng-server.fly.dev/roleplay/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scenario_id":"job_interview","student_name":"Test","use_rag":true}' \
  | jq -r '.session_id')

echo "Session: $SESSION"

# 3. Submit turn (this might fail)
curl -X POST https://bizeng-server.fly.dev/roleplay/turn \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION\",\"message\":\"Hello\"}"
```

Watch for:
- Where it fails
- What error message
- How long it takes

---

## 💡 HYPOTHESIS

Based on the symptoms:

**Most likely cause:** Azure OpenAI API calls are timing out or taking too long, causing:
1. Android's OkHttp to timeout (unexpected end of stream)
2. Fly.io to kill the request after 30s
3. Intermittent failures depending on Azure load

**Why admin specifically?**
- Admin might be triggering different code paths
- Admin might not have proper session setup
- Admin users doing longer conversations = more Azure calls = more timeouts

**Solution Priority:**
1. Add timeouts to Azure API calls
2. Add retry logic
3. Add comprehensive logging
4. Increase Android timeout (if possible)

---

## 🚀 NEXT STEPS

1. **Check Fly logs** - See actual errors
2. **Add timeout to Azure calls** - Prevent hanging
3. **Add detailed logging** - Track execution path
4. **Test with increased timeouts** - Confirm hypothesis
5. **Deploy and re-test** - Verify fixes work

Once we see the actual logs, we can pinpoint the exact issue and fix it properly.

---

**Status:** 🔴 Issues identified, fixes proposed  
**Next:** Check Fly logs and implement timeout fixes  
**Priority:** HIGH (blocking admin usage)

