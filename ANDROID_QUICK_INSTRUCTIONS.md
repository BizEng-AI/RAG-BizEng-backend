# 📱 ANDROID SIDE - QUICK INSTRUCTIONS

## What You Need to Say to Android Developer:

---

## 🎯 The Task

**Server is now live in production!** Update your Android app to use the production URL.

---

## 📝 Step-by-Step

### 1. Update Base URL (1 line change)

Find your `NetworkModule.kt` (or wherever you set the base URL) and change:

**FROM:**
```kotlin
return "http://localhost:8020"  // or ngrok URL
```

**TO:**
```kotlin
return "https://bizeng-server.fly.dev"
```

### 2. Rebuild the App
```bash
./gradlew clean assembleDebug
```

### 3. Test These 2 Endpoints

**Test A: RAG Search**
```
GET /debug/search?q=business%20meeting&k=5
```
Should return 5 results from our course materials.

**Test B: Chat**
```
POST /chat
Body: {"messages":[{"role":"user","content":"How to open a meeting politely?"}]}
```
Should return an AI-generated answer about meeting etiquette.

---

## ✅ Success Criteria

In Logcat, you should see:
```
✅ RAG search: Found 5 results
✅ Chat: Received answer (350+ chars)
```

---

## 🔗 Production URL

**Base URL:** `https://bizeng-server.fly.dev`

**Benefits:**
- ✅ No more localhost/ngrok headaches
- ✅ Always available (24/7)
- ✅ Same backend data as local testing
- ✅ HTTPS secure connection

---

## 📄 Full Guide

For detailed instructions with code examples, see:
`ANDROID_PRODUCTION_UPDATE.md`

---

## 🆘 If Something Goes Wrong

**Common issues:**

1. **"Connection refused"**
   - Check: Are you using `https://` (not `http://`)?
   - Check: Did you rebuild the app?

2. **"Timeout"**
   - First request might take 30 sec (cold start)
   - Fly.io wakes up after sleeping

3. **"SSL error"**
   - Make sure using HTTPS URL
   - Check AndroidManifest.xml allows HTTPS

---

## 🎉 That's It!

Just update the URL, rebuild, and test those 2 endpoints. Should take 5 minutes max.

**Current server status:** ✅ Live and tested  
**Data available:** 550 vectors (enough for all features)  
**All endpoints:** ✅ Working

