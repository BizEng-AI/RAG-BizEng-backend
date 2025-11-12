# 📱 ANDROID AUTH INTEGRATION - COMPLETE GUIDE

**Date:** November 11, 2025  
**For:** Android Development Team  
**Server:** https://bizeng-server.fly.dev

---

## 🎯 OVERVIEW

Integrate JWT authentication, student tracking, and admin features into Android app.

**What You'll Build:**
- Login/Register screens
- Secure token storage (EncryptedSharedPreferences)
- Automatic token refresh on 401
- Exercise attempt tracking (automatic)
- Activity event logging
- Profile screen
- Admin dashboard (optional)

---

## 📦 STEP 1: ADD DEPENDENCIES

### app/build.gradle.kts
```kotlin
dependencies {
    // Existing dependencies...
    
    // Secure storage for tokens
    implementation("androidx.security:security-crypto:1.1.0-alpha06")
    
    // Ktor (if using) - already have
    implementation("io.ktor:ktor-client-core:2.3.0")
    implementation("io.ktor:ktor-client-cio:2.3.0")
    implementation("io.ktor:ktor-client-auth:2.3.0")
    implementation("io.ktor:ktor-client-content-negotiation:2.3.0")
    implementation("io.ktor:ktor-serialization-kotlinx-json:2.3.0")
    
    // Jetpack Compose Navigation (if needed)
    implementation("androidx.navigation:navigation-compose:2.7.5")
}
```

---

## 📋 STEP 2: CREATE DTOs

### data/remote/dto/AuthDtos.kt
```kotlin
package com.example.bizeng.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// Registration
@Serializable
data class RegisterReq(
    val email: String,
    val password: String,
    @SerialName("display_name") val displayName: String,
    @SerialName("group_number") val groupNumber: String? = null
)

// Login
@Serializable
data class LoginReq(
    val email: String,
    val password: String
)

// Token response
@Serializable
data class TokenResponse(
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String,
    @SerialName("token_type") val tokenType: String = "bearer"
)

// Refresh request
@Serializable
data class RefreshReq(
    @SerialName("refresh_token") val refreshToken: String
)

// Profile
@Serializable
data class ProfileDto(
    val id: Int,
    val email: String,
    @SerialName("display_name") val displayName: String?,
    @SerialName("group_number") val groupNumber: String?,
    val roles: List<String>,
    @SerialName("created_at") val createdAt: String
)

// Exercise tracking
@Serializable
data class ExerciseAttemptReq(
    @SerialName("exercise_type") val exerciseType: String,  // "chat", "roleplay", "pronunciation", "rag_qa"
    @SerialName("exercise_id") val exerciseId: String? = null,
    @SerialName("extra_metadata") val extraMetadata: Map<String, String>? = null
)

@Serializable
data class ExerciseAttemptUpdate(
    @SerialName("duration_seconds") val durationSeconds: Int? = null,
    val score: Float? = null,  // 0.0 - 1.0
    val passed: Boolean? = null,
    @SerialName("extra_metadata") val extraMetadata: Map<String, String>? = null
)

@Serializable
data class ExerciseAttemptDto(
    val id: Int,
    @SerialName("user_id") val userId: Int,
    @SerialName("exercise_type") val exerciseType: String,
    @SerialName("exercise_id") val exerciseId: String?,
    @SerialName("started_at") val startedAt: String,
    @SerialName("finished_at") val finishedAt: String?,
    @SerialName("duration_seconds") val durationSeconds: Int?,
    val score: Float?,
    val passed: Boolean?,
    @SerialName("extra_metadata") val extraMetadata: Map<String, String>?
)

// Activity events
@Serializable
data class ActivityEventReq(
    @SerialName("event_type") val eventType: String,  // "opened_chat", "started_roleplay"
    val feature: String,  // "chat", "roleplay", "pronunciation"
    @SerialName("extra_metadata") val extraMetadata: Map<String, String>? = null
)

@Serializable
data class ActivityEventDto(
    val id: Int,
    @SerialName("user_id") val userId: Int,
    @SerialName("event_type") val eventType: String,
    val feature: String,
    val timestamp: String,
    @SerialName("extra_metadata") val extraMetadata: Map<String, String>?
)
```

---

## 🔐 STEP 3: IMPLEMENT AUTH MANAGER

### data/local/AuthManager.kt
```kotlin
package com.example.bizeng.data.local

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class AuthManager(context: Context) {
    
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()
    
    private val prefs: SharedPreferences = EncryptedSharedPreferences.create(
        context,
        "auth_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )
    
    companion object {
        private const val KEY_ACCESS_TOKEN = "access_token"
        private const val KEY_REFRESH_TOKEN = "refresh_token"
        private const val KEY_USER_EMAIL = "user_email"
        private const val KEY_USER_ID = "user_id"
        private const val KEY_IS_ADMIN = "is_admin"
    }
    
    fun saveTokens(accessToken: String, refreshToken: String) {
        prefs.edit()
            .putString(KEY_ACCESS_TOKEN, accessToken)
            .putString(KEY_REFRESH_TOKEN, refreshToken)
            .apply()
    }
    
    fun getAccessToken(): String? {
        return prefs.getString(KEY_ACCESS_TOKEN, null)
    }
    
    fun getRefreshToken(): String? {
        return prefs.getString(KEY_REFRESH_TOKEN, null)
    }
    
    fun saveUserInfo(userId: Int, email: String, isAdmin: Boolean) {
        prefs.edit()
            .putInt(KEY_USER_ID, userId)
            .putString(KEY_USER_EMAIL, email)
            .putBoolean(KEY_IS_ADMIN, isAdmin)
            .apply()
    }
    
    fun getUserId(): Int {
        return prefs.getInt(KEY_USER_ID, -1)
    }
    
    fun getUserEmail(): String? {
        return prefs.getString(KEY_USER_EMAIL, null)
    }
    
    fun isAdmin(): Boolean {
        return prefs.getBoolean(KEY_IS_ADMIN, false)
    }
    
    fun isLoggedIn(): Boolean {
        return getAccessToken() != null && getRefreshToken() != null
    }
    
    fun clearTokens() {
        prefs.edit().clear().apply()
    }
}
```

---

## 🌐 STEP 4: CREATE AUTH API

### data/remote/api/AuthApi.kt
```kotlin
package com.example.bizeng.data.remote.api

import com.example.bizeng.data.remote.dto.*
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.request.*
import io.ktor.http.*

class AuthApi(
    private val client: HttpClient,
    private val baseUrl: String
) {
    
    suspend fun register(request: RegisterReq): TokenResponse {
        return client.post("$baseUrl/auth/register") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.body()
    }
    
    suspend fun login(request: LoginReq): TokenResponse {
        return client.post("$baseUrl/auth/login") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.body()
    }
    
    suspend fun refresh(refreshToken: String): TokenResponse {
        return client.post("$baseUrl/auth/refresh") {
            contentType(ContentType.Application.Json)
            setBody(RefreshReq(refreshToken))
        }.body()
    }
    
    suspend fun logout(refreshToken: String) {
        client.post("$baseUrl/auth/logout") {
            contentType(ContentType.Application.Json)
            setBody(RefreshReq(refreshToken))
        }
    }
    
    suspend fun getProfile(): ProfileDto {
        return client.get("$baseUrl/me").body()
    }
}
```

### data/remote/api/TrackingApi.kt
```kotlin
package com.example.bizeng.data.remote.api

import com.example.bizeng.data.remote.dto.*
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.request.*
import io.ktor.http.*

class TrackingApi(
    private val client: HttpClient,
    private val baseUrl: String
) {
    
    suspend fun startAttempt(request: ExerciseAttemptReq): ExerciseAttemptDto {
        return client.post("$baseUrl/tracking/attempts") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.body()
    }
    
    suspend fun finishAttempt(id: Int, update: ExerciseAttemptUpdate): ExerciseAttemptDto {
        return client.patch("$baseUrl/tracking/attempts/$id") {
            contentType(ContentType.Application.Json)
            setBody(update)
        }.body()
    }
    
    suspend fun logEvent(request: ActivityEventReq): ActivityEventDto {
        return client.post("$baseUrl/tracking/events") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.body()
    }
    
    suspend fun getMyAttempts(): List<ExerciseAttemptDto> {
        return client.get("$baseUrl/tracking/my-attempts").body()
    }
}
```

---

## 🔄 STEP 5: ADD AUTH INTERCEPTOR

### di/NetworkModule.kt (update)
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    
    @Provides
    @Singleton
    fun provideHttpClient(
        authManager: AuthManager,
        authApi: AuthApi
    ): HttpClient {
        return HttpClient(CIO) {
            install(ContentNegotiation) {
                json(Json {
                    ignoreUnknownKeys = true
                    isLenient = true
                })
            }
            
            install(Logging) {
                logger = Logger.ANDROID
                level = LogLevel.INFO
            }
            
            // Auth interceptor
            install(HttpSend) {
                maxSendCount = 3
                
                intercept { request ->
                    val originalCall = execute(request)
                    
                    if (originalCall.response.status == HttpStatusCode.Unauthorized) {
                        // Try to refresh token
                        val refreshToken = authManager.getRefreshToken()
                        if (refreshToken != null) {
                            try {
                                val newTokens = authApi.refresh(refreshToken)
                                authManager.saveTokens(
                                    newTokens.accessToken,
                                    newTokens.refreshToken
                                )
                                
                                // Retry with new token
                                execute(request.apply {
                                    headers.remove(HttpHeaders.Authorization)
                                    headers.append(
                                        HttpHeaders.Authorization,
                                        "Bearer ${newTokens.accessToken}"
                                    )
                                })
                            } catch (e: Exception) {
                                // Refresh failed, logout
                                authManager.clearTokens()
                                originalCall
                            }
                        } else {
                            originalCall
                        }
                    } else {
                        originalCall
                    }
                }
            }
            
            // Add bearer token to all requests
            defaultRequest {
                val token = authManager.getAccessToken()
                if (token != null) {
                    headers.append(HttpHeaders.Authorization, "Bearer $token")
                }
            }
        }
    }
}
```

---

## 📊 STEP 6: CREATE REPOSITORY

### data/repository/AuthRepository.kt
```kotlin
package com.example.bizeng.data.repository

import com.example.bizeng.data.local.AuthManager
import com.example.bizeng.data.remote.api.AuthApi
import com.example.bizeng.data.remote.dto.*
import javax.inject.Inject

class AuthRepository @Inject constructor(
    private val authApi: AuthApi,
    private val authManager: AuthManager
) {
    
    suspend fun register(
        email: String,
        password: String,
        displayName: String,
        groupNumber: String?
    ): Result<Unit> = runCatching {
        val response = authApi.register(
            RegisterReq(email, password, displayName, groupNumber)
        )
        authManager.saveTokens(response.accessToken, response.refreshToken)
        
        // Get profile to save user info
        val profile = authApi.getProfile()
        authManager.saveUserInfo(
            profile.id,
            profile.email,
            profile.roles.contains("admin")
        )
    }
    
    suspend fun login(email: String, password: String): Result<Unit> = runCatching {
        val response = authApi.login(LoginReq(email, password))
        authManager.saveTokens(response.accessToken, response.refreshToken)
        
        // Get profile
        val profile = authApi.getProfile()
        authManager.saveUserInfo(
            profile.id,
            profile.email,
            profile.roles.contains("admin")
        )
    }
    
    suspend fun logout(): Result<Unit> = runCatching {
        val refreshToken = authManager.getRefreshToken()
        if (refreshToken != null) {
            authApi.logout(refreshToken)
        }
        authManager.clearTokens()
    }
    
    suspend fun getProfile(): Result<ProfileDto> = runCatching {
        authApi.getProfile()
    }
    
    fun isLoggedIn(): Boolean = authManager.isLoggedIn()
    
    fun isAdmin(): Boolean = authManager.isAdmin()
}
```

### data/repository/TrackingRepository.kt
```kotlin
package com.example.bizeng.data.repository

import com.example.bizeng.data.remote.api.TrackingApi
import com.example.bizeng.data.remote.dto.*
import javax.inject.Inject

class TrackingRepository @Inject constructor(
    private val trackingApi: TrackingApi
) {
    
    suspend fun startExercise(
        type: String,
        exerciseId: String? = null,
        metadata: Map<String, String>? = null
    ): Result<ExerciseAttemptDto> = runCatching {
        trackingApi.startAttempt(
            ExerciseAttemptReq(type, exerciseId, metadata)
        )
    }
    
    suspend fun finishExercise(
        attemptId: Int,
        durationSeconds: Int,
        score: Float? = null,
        passed: Boolean? = null,
        metadata: Map<String, String>? = null
    ): Result<ExerciseAttemptDto> = runCatching {
        trackingApi.finishAttempt(
            attemptId,
            ExerciseAttemptUpdate(durationSeconds, score, passed, metadata)
        )
    }
    
    suspend fun logActivity(
        eventType: String,
        feature: String,
        metadata: Map<String, String>? = null
    ): Result<Unit> = runCatching {
        trackingApi.logEvent(
            ActivityEventReq(eventType, feature, metadata)
        )
    }
    
    suspend fun getMyHistory(): Result<List<ExerciseAttemptDto>> = runCatching {
        trackingApi.getMyAttempts()
    }
}
```

---

## 🎨 STEP 7: CREATE UI SCREENS

### ui/auth/LoginScreen.kt
```kotlin
@Composable
fun LoginScreen(
    onLoginSuccess: () -> Unit,
    onNavigateToRegister: () -> Unit,
    viewModel: AuthViewModel = hiltViewModel()
) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    val uiState by viewModel.uiState.collectAsState()
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text("Login", style = MaterialTheme.typography.headlineLarge)
        
        Spacer(modifier = Modifier.height(32.dp))
        
        OutlinedTextField(
            value = email,
            onValueChange = { email = it },
            label = { Text("Email") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
            modifier = Modifier.fillMaxWidth()
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text("Password") },
            visualTransformation = PasswordVisualTransformation(),
            modifier = Modifier.fillMaxWidth()
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Button(
            onClick = {
                viewModel.login(email, password) { success ->
                    if (success) onLoginSuccess()
                }
            },
            modifier = Modifier.fillMaxWidth(),
            enabled = uiState !is AuthUiState.Loading
        ) {
            if (uiState is AuthUiState.Loading) {
                CircularProgressIndicator(modifier = Modifier.size(24.dp))
            } else {
                Text("Login")
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        TextButton(onClick = onNavigateToRegister) {
            Text("Don't have an account? Register")
        }
        
        if (uiState is AuthUiState.Error) {
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = (uiState as AuthUiState.Error).message,
                color = MaterialTheme.colorScheme.error
            )
        }
    }
}
```

---

## 🔍 STEP 8: AUTOMATIC TRACKING

### Wrap Exercise Screens

```kotlin
@Composable
fun RoleplayScreen(viewModel: RoleplayViewModel = hiltViewModel()) {
    val trackingRepo: TrackingRepository = hiltViewModel()
    val attemptId = remember { mutableStateOf<Int?>(null) }
    
    LaunchedEffect(Unit) {
        // Log activity event
        trackingRepo.logActivity("opened_roleplay", "roleplay")
        
        // Start attempt tracking
        trackingRepo.startExercise("roleplay", null).onSuccess {
            attemptId.value = it.id
        }
    }
    
    DisposableEffect(Unit) {
        val startTime = System.currentTimeMillis()
        onDispose {
            // Finish attempt when leaving screen
            attemptId.value?.let { id ->
                val durationSec = ((System.currentTimeMillis() - startTime) / 1000).toInt()
                lifecycleScope.launch {
                    trackingRepo.finishExercise(id, durationSec)
                }
            }
        }
    }
    
    // Rest of roleplay UI...
}
```

---

## ✅ TESTING CHECKLIST

- [ ] Login screen shows and accepts credentials
- [ ] Register screen creates new account
- [ ] Tokens saved to EncryptedSharedPreferences
- [ ] Profile screen shows user info
- [ ] Token auto-refresh on 401
- [ ] Exercise tracking logs attempts
- [ ] Activity events logged for each feature
- [ ] Logout clears tokens
- [ ] Admin features show only for admin users

---

## 🚀 DEPLOYMENT

1. Update `BASE_URL` to production: `https://bizeng-server.fly.dev`
2. Test all auth flows
3. Verify tracking is working
4. Build release APK
5. Test on physical devices

---

**Status:** ✅ Ready for implementation  
**Estimated Time:** 2-3 days for full integration  
**Priority:** High - Required for admin analytics

