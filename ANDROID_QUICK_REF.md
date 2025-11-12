# 📱 ANDROID QUICK REFERENCE

**Server:** ✅ Production Ready  
**Base URL:** `https://bizeng-server.fly.dev`

---

## ⚠️ CRITICAL CHANGE

**Field renamed:** `metadata` → `extra_metadata`

Update all DTOs:
```kotlin
@SerialName("extra_metadata") val extraMetadata: Map<String, String>?
```

---

## 🔑 ESSENTIAL ENDPOINTS

### Auth
```kotlin
POST /auth/register
POST /auth/login
POST /auth/refresh
GET /me
```

### Tracking (⚠️ Use extra_metadata)
```kotlin
POST /tracking/attempts         // Start exercise
PATCH /tracking/attempts/{id}   // Finish exercise
POST /tracking/events           // Log activity
```

### Existing Features
```kotlin
POST /chat
POST /ask
POST /roleplay/start
POST /roleplay/turn
POST /pronunciation/assess
```

---

## 📦 KEY DEPENDENCIES

```kotlin
// Security
implementation("androidx.security:security-crypto:1.1.0-alpha06")

// Networking (Ktor or Retrofit)
implementation("io.ktor:ktor-client-core:2.3.7")
implementation("io.ktor:ktor-client-auth:2.3.7")
```

---

## 🔐 AUTH FLOW

1. **Register/Login** → Get tokens
2. **Save tokens** → EncryptedSharedPreferences
3. **Add Bearer token** → All API calls
4. **Auto-refresh** → On 401 error
5. **Logout** → Clear tokens

---

## 📊 TRACKING PATTERN

```kotlin
// On screen enter
LaunchedEffect(Unit) {
    trackingRepo.logActivity("opened_X", "X")
    val attempt = trackingRepo.startExercise("X")
    attemptId = attempt.id
}

// On screen exit
DisposableEffect(Unit) {
    onDispose {
        trackingRepo.finishExercise(
            attemptId = attemptId,
            durationSeconds = calculateDuration(),
            score = finalScore,
            extraMetadata = mapOf("key" to "value")  // ⚠️
        )
    }
}
```

---

## 🎯 IMPLEMENTATION PRIORITY

**Day 1:**
- [ ] AuthManager (token storage)
- [ ] Login/Register screens
- [ ] Test authentication flow

**Day 2:**
- [ ] TrackingRepository
- [ ] Wrap existing screens with tracking
- [ ] Test tracking works

**Day 3:**
- [ ] Profile screen
- [ ] Admin dashboard (if needed)
- [ ] Polish & test

---

## 📚 FULL DOCS

See `ANDROID_COMPLETE_GUIDE.md` for:
- Complete DTOs
- Full code examples
- All API endpoints
- Testing checklist

---

**Status:** Backend ready, Android can start! 🚀

