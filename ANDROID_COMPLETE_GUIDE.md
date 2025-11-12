1. ✅ Authentication (Login/Register) - Day 1
2. ✅ Token storage & refresh - Day 1
3. ✅ Exercise tracking - Day 2
4. ✅ Existing features integration - Day 2-3
5. ⏳ Admin dashboard (Optional) - Day 3+

**Critical Updates:**
- ⚠️ Use `extra_metadata` instead of `metadata` in all DTOs
- ⚠️ All tracking is automatic via LaunchedEffect/DisposableEffect
- ⚠️ NO content stored - only scores, duration, timestamps

---

**Status:** ✅ **SERVER READY - ANDROID CAN START INTEGRATION**

**Server URL:** `https://bizeng-server.fly.dev` (after deployment)  
**Local URL:** `http://localhost:8020` (for development)

**Questions?** Check `AUTH_SYSTEM_COMPLETE.md` on server for detailed API docs!
# 📱 ANDROID CLIENT - COMPLETE INTEGRATION GUIDE (UPDATED)

**Date:** November 11, 2025  
**Server Status:** ✅ Production Ready (All tests passed)  
**Base URL Production:** `https://bizeng-server.fly.dev`  
**Base URL Local:** `http://localhost:8020`

---

## 🎯 CRITICAL UPDATES FROM SERVER

### ⚠️ BREAKING CHANGE: Field Name Changed

**OLD (Don't use):** `metadata`  
**NEW (Use this):** `extra_metadata`

This affects:
- Exercise attempt tracking
- Activity event logging
- All responses containing these fields

---

## 📦 STEP 1: ADD DEPENDENCIES

### app/build.gradle.kts

```kotlin
dependencies {
    // Existing dependencies...
    
    // Security & Authentication
    implementation("androidx.security:security-crypto:1.1.0-alpha06")
    
    // Networking (if using Ktor)
    implementation("io.ktor:ktor-client-core:2.3.7")
    implementation("io.ktor:ktor-client-cio:2.3.7")
    implementation("io.ktor:ktor-client-auth:2.3.7")
    implementation("io.ktor:ktor-client-content-negotiation:2.3.7")
    implementation("io.ktor:ktor-serialization-kotlinx-json:2.3.7")
    implementation("io.ktor:ktor-client-logging:2.3.7")
    
    // Or if using Retrofit
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.11.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.11.0")
    
    // Coroutines (if not already added)
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    
    // Jetpack Compose Navigation
    implementation("androidx.navigation:navigation-compose:2.7.5")
}
```

---

## 📋 STEP 2: CREATE DTOs (DATA CLASSES)

### data/remote/dto/AuthDtos.kt

```kotlin
package com.example.bizeng.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ============================================================================
// AUTHENTICATION DTOs
// ============================================================================

@Serializable
data class RegisterReq(
    val email: String,
    val password: String,
    @SerialName("display_name") val displayName: String,
    @SerialName("group_number") val groupNumber: String? = null
)

@Serializable
data class LoginReq(
    val email: String,
    val password: String
)

@Serializable
data class TokenResponse(
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String,
    @SerialName("token_type") val tokenType: String = "bearer"
)

@Serializable
data class RefreshReq(
    @SerialName("refresh_token") val refreshToken: String
)

@Serializable
data class ProfileDto(
    val id: Int,
    val email: String,
    @SerialName("display_name") val displayName: String?,
    @SerialName("group_number") val groupNumber: String?,
    val roles: List<String>,
    @SerialName("created_at") val createdAt: String
)

// ============================================================================
// EXERCISE TRACKING DTOs (⚠️ UPDATED - uses extra_metadata)
// ============================================================================

@Serializable
data class ExerciseAttemptReq(
    @SerialName("exercise_type") val exerciseType: String,  // "chat", "roleplay", "pronunciation", "rag_qa"
    @SerialName("exercise_id") val exerciseId: String? = null,
    @SerialName("extra_metadata") val extraMetadata: Map<String, String>? = null  // ⚠️ CHANGED from metadata
)

@Serializable
data class ExerciseAttemptUpdate(
    @SerialName("duration_seconds") val durationSeconds: Int? = null,
    val score: Float? = null,  // 0.0 - 1.0
    val passed: Boolean? = null,
    @SerialName("extra_metadata") val extraMetadata: Map<String, String>? = null  // ⚠️ CHANGED from metadata
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
    @SerialName("extra_metadata") val extraMetadata: Map<String, String>?  // ⚠️ CHANGED from metadata
)

// ============================================================================
// ACTIVITY EVENT DTOs (⚠️ UPDATED - uses extra_metadata)
// ============================================================================

@Serializable
data class ActivityEventReq(
    @SerialName("event_type") val eventType: String,  // "opened_chat", "started_roleplay"
    val feature: String,  // "chat", "roleplay", "pronunciation", "rag_qa"
    @SerialName("extra_metadata") val extraMetadata: Map<String, String>? = null  // ⚠️ CHANGED from metadata
)

@Serializable
data class ActivityEventDto(
    val id: Int,
    @SerialName("user_id") val userId: Int,
    @SerialName("event_type") val eventType: String,
    val feature: String,
    val timestamp: String,
    @SerialName("extra_metadata") val extraMetadata: Map<String, String>?  // ⚠️ CHANGED from metadata
)

// ============================================================================
// ADMIN DTOs (Teacher/Admin only)
// ============================================================================

@Serializable
data class StudentSummaryDto(
    @SerialName("student_id") val studentId: Int,
    val email: String,
    @SerialName("display_name") val displayName: String?,
    @SerialName("group_number") val groupNumber: String?,
    @SerialName("total_attempts") val totalAttempts: Int,
    @SerialName("completed_attempts") val completedAttempts: Int,
    @SerialName("avg_score") val avgScore: Float?,
    @SerialName("total_minutes") val totalMinutes: Int,
    @SerialName("features_used") val featuresUsed: Map<String, Int>,
    @SerialName("last_active") val lastActive: String?
)

@Serializable
data class AdminDashboardDto(
    @SerialName("total_students") val totalStudents: Int,
    @SerialName("active_students_7d") val activeStudents7d: Int,
    @SerialName("total_attempts") val totalAttempts: Int,
    @SerialName("avg_completion_rate") val avgCompletionRate: Float,
    @SerialName("popular_features") val popularFeatures: Map<String, Int>
)
```

---

## 🔐 STEP 3: CREATE AUTH MANAGER

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
        private const val KEY_USER_NAME = "user_name"
        private const val KEY_IS_ADMIN = "is_admin"
    }
    
    fun saveTokens(accessToken: String, refreshToken: String) {
        prefs.edit()
            .putString(KEY_ACCESS_TOKEN, accessToken)
            .putString(KEY_REFRESH_TOKEN, refreshToken)
            .apply()
    }
    
    fun saveUserInfo(userId: Int, email: String, displayName: String?, isAdmin: Boolean) {
        prefs.edit()
            .putInt(KEY_USER_ID, userId)
            .putString(KEY_USER_EMAIL, email)
            .putString(KEY_USER_NAME, displayName)
            .putBoolean(KEY_IS_ADMIN, isAdmin)
            .apply()
    }
    
    fun getAccessToken(): String? = prefs.getString(KEY_ACCESS_TOKEN, null)
    
    fun getRefreshToken(): String? = prefs.getString(KEY_REFRESH_TOKEN, null)
    
    fun getUserId(): Int = prefs.getInt(KEY_USER_ID, -1)
    
    fun getUserEmail(): String? = prefs.getString(KEY_USER_EMAIL, null)
    
    fun getUserName(): String? = prefs.getString(KEY_USER_NAME, null)
    
    fun isAdmin(): Boolean = prefs.getBoolean(KEY_IS_ADMIN, false)
    
    fun isLoggedIn(): Boolean {
        return getAccessToken() != null && getRefreshToken() != null
    }
    
    fun clearTokens() {
        prefs.edit().clear().apply()
    }
}
```

---

## 🌐 STEP 4: CREATE API SERVICES

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

### data/remote/api/AdminApi.kt

```kotlin
package com.example.bizeng.data.remote.api

import com.example.bizeng.data.remote.dto.*
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.request.*

class AdminApi(
    private val client: HttpClient,
    private val baseUrl: String
) {
    
    suspend fun getDashboard(): AdminDashboardDto {
        return client.get("$baseUrl/admin/dashboard").body()
    }
    
    suspend fun getStudentSummary(studentId: Int): StudentSummaryDto {
        return client.get("$baseUrl/admin/students/$studentId").body()
    }
    
    suspend fun getStudentAttempts(studentId: Int, limit: Int = 50): List<ExerciseAttemptDto> {
        return client.get("$baseUrl/admin/students/$studentId/attempts") {
            parameter("limit", limit)
        }.body()
    }
}
```

---

## 🔄 STEP 5: CREATE AUTH INTERCEPTOR

### di/NetworkModule.kt

```kotlin
package com.example.bizeng.di

import android.content.Context
import com.example.bizeng.data.local.AuthManager
import com.example.bizeng.data.remote.api.*
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import io.ktor.client.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.plugins.logging.*
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.serialization.json.Json
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    
    @Provides
    @Singleton
    fun provideBaseUrl(): String {
        // Change this for production
        val USE_PRODUCTION = false
        return if (USE_PRODUCTION) {
            "https://bizeng-server.fly.dev"
        } else {
            "http://10.0.2.2:8020"  // Android emulator localhost
            // For physical device, use: "http://YOUR_COMPUTER_IP:8020"
        }
    }
    
    @Provides
    @Singleton
    fun provideAuthManager(@ApplicationContext context: Context): AuthManager {
        return AuthManager(context)
    }
    
    @Provides
    @Singleton
    fun provideHttpClient(
        authManager: AuthManager,
        baseUrl: String
    ): HttpClient {
        return HttpClient(CIO) {
            install(ContentNegotiation) {
                json(Json {
                    ignoreUnknownKeys = true
                    isLenient = true
                    prettyPrint = true
                })
            }
            
            install(Logging) {
                logger = Logger.ANDROID
                level = LogLevel.INFO
            }
            
            install(HttpTimeout) {
                requestTimeoutMillis = 30000
                connectTimeoutMillis = 30000
            }
            
            // Default headers
            defaultRequest {
                val token = authManager.getAccessToken()
                if (token != null) {
                    headers.append(HttpHeaders.Authorization, "Bearer $token")
                }
                contentType(ContentType.Application.Json)
            }
            
            // Auto-retry on 401 with token refresh
            install(HttpSend) {
                maxSendCount = 3
                
                intercept { request ->
                    val originalCall = execute(request)
                    
                    if (originalCall.response.status == HttpStatusCode.Unauthorized) {
                        // Try to refresh token
                        val refreshToken = authManager.getRefreshToken()
                        if (refreshToken != null) {
                            try {
                                // Create temporary client for refresh (no auth header)
                                val refreshClient = HttpClient(CIO) {
                                    install(ContentNegotiation) {
                                        json(Json { ignoreUnknownKeys = true })
                                    }
                                }
                                
                                val refreshReq = RefreshReq(refreshToken)
                                val newTokens: TokenResponse = refreshClient.post("$baseUrl/auth/refresh") {
                                    contentType(ContentType.Application.Json)
                                    setBody(refreshReq)
                                }.body()
                                
                                refreshClient.close()
                                
                                // Save new tokens
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
                                // Refresh failed, logout user
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
        }
    }
    
    @Provides
    @Singleton
    fun provideAuthApi(client: HttpClient, baseUrl: String): AuthApi {
        return AuthApi(client, baseUrl)
    }
    
    @Provides
    @Singleton
    fun provideTrackingApi(client: HttpClient, baseUrl: String): TrackingApi {
        return TrackingApi(client, baseUrl)
    }
    
    @Provides
    @Singleton
    fun provideAdminApi(client: HttpClient, baseUrl: String): AdminApi {
        return AdminApi(client, baseUrl)
    }
}
```

---

## 📊 STEP 6: CREATE REPOSITORIES

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
            profile.displayName,
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
            profile.displayName,
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
    
    /**
     * Start tracking an exercise attempt
     * Call this when user begins an exercise
     */
    suspend fun startExercise(
        type: String,  // "chat", "roleplay", "pronunciation", "rag_qa"
        exerciseId: String? = null,
        extraMetadata: Map<String, String>? = null  // ⚠️ CHANGED from metadata
    ): Result<ExerciseAttemptDto> = runCatching {
        trackingApi.startAttempt(
            ExerciseAttemptReq(type, exerciseId, extraMetadata)
        )
    }
    
    /**
     * Finish tracking an exercise attempt
     * Call this when user completes or exits an exercise
     */
    suspend fun finishExercise(
        attemptId: Int,
        durationSeconds: Int,
        score: Float? = null,
        passed: Boolean? = null,
        extraMetadata: Map<String, String>? = null  // ⚠️ CHANGED from metadata
    ): Result<ExerciseAttemptDto> = runCatching {
        trackingApi.finishAttempt(
            attemptId,
            ExerciseAttemptUpdate(durationSeconds, score, passed, extraMetadata)
        )
    }
    
    /**
     * Log an activity event (lightweight tracking)
     * Call this when user opens a feature or takes an action
     */
    suspend fun logActivity(
        eventType: String,  // "opened_chat", "started_roleplay", etc.
        feature: String,  // "chat", "roleplay", "pronunciation"
        extraMetadata: Map<String, String>? = null  // ⚠️ CHANGED from metadata
    ): Result<Unit> = runCatching {
        trackingApi.logEvent(
            ActivityEventReq(eventType, feature, extraMetadata)
        )
    }
    
    suspend fun getMyHistory(): Result<List<ExerciseAttemptDto>> = runCatching {
        trackingApi.getMyAttempts()
    }
}
```

---

## 🎨 STEP 7: CREATE VIEW MODELS

### ui/auth/AuthViewModel.kt

```kotlin
package com.example.bizeng.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.bizeng.data.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class AuthUiState {
    object Idle : AuthUiState()
    object Loading : AuthUiState()
    object Success : AuthUiState()
    data class Error(val message: String) : AuthUiState()
}

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow<AuthUiState>(AuthUiState.Idle)
    val uiState: StateFlow<AuthUiState> = _uiState
    
    fun login(email: String, password: String, onSuccess: () -> Unit) {
        viewModelScope.launch {
            _uiState.value = AuthUiState.Loading
            
            authRepository.login(email, password)
                .onSuccess {
                    _uiState.value = AuthUiState.Success
                    onSuccess()
                }
                .onFailure { error ->
                    _uiState.value = AuthUiState.Error(
                        error.message ?: "Login failed"
                    )
                }
        }
    }
    
    fun register(
        email: String,
        password: String,
        displayName: String,
        groupNumber: String?,
        onSuccess: () -> Unit
    ) {
        viewModelScope.launch {
            _uiState.value = AuthUiState.Loading
            
            authRepository.register(email, password, displayName, groupNumber)
                .onSuccess {
                    _uiState.value = AuthUiState.Success
                    onSuccess()
                }
                .onFailure { error ->
                    _uiState.value = AuthUiState.Error(
                        error.message ?: "Registration failed"
                    )
                }
        }
    }
    
    fun logout(onSuccess: () -> Unit) {
        viewModelScope.launch {
            authRepository.logout()
                .onSuccess {
                    onSuccess()
                }
        }
    }
    
    fun isLoggedIn(): Boolean = authRepository.isLoggedIn()
    
    fun isAdmin(): Boolean = authRepository.isAdmin()
}
```

---

## 🎭 STEP 8: AUTOMATIC EXERCISE TRACKING

### Example: Wrapping Roleplay Screen with Tracking

```kotlin
@Composable
fun RoleplayScreen(
    viewModel: RoleplayViewModel = hiltViewModel(),
    trackingRepository: TrackingRepository = hiltViewModel()
) {
    var attemptId by remember { mutableStateOf<Int?>(null) }
    val startTime = remember { System.currentTimeMillis() }
    
    // Log activity when screen opens
    LaunchedEffect(Unit) {
        // Log that user opened this feature
        trackingRepository.logActivity(
            eventType = "opened_roleplay",
            feature = "roleplay"
        )
        
        // Start tracking attempt
        trackingRepository.startExercise(
            type = "roleplay",
            exerciseId = viewModel.scenarioId,
            extraMetadata = mapOf("difficulty" to "intermediate")  // ⚠️ Use extraMetadata
        ).onSuccess {
            attemptId.value = it.id
        }
    }
    
    // Finish tracking when leaving screen
    DisposableEffect(Unit) {
        onDispose {
            attemptId.value?.let { id ->
                val durationSec = ((System.currentTimeMillis() - startTime) / 1000).toInt()
                
                viewModel.viewModelScope.launch {
                    trackingRepository.finishExercise(
                        attemptId = id,
                        durationSeconds = durationSec,
                        score = viewModel.finalScore,
                        passed = viewModel.passed,
                        extraMetadata = mapOf(  // ⚠️ Use extraMetadata
                            "corrections" to viewModel.correctionsCount.toString(),
                            "turns" to viewModel.turnCount.toString()
                        )
                    )
                }
            }
        }
    }
    
    // Rest of your roleplay UI...
}
```

---

## 📱 STEP 9: CREATE UI SCREENS

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
        Text(
            text = "BizEng Login",
            style = MaterialTheme.typography.headlineLarge
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        
        OutlinedTextField(
            value = email,
            onValueChange = { email = it },
            label = { Text("Email") },
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Email,
                imeAction = ImeAction.Next
            ),
            modifier = Modifier.fillMaxWidth(),
            singleLine = true
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text("Password") },
            visualTransformation = PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Password,
                imeAction = ImeAction.Done
            ),
            keyboardActions = KeyboardActions(
                onDone = {
                    viewModel.login(email, password, onLoginSuccess)
                }
            ),
            modifier = Modifier.fillMaxWidth(),
            singleLine = true
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Button(
            onClick = {
                viewModel.login(email, password, onLoginSuccess)
            },
            modifier = Modifier.fillMaxWidth(),
            enabled = uiState !is AuthUiState.Loading && email.isNotBlank() && password.isNotBlank()
        ) {
            if (uiState is AuthUiState.Loading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp),
                    color = MaterialTheme.colorScheme.onPrimary
                )
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
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}
```

---

## 🚀 STEP 10: UPDATE NAVIGATION

### navigation/NavGraph.kt

```kotlin
@Composable
fun NavGraph(
    navController: NavHostController,
    authViewModel: AuthViewModel = hiltViewModel()
) {
    val startDestination = if (authViewModel.isLoggedIn()) {
        "home"
    } else {
        "login"
    }
    
    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable("login") {
            LoginScreen(
                onLoginSuccess = {
                    navController.navigate("home") {
                        popUpTo("login") { inclusive = true }
                    }
                },
                onNavigateToRegister = {
                    navController.navigate("register")
                }
            )
        }
        
        composable("register") {
            RegisterScreen(
                onRegisterSuccess = {
                    navController.navigate("home") {
                        popUpTo("register") { inclusive = true }
                    }
                },
                onNavigateToLogin = {
                    navController.popBackStack()
                }
            )
        }
        
        composable("home") {
            HomeScreen(
                onLogout = {
                    authViewModel.logout {
                        navController.navigate("login") {
                            popUpTo(0) { inclusive = true }
                        }
                    }
                },
                isAdmin = authViewModel.isAdmin()
            )
        }
        
        // Add admin dashboard if user is admin
        composable("admin_dashboard") {
            if (authViewModel.isAdmin()) {
                AdminDashboardScreen()
            } else {
                // Redirect non-admins
                LaunchedEffect(Unit) {
                    navController.popBackStack()
                }
            }
        }
    }
}
```

---

## ✅ TESTING CHECKLIST

### Phase 1: Authentication
- [ ] Can register new account
- [ ] Can login with credentials
- [ ] Tokens saved to EncryptedSharedPreferences
- [ ] Profile info displayed correctly
- [ ] Can logout
- [ ] Token auto-refresh works on 401

### Phase 2: Tracking
- [ ] Exercise start logged when entering screen
- [ ] Exercise finish logged when exiting screen
- [ ] Duration calculated correctly
- [ ] Score sent if applicable
- [ ] Activity events logged
- [ ] Can view exercise history

### Phase 3: Admin Features (if implementing)
- [ ] Admin dashboard visible only to admins
- [ ] Can view student list
- [ ] Can view individual student progress
- [ ] Statistics display correctly

---

## 🔧 CONFIGURATION

### Production vs Local

Update `NetworkModule.kt`:

```kotlin
@Provides
@Singleton
fun provideBaseUrl(): String {
    return "https://bizeng-server.fly.dev"  // Production
    // OR
    // return "http://10.0.2.2:8020"  // Local (emulator)
    // return "http://192.168.1.XXX:8020"  // Local (physical device)
}
```

---

## 📊 COMPLETE API ENDPOINT REFERENCE

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/register` | POST | No | Register new student |
| `/auth/login` | POST | No | Login |
| `/auth/refresh` | POST | No | Refresh access token |
| `/auth/logout` | POST | No | Logout |
| `/me` | GET | Yes | Get profile |
| `/tracking/attempts` | POST | Yes | Start exercise |
| `/tracking/attempts/{id}` | PATCH | Yes | Finish exercise |
| `/tracking/events` | POST | Yes | Log activity |
| `/tracking/my-attempts` | GET | Yes | Get history |
| `/admin/dashboard` | GET | Admin | Dashboard stats |
| `/admin/students` | GET | Admin | List students |
| `/admin/students/{id}` | GET | Admin | Student summary |
| `/chat` | POST | Optional | Free chat |
| `/ask` | POST | Optional | RAG Q&A |
| `/roleplay/start` | POST | Optional | Start roleplay |
| `/roleplay/turn` | POST | Optional | Roleplay turn |
| `/pronunciation/assess` | POST | Optional | Pronunciation |

---

## 🎯 SUMMARY

**Total Implementation Time:** 2-3 days

**What to implement:**

