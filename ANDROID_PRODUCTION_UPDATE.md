# 🔄 ANDROID CLIENT - PRODUCTION UPDATE GUIDE

**Date:** November 10, 2025  
**Action Required:** Point Android app to production Fly.io server

---

## 🎯 WHAT TO DO

Your server is now deployed to **Fly.io production**. Update your Android app to use the production URL instead of localhost/ngrok.

---

## 📝 STEP 1: Update Base URL in Android

### Find Your Network Module

Look for one of these files in your Android project:
- `app/src/main/java/.../di/NetworkModule.kt`
- `app/src/main/java/.../network/NetworkModule.kt`
- Or wherever you define `baseUrl` for Retrofit/Ktor

### Change the Base URL

**FROM (current - ngrok/localhost):**
```kotlin
@Provides
@Singleton
fun provideBaseUrl(): String {
    return "http://localhost:8020"
    // or "https://your-ngrok-url.ngrok-free.app"
}
```

**TO (production):**
```kotlin
@Provides
@Singleton
fun provideBaseUrl(): String {
    return "https://bizeng-server.fly.dev"
}
```

### Full Example:

```kotlin
// di/NetworkModule.kt or network/NetworkModule.kt

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideBaseUrl(): String {
        // ✅ PRODUCTION URL - Fly.io deployment
        return "https://bizeng-server.fly.dev"
        
        // For local development, use:
        // return "http://10.0.2.2:8020"  // Android emulator
        // return "http://YOUR_LOCAL_IP:8020"  // Physical device
    }

    @Provides
    @Singleton
    fun provideHttpClient(): HttpClient {
        return HttpClient(CIO) {
            install(ContentNegotiation) {
                json(Json {
                    ignoreUnknownKeys = true
                    isLenient = true
                })
            }
            install(Logging) {
                level = LogLevel.INFO
            }
            defaultRequest {
                url(provideBaseUrl())
            }
        }
    }
}
```

---

## 🧪 STEP 2: Test These 2 Endpoints from Android Device

### Test 1: RAG Search
**Endpoint:** `GET /debug/search?q=business%20meeting&k=5`

**Expected Response:**
```json
{
  "items": [
    {
      "score": 0.85,
      "src": "book_1_ocr",
      "unit": null,
      "snippet": "Business meetings typically have..."
    }
  ]
}
```

**Android Code Example:**
```kotlin
// Test in your ViewModel or Repository
suspend fun testRagSearch() {
    try {
        val response = httpClient.get("debug/search") {
            parameter("q", "business meeting")
            parameter("k", 5)
        }
        
        val data = response.body<JsonObject>()
        val items = data["items"]?.jsonArray
        
        Log.d("RAG_TEST", "✅ Found ${items?.size} results")
        Log.d("RAG_TEST", "Response: $data")
    } catch (e: Exception) {
        Log.e("RAG_TEST", "❌ Failed: ${e.message}")
    }
}
```

---

### Test 2: Chat Endpoint
**Endpoint:** `POST /chat`

**Request Body:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "How to open a meeting politely?"
    }
  ]
}
```

**Expected Response:**
```json
{
  "answer": "Opening a meeting politely is important for setting the right tone...",
  "sources": []
}
```

**Android Code Example:**
```kotlin
// Test in your ViewModel or Repository
suspend fun testChat() {
    try {
        val request = ChatReqDto(
            messages = listOf(
                ChatMsgDto(
                    role = "user",
                    content = "How to open a meeting politely?"
                )
            )
        )
        
        val response = httpClient.post("chat") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        
        val data = response.body<ChatRespDto>()
        
        Log.d("CHAT_TEST", "✅ Answer length: ${data.answer?.length} chars")
        Log.d("CHAT_TEST", "Answer: ${data.answer?.take(100)}...")
    } catch (e: Exception) {
        Log.e("CHAT_TEST", "❌ Failed: ${e.message}")
    }
}
```

---

## 🔍 STEP 3: Verify in Android Studio Logcat

After making the calls, check Logcat for these logs:

### Expected Success Logs:
```
D/RAG_TEST: ✅ Found 5 results
D/RAG_TEST: Response: {"items":[{"score":0.85,...}]}

D/CHAT_TEST: ✅ Answer length: 350 chars
D/CHAT_TEST: Answer: Opening a meeting politely is important for setting...
```

### If You See Errors:

**Error: "Connection refused"**
- ✅ Check: Are you using `https://` (not `http://`)?
- ✅ Check: Is device connected to internet?
- ✅ Check: Did you rebuild the app after changing URL?

**Error: "SSL Handshake failed"**
- ✅ Add to `AndroidManifest.xml`: `android:usesCleartextTraffic="false"`
- ✅ Ensure using HTTPS URL

**Error: "Timeout"**
- ✅ Fly.io might be cold-starting (wait 30 seconds)
- ✅ Increase timeout in HttpClient config

---

## 📱 STEP 4: Full Production Test Checklist

After updating base URL, test all features:

- [ ] **Health Check:** `GET /health` returns `{"status":"nowwww"}`
- [ ] **RAG Search:** `GET /debug/search?q=business&k=5` returns results
- [ ] **Chat:** `POST /chat` with test message returns answer
- [ ] **Ask (RAG Q&A):** `POST /ask` returns answer with sources
- [ ] **Roleplay Start:** `POST /roleplay/start` creates session
- [ ] **Roleplay Turn:** `POST /roleplay/turn` returns AI response + corrections
- [ ] **Pronunciation:** `POST /pronunciation/assess` returns scores

---

## 🔧 COMPLETE NETWORK MODULE EXAMPLE

Here's a complete, production-ready NetworkModule:

```kotlin
package com.example.bizeng.di

import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import io.ktor.client.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.plugins.logging.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.serialization.json.Json
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    private const val PRODUCTION_URL = "https://bizeng-server.fly.dev"
    private const val DEVELOPMENT_URL = "http://10.0.2.2:8020" // Emulator localhost
    
    @Provides
    @Singleton
    fun provideBaseUrl(): String {
        // Toggle for development vs production
        val isProduction = true  // Set to false for local development
        
        return if (isProduction) {
            PRODUCTION_URL
        } else {
            DEVELOPMENT_URL
        }
    }

    @Provides
    @Singleton
    fun provideJson(): Json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
    }

    @Provides
    @Singleton
    fun provideHttpClient(json: Json): HttpClient {
        return HttpClient(CIO) {
            install(ContentNegotiation) {
                json(json)
            }
            
            install(Logging) {
                logger = Logger.ANDROID
                level = LogLevel.INFO
            }
            
            install(HttpTimeout) {
                requestTimeoutMillis = 30_000  // 30 seconds
                connectTimeoutMillis = 10_000   // 10 seconds
                socketTimeoutMillis = 30_000    // 30 seconds
            }
            
            defaultRequest {
                url(provideBaseUrl())
            }
        }
    }
}
```

---

## 🎯 EXPECTED BEHAVIOR

### Before (Localhost/Ngrok):
```
❌ App only works when server running locally
❌ Need to restart ngrok every 2 hours
❌ Different URL every time
```

### After (Production):
```
✅ App works from anywhere with internet
✅ Stable URL: https://bizeng-server.fly.dev
✅ No need to manage local server
✅ Same backend as local (same Qdrant Cloud data)
```

---

## 🚨 IMPORTANT NOTES

### 1. Rebuild the App
After changing base URL, you MUST rebuild:
```bash
./gradlew clean
./gradlew assembleDebug  # or assembleRelease
```

### 2. Current Data State
The production server has **550 vectors** (same as local):
- ✅ Enough for testing all features
- ⚠️ Only 15% of full dataset
- ✅ RAG will work (with limited knowledge)

### 3. Production URL Features
- ✅ HTTPS (secure)
- ✅ Always available (Fly.io hosting)
- ✅ Connected to Qdrant Cloud (same data)
- ✅ Azure OpenAI (Sweden Central + UAE North)
- ✅ Azure Speech (East Asia)

---

## 🔄 SWITCHING BETWEEN DEV AND PROD

For easy switching, use BuildConfig:

```kotlin
// build.gradle.kts (app level)
android {
    buildTypes {
        debug {
            buildConfigField("String", "BASE_URL", "\"http://10.0.2.2:8020\"")
        }
        release {
            buildConfigField("String", "BASE_URL", "\"https://bizeng-server.fly.dev\"")
        }
    }
}

// NetworkModule.kt
@Provides
@Singleton
fun provideBaseUrl(): String {
    return BuildConfig.BASE_URL
}
```

Now:
- `./gradlew assembleDebug` → Uses localhost
- `./gradlew assembleRelease` → Uses production

---

## ✅ QUICK START SUMMARY

**1. Update base URL:**
```kotlin
return "https://bizeng-server.fly.dev"
```

**2. Rebuild app:**
```bash
./gradlew clean assembleDebug
```

**3. Test 2 endpoints:**
- RAG Search: `GET /debug/search?q=business%20meeting&k=5`
- Chat: `POST /chat` with test message

**4. Check logs:**
```
✅ RAG_TEST: Found 5 results
✅ CHAT_TEST: Answer length: 350 chars
```

---

## 🎉 RESULT

After these changes:
- ✅ Android app connects to production server
- ✅ No more localhost/ngrok dependency
- ✅ Works from any device with internet
- ✅ Same functionality as local testing
- ✅ Ready for APK distribution

---

**Status:** Configuration instructions ready  
**Action Required:** Update NetworkModule.kt and rebuild  
**Expected Time:** 5 minutes  
**Test Commands:** 2 endpoints (search + chat)

