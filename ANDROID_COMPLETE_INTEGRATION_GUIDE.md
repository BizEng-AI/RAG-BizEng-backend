        }
    }
}
```

---

### 5. AuthApi

```kotlin
// app/src/main/java/com/example/myapplication/data/remote/AuthApi.kt

class AuthApi(private val client: HttpClient, private val baseUrl: String) {
    
    suspend fun register(request: RegisterRequest): TokenResponse {
        return client.post("$baseUrl/auth/register") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.body()
    }
    
    suspend fun login(request: LoginRequest): TokenResponse {
        return client.post("$baseUrl/auth/login") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.body()
    }
    
    suspend fun refresh(request: RefreshRequest): TokenResponse {
        return client.post("$baseUrl/auth/refresh") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.body()
    }
    
    suspend fun logout(refreshToken: String) {
        client.post("$baseUrl/auth/logout") {
            contentType(ContentType.Application.Json)
            setBody(mapOf("refresh_token" to refreshToken))
        }
    }
    
    suspend fun getProfile(): UserProfileDto {
        return client.get("$baseUrl/me").body()
    }
}
```

---

### 6. TrackingApi

```kotlin
// app/src/main/java/com/example/myapplication/data/remote/TrackingApi.kt

class TrackingApi(private val client: HttpClient, private val baseUrl: String) {
    
    suspend fun startAttempt(request: StartAttemptRequest): AttemptDto {
        return client.post("$baseUrl/tracking/attempts") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.body()
    }
    
    suspend fun updateAttempt(attemptId: String, request: UpdateAttemptRequest): AttemptDto {
        return client.patch("$baseUrl/tracking/attempts/$attemptId") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.body()
    }
    
    suspend fun logEvent(request: LogEventRequest) {
        client.post("$baseUrl/tracking/events") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }
    }
    
    suspend fun getMyProgress(from: String? = null, to: String? = null): ProgressSummaryDto {
        return client.get("$baseUrl/tracking/my-progress") {
            from?.let { parameter("from", it) }
            to?.let { parameter("to", it) }
        }.body()
    }
}
```

---

### 7. AdminApi

```kotlin
// app/src/main/java/com/example/myapplication/data/remote/AdminApi.kt

class AdminApi(private val client: HttpClient, private val baseUrl: String) {
    
    suspend fun getDashboard(): AdminDashboardDto {
        return client.get("$baseUrl/admin/dashboard").body()
    }
    
    suspend fun getStudents(skip: Int = 0, limit: Int = 50): StudentsListDto {
        return client.get("$baseUrl/admin/students") {
            parameter("skip", skip)
            parameter("limit", limit)
        }.body()
    }
    
    suspend fun getStudentProgress(
        userId: String,
        from: String? = null,
        to: String? = null
    ): StudentProgressDto {
        return client.get("$baseUrl/admin/students/$userId/progress") {
            from?.let { parameter("from", it) }
            to?.let { parameter("to", it) }
        }.body()
    }
}
```

---

## 📱 UI IMPLEMENTATION

### Navigation Structure

```
┌─────────────────────────────────────┐
│          SplashScreen               │
│  (Check if logged in)               │
└────────┬────────────────────────────┘
         │
         ├─ Not Logged In
         │  ↓
         │  ┌──────────────────────┐
         │  │   LoginScreen        │
         │  └──────────────────────┘
         │
         └─ Logged In
            ↓
            ┌──────────────────────┐
            │   Is Admin?          │
            └────┬─────────────────┘
                 │
                 ├─ Student
                 │  ↓
                 │  ┌──────────────────────┐
                 │  │  MainScreen          │
                 │  │  - Home              │
                 │  │  - Chat              │
                 │  │  - RAG/Ask           │
                 │  │  - Roleplay          │
                 │  │  - Pronunciation     │
                 │  │  - My Progress       │
                 │  │  - Profile           │
                 │  └──────────────────────┘
                 │
                 └─ Admin
                    ↓
                    ┌──────────────────────┐
                    │  AdminDashboard      │
                    │  - Overview          │
                    │  - Students List     │
                    │  - Student Detail    │
                    └──────────────────────┘
```

---

### Student Flow Example

```kotlin
// When opening Chat screen
LaunchedEffect(Unit) {
    // Log "opened" event
    trackingApi.logEvent(
        LogEventRequest(
            exerciseId = "chat_general",
            eventType = "opened",
            payload = mapOf("screen" to "ChatScreen")
        )
    )
    
    // Start attempt
    val attempt = trackingApi.startAttempt(
        StartAttemptRequest(
            exerciseId = "chat_general",
            exerciseType = "chat"
        )
    )
    currentAttemptId = attempt.id
}

// When user sends message
scope.launch {
    val startTime = System.currentTimeMillis()
    
    // Call chat API
    val response = chatApi.chat(ChatReqDto(messages = messages))
    
    // If successful, mark completed
    val duration = ((System.currentTimeMillis() - startTime) / 1000).toInt()
    trackingApi.updateAttempt(
        attemptId = currentAttemptId,
        request = UpdateAttemptRequest(
            status = "completed",
            durationSec = duration
        )
    )
}
```

---

### Admin Dashboard Screen

```kotlin
@Composable
fun AdminDashboardScreen(
    viewModel: AdminViewModel = viewModel()
) {
    val dashboard by viewModel.dashboard.collectAsState()
    val students by viewModel.students.collectAsState()
    
    LaunchedEffect(Unit) {
        viewModel.loadDashboard()
        viewModel.loadStudents()
    }
    
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        // Overview Cards
        Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            DashboardCard(
                title = "Total Students",
                value = dashboard.totalStudents.toString()
            )
            DashboardCard(
                title = "Active Today",
                value = dashboard.activeToday.toString()
            )
            DashboardCard(
                title = "Avg Score",
                value = "${dashboard.avgScore}%"
            )
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Students List
        Text("Students", style = MaterialTheme.typography.h6)
        
        LazyColumn {
            items(students) { student ->
                StudentListItem(
                    student = student,
                    onClick = { 
                        navController.navigate("student_detail/${student.id}")
                    }
                )
            }
        }
    }
}

@Composable
fun StudentListItem(student: StudentSummaryDto, onClick: () -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp)
            .clickable(onClick = onClick)
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column {
                Text(student.displayName, style = MaterialTheme.typography.subtitle1)
                Text(student.email, style = MaterialTheme.typography.caption)
                Text(
                    "Last active: ${formatDate(student.lastActive)}",
                    style = MaterialTheme.typography.caption
                )
            }
            Column(horizontalAlignment = Alignment.End) {
                Text("${student.totalAttempts} attempts")
                student.avgScore?.let {
                    Text("Avg: ${it.toInt()}%", color = MaterialTheme.colors.primary)
                }
            }
        }
    }
}
```

---

### Student Detail Screen (Admin View)

```kotlin
@Composable
fun StudentDetailScreen(
    userId: String,
    viewModel: AdminViewModel = viewModel()
) {
    val progress by viewModel.studentProgress.collectAsState()
    
    LaunchedEffect(userId) {
        viewModel.loadStudentProgress(userId)
    }
    
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        // Student Info
        Text(progress.user.displayName, style = MaterialTheme.typography.h5)
        Text(progress.user.email, style = MaterialTheme.typography.body2)
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Stats Summary
        Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            StatCard("Attempts", progress.totals.attempts.toString())
            StatCard("Completed", progress.totals.completed.toString())
            StatCard("Avg Score", "${progress.totals.avgScore.toInt()}%")
            StatCard("Minutes", progress.totals.totalMinutes.toString())
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // By Type Breakdown
        Text("By Exercise Type", style = MaterialTheme.typography.h6)
        progress.byType.forEach { (type, stats) ->
            Row(
                modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(type.capitalize())
                Text("${stats.attempts} attempts • ${stats.avgScore.toInt()}% avg")
            }
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Recent Attempts
        Text("Recent Activity", style = MaterialTheme.typography.h6)
        LazyColumn {
            items(progress.recentAttempts) { attempt ->
                AttemptCard(attempt)
            }
        }
    }
}
```

---

## 🔒 SECURITY CONSIDERATIONS

### ✅ Implemented:
1. **Argon2id password hashing** (server-side)
2. **Short-lived access tokens** (30 min)
3. **Long-lived refresh tokens** (45 days) with rotation
4. **Encrypted token storage** (EncryptedSharedPreferences)
5. **Role-based access control** (RBAC)
6. **Database-level permission checks** (not just token claims)
7. **HTTPS only** (Fly.io)
8. **SQL injection prevention** (SQLAlchemy ORM)
9. **CORS configured** (only for specific origins)

### 🚨 Important:
- **NEVER log tokens** in production
- **NEVER hardcode secrets** in Android app
- **Admin registration** should be manual/CLI only in production
- **Tokens stored only in EncryptedSharedPreferences**, never plain SharedPreferences
- **Always use HTTPS** in production
- **Validate all user input** on both client and server

---

## 🧪 TESTING WORKFLOW

### 1. Test Server Endpoints
```cmd
cd C:\Users\sanja\rag-biz-english\server
python test_auth_system.py
```

### 2. Test Android App
```cmd
cd C:\Users\sanja\rag-biz-english\android
gradlew test
gradlew connectedAndroidTest
```

### 3. Manual Testing Flow

**Register → Login → Use App → Check Admin Dashboard**

1. Register student account
2. Login
3. Use chat, roleplay, pronunciation
4. Check progress in "My Progress"
5. Admin logs in
6. Admin sees student's activity in dashboard
7. Admin clicks student → sees detailed progress

---

## 📊 PRIVACY COMPLIANCE

### What We Track:
- ✅ Exercise ID (what exercise)
- ✅ Attempt start/finish time
- ✅ Score (pronunciation, roleplay)
- ✅ Duration
- ✅ Exercise type

### What We DON'T Track:
- ❌ Message content (chat, roleplay)
- ❌ Audio recordings
- ❌ Personal identifying info beyond email
- ❌ Device info
- ❌ Location

### GDPR Compliance:
- Users can request data export (implement `/me/export`)
- Users can request data deletion (implement `/me/delete`)
- Clear privacy policy
- Opt-in for analytics (if adding Google Analytics later)

---

## 🚀 DEPLOYMENT CHECKLIST

### Server (Already Done ✅):
- [x] Neon PostgreSQL setup
- [x] Qdrant Cloud setup
- [x] Azure OpenAI/Speech configured
- [x] Fly.io deployment
- [x] Environment variables set
- [x] Database migrations run
- [x] All endpoints tested

### Android (TODO):
- [ ] Update DTOs to match server
- [ ] Implement AuthManager
- [ ] Implement AuthInterceptor
- [ ] Create AuthApi, TrackingApi, AdminApi
- [ ] Update existing APIs (ChatApi, RoleplayApi, etc.) to use auth
- [ ] Implement LoginScreen
- [ ] Implement AdminDashboardScreen
- [ ] Add progress tracking to all exercises
- [ ] Test registration flow
- [ ] Test login flow
- [ ] Test token refresh
- [ ] Test admin dashboard
- [ ] Build APK
- [ ] Test on device

---

## 📞 API REFERENCE SUMMARY

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/health` | GET | No | Server health check |
| `/auth/register` | POST | No | Create account |
| `/auth/login` | POST | No | Login |
| `/auth/refresh` | POST | No | Refresh token |
| `/auth/logout` | POST | Yes | Logout |
| `/me` | GET | Yes | Get profile |
| `/tracking/attempts` | POST | Yes | Start attempt |
| `/tracking/attempts/{id}` | PATCH | Yes | Update attempt |
| `/tracking/events` | POST | Yes | Log event |
| `/tracking/my-progress` | GET | Yes | Get progress |
| `/admin/dashboard` | GET | Admin | Dashboard |
| `/admin/students` | GET | Admin | List students |
| `/admin/students/{id}/progress` | GET | Admin | Student detail |
| `/chat` | POST | Yes | Chat |
| `/ask` | POST | Yes | RAG Q&A |
| `/roleplay/start` | POST | Yes | Start roleplay |
| `/roleplay/turn` | POST | Yes | Roleplay turn |
| `/pronunciation/assess` | POST | Yes | Assess pronunciation |

---

## 🎯 NEXT STEPS

1. **Copy all DTOs** to Android project
2. **Implement AuthManager** (token storage)
3. **Implement AuthInterceptor** (auto-refresh)
4. **Create API classes** (AuthApi, TrackingApi, AdminApi)
5. **Build LoginScreen**
6. **Build AdminDashboardScreen**
7. **Add tracking to exercises**
8. **Test end-to-end**
9. **Build APK**
10. **Distribute to students**

---

**Server Ready ✅ | Android Implementation TODO**

**Last Updated:** November 12, 2025  
**Server URL:** https://bizeng-server.fly.dev  
**Database:** Neon PostgreSQL (Production Ready)  
**Vector DB:** Qdrant Cloud (Production Ready)
# 📱 COMPLETE ANDROID INTEGRATION GUIDE
**Generated:** November 12, 2025  
**Server:** https://bizeng-server.fly.dev  
**Status:** ✅ Production Ready with Auth System

---

## 🎯 OVERVIEW

Your Business English Learning App now has:
- ✅ **Full Authentication System** (JWT + Refresh Tokens)
- ✅ **Role-Based Access Control** (Student/Admin)
- ✅ **Progress Tracking** (Attempts & Events)
- ✅ **Admin Dashboard** (Monitor all students)
- ✅ **Azure OpenAI Integration** (Chat, RAG, Roleplay)
- ✅ **Azure Speech Services** (Pronunciation Assessment)
- ✅ **Qdrant Vector Database** (RAG retrieval)

---

## 🏗️ ARCHITECTURE

### Server Stack:
- **FastAPI** (Python) on Fly.io
- **Neon PostgreSQL** (Database)
- **Qdrant Cloud** (Vector DB)
- **Azure OpenAI** (Chat, Embeddings)
- **Azure Speech** (Pronunciation)

### Android Stack:
- **Kotlin** + Jetpack Compose
- **Ktor Client** (Networking)
- **EncryptedSharedPreferences** (Token storage)
- **Kotlin Serialization** (JSON)
- **Hilt** (Dependency Injection - optional)

---

## 🔐 AUTHENTICATION FLOW

### Registration & Login

```
┌─────────────┐
│   Android   │
└──────┬──────┘
       │ POST /auth/register
       │ { email, password, display_name }
       ▼
┌─────────────┐
│   Server    │ → Creates user in Neon DB
└──────┬──────┘ → Generates JWT tokens
       │
       │ Returns:
       │ { access_token, refresh_token, user: { id, email, roles } }
       ▼
┌─────────────┐
│   Android   │ → Saves tokens in EncryptedSharedPreferences
└─────────────┘ → Navigates to main screen
```

### Token Refresh (Automatic)

```
┌─────────────┐
│   Android   │ Makes API call with access_token
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Server    │ Returns 401 (token expired)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Auth        │ Intercepts 401
│ Interceptor │ → Calls /auth/refresh with refresh_token
└──────┬──────┘ → Gets new tokens
       │        → Retries original request
       │
       ▼
┌─────────────┐
│   Android   │ Original request succeeds
└─────────────┘
```

---

## 📊 DATABASE SCHEMA (Server Side)

### users
```sql
id               UUID PRIMARY KEY
email            TEXT UNIQUE NOT NULL
password_hash    TEXT NOT NULL (Argon2id)
display_name     TEXT
is_active        BOOLEAN DEFAULT TRUE
created_at       TIMESTAMPTZ DEFAULT NOW()
```

### roles
```sql
id               SERIAL PRIMARY KEY
name             TEXT UNIQUE (student, admin)
description      TEXT
```

### user_roles (Many-to-Many)
```sql
user_id          UUID REFERENCES users(id)
role_id          INTEGER REFERENCES roles(id)
PRIMARY KEY (user_id, role_id)
```

### refresh_tokens
```sql
id               UUID PRIMARY KEY
user_id          UUID REFERENCES users(id)
token_hash       TEXT NOT NULL
issued_at        TIMESTAMPTZ DEFAULT NOW()
expires_at       TIMESTAMPTZ
revoked_at       TIMESTAMPTZ
replaces_token   UUID REFERENCES refresh_tokens(id)
```

### exercise_attempts (Progress Tracking)
```sql
id               TEXT PRIMARY KEY
user_id          UUID REFERENCES users(id)
exercise_id      TEXT NOT NULL
exercise_type    TEXT (chat, roleplay, pronunciation, rag)
status           TEXT (started, completed, abandoned)
score            NUMERIC(5,2)
duration_sec     INTEGER
started_at       TIMESTAMPTZ DEFAULT NOW()
finished_at      TIMESTAMPTZ
metadata         JSONB
```

### activity_events (Analytics)
```sql
id               BIGSERIAL PRIMARY KEY
user_id          UUID REFERENCES users(id)
exercise_id      TEXT
event_type       TEXT (opened, started, completed, abandoned)
ts               TIMESTAMPTZ DEFAULT NOW()
payload          JSONB
```

---

## 🔑 SERVER ENDPOINTS

### 🔐 Authentication Endpoints

#### POST /auth/register
**Purpose:** Create new user account (admin-only in production)

**Request:**
```json
{
  "email": "student@example.com",
  "password": "SecurePass123!",
  "display_name": "John Doe"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-string",
    "email": "student@example.com",
    "display_name": "John Doe",
    "roles": ["student"]
  }
}
```

**Android DTO:**
```kotlin
@Serializable
data class RegisterRequest(
    val email: String,
    val password: String,
    @SerialName("display_name") val displayName: String
)

@Serializable
data class TokenResponse(
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String,
    @SerialName("token_type") val tokenType: String = "bearer",
    val user: UserDto
)

@Serializable
data class UserDto(
    val id: String,
    val email: String,
    @SerialName("display_name") val displayName: String,
    val roles: List<String>
)
```

---

#### POST /auth/login
**Purpose:** Login existing user

**Request:**
```json
{
  "email": "student@example.com",
  "password": "SecurePass123!"
}
```

**Response:** Same as registration

**Android DTO:**
```kotlin
@Serializable
data class LoginRequest(
    val email: String,
    val password: String
)
```

---

#### POST /auth/refresh
**Purpose:** Get new access token using refresh token

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "new-token...",
  "refresh_token": "new-refresh-token...",
  "token_type": "bearer"
}
```

**Android DTO:**
```kotlin
@Serializable
data class RefreshRequest(
    @SerialName("refresh_token") val refreshToken: String
)
```

---

#### POST /auth/logout
**Purpose:** Revoke refresh token (optional but recommended)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "refresh_token": "token-to-revoke..."
}
```

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

---

### 👤 User Profile Endpoints

#### GET /me
**Purpose:** Get current user info

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "uuid",
  "email": "student@example.com",
  "display_name": "John Doe",
  "roles": ["student"],
  "is_active": true,
  "created_at": "2025-11-12T10:30:00Z"
}
```

**Android DTO:**
```kotlin
@Serializable
data class UserProfileDto(
    val id: String,
    val email: String,
    @SerialName("display_name") val displayName: String,
    val roles: List<String>,
    @SerialName("is_active") val isActive: Boolean,
    @SerialName("created_at") val createdAt: String
)
```

---

### 📊 Progress Tracking Endpoints

#### POST /tracking/attempts
**Purpose:** Start a new exercise attempt

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "exercise_id": "roleplay_job_interview_001",
  "exercise_type": "roleplay"
}
```

**Response:**
```json
{
  "id": "attempt_uuid",
  "exercise_id": "roleplay_job_interview_001",
  "exercise_type": "roleplay",
  "status": "started",
  "started_at": "2025-11-12T15:30:00Z"
}
```

**Android DTO:**
```kotlin
@Serializable
data class StartAttemptRequest(
    @SerialName("exercise_id") val exerciseId: String,
    @SerialName("exercise_type") val exerciseType: String
)

@Serializable
data class AttemptDto(
    val id: String,
    @SerialName("exercise_id") val exerciseId: String,
    @SerialName("exercise_type") val exerciseType: String,
    val status: String,
    val score: Float? = null,
    @SerialName("duration_sec") val durationSec: Int? = null,
    @SerialName("started_at") val startedAt: String,
    @SerialName("finished_at") val finishedAt: String? = null
)
```

---

#### PATCH /tracking/attempts/{attempt_id}
**Purpose:** Update attempt (mark completed, add score)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "status": "completed",
  "score": 85.5,
  "duration_sec": 420
}
```

**Response:**
```json
{
  "id": "attempt_uuid",
  "exercise_id": "roleplay_job_interview_001",
  "status": "completed",
  "score": 85.5,
  "duration_sec": 420,
  "finished_at": "2025-11-12T15:37:00Z"
}
```

**Android DTO:**
```kotlin
@Serializable
data class UpdateAttemptRequest(
    val status: String? = null,
    val score: Float? = null,
    @SerialName("duration_sec") val durationSec: Int? = null
)
```

---

#### POST /tracking/events
**Purpose:** Log activity events (opened, started, completed)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "exercise_id": "chat_basic_001",
  "event_type": "opened",
  "payload": {
    "attempt_id": "attempt_uuid",
    "screen": "ChatScreen"
  }
}
```

**Response:**
```json
{
  "id": 12345,
  "event_type": "opened",
  "ts": "2025-11-12T15:30:00Z"
}
```

**Android DTO:**
```kotlin
@Serializable
data class LogEventRequest(
    @SerialName("exercise_id") val exerciseId: String,
    @SerialName("event_type") val eventType: String,
    val payload: Map<String, String>? = null
)
```

---

#### GET /tracking/my-progress
**Purpose:** Get current user's progress summary

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Params:**
- `from` (optional): ISO date (e.g., 2025-11-01)
- `to` (optional): ISO date (e.g., 2025-11-07)
- `exercise_type` (optional): chat, roleplay, pronunciation, rag

**Response:**
```json
{
  "totals": {
    "attempts": 25,
    "completed": 20,
    "avg_score": 82.5,
    "total_minutes": 180
  },
  "by_type": {
    "roleplay": {"attempts": 10, "avg_score": 85.0},
    "pronunciation": {"attempts": 8, "avg_score": 78.0},
    "chat": {"attempts": 7, "avg_score": 85.0}
  },
  "recent_attempts": [
    {
      "id": "attempt_uuid",
      "exercise_id": "roleplay_job_interview_001",
      "exercise_type": "roleplay",
      "score": 88.0,
      "finished_at": "2025-11-12T15:30:00Z"
    }
  ]
}
```

**Android DTO:**
```kotlin
@Serializable
data class ProgressSummaryDto(
    val totals: TotalsDto,
    @SerialName("by_type") val byType: Map<String, TypeStatsDto>,
    @SerialName("recent_attempts") val recentAttempts: List<AttemptDto>
)

@Serializable
data class TotalsDto(
    val attempts: Int,
    val completed: Int,
    @SerialName("avg_score") val avgScore: Float,
    @SerialName("total_minutes") val totalMinutes: Int
)

@Serializable
data class TypeStatsDto(
    val attempts: Int,
    @SerialName("avg_score") val avgScore: Float
)
```

---

### 👨‍💼 Admin Endpoints (Require admin role)

#### GET /admin/dashboard
**Purpose:** Get overview of all students

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "total_students": 25,
  "active_today": 12,
  "total_attempts": 500,
  "avg_score": 78.5,
  "top_performers": [
    {"user_id": "uuid", "display_name": "John Doe", "avg_score": 95.0}
  ]
}
```

**Android DTO:**
```kotlin
@Serializable
data class AdminDashboardDto(
    @SerialName("total_students") val totalStudents: Int,
    @SerialName("active_today") val activeToday: Int,
    @SerialName("total_attempts") val totalAttempts: Int,
    @SerialName("avg_score") val avgScore: Float,
    @SerialName("top_performers") val topPerformers: List<TopPerformerDto>
)

@Serializable
data class TopPerformerDto(
    @SerialName("user_id") val userId: String,
    @SerialName("display_name") val displayName: String,
    @SerialName("avg_score") val avgScore: Float
)
```

---

#### GET /admin/students
**Purpose:** List all students

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Params:**
- `skip` (optional): Pagination offset
- `limit` (optional): Page size (default: 50)

**Response:**
```json
{
  "total": 25,
  "students": [
    {
      "id": "uuid",
      "email": "student1@example.com",
      "display_name": "John Doe",
      "created_at": "2025-11-01T10:00:00Z",
      "last_active": "2025-11-12T14:30:00Z",
      "total_attempts": 15,
      "avg_score": 82.5
    }
  ]
}
```

**Android DTO:**
```kotlin
@Serializable
data class StudentsListDto(
    val total: Int,
    val students: List<StudentSummaryDto>
)

@Serializable
data class StudentSummaryDto(
    val id: String,
    val email: String,
    @SerialName("display_name") val displayName: String,
    @SerialName("created_at") val createdAt: String,
    @SerialName("last_active") val lastActive: String? = null,
    @SerialName("total_attempts") val totalAttempts: Int,
    @SerialName("avg_score") val avgScore: Float?
)
```

---

#### GET /admin/students/{user_id}/progress
**Purpose:** Get detailed progress for a specific student

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Params:**
- `from` (optional): ISO date
- `to` (optional): ISO date

**Response:**
```json
{
  "user": {
    "id": "uuid",
    "display_name": "John Doe",
    "email": "student@example.com"
  },
  "totals": {
    "attempts": 25,
    "completed": 20,
    "avg_score": 82.5,
    "total_minutes": 180
  },
  "by_day": [
    {
      "date": "2025-11-12",
      "attempts": 5,
      "completed": 4,
      "avg_score": 85.0,
      "minutes": 35
    }
  ],
  "by_type": {
    "roleplay": {"attempts": 10, "avg_score": 85.0},
    "pronunciation": {"attempts": 8, "avg_score": 78.0}
  },
  "recent_attempts": [
    {
      "id": "attempt_uuid",
      "exercise_id": "roleplay_job_interview_001",
      "exercise_type": "roleplay",
      "score": 88.0,
      "duration_sec": 420,
      "finished_at": "2025-11-12T15:30:00Z"
    }
  ]
}
```

**Android DTO:**
```kotlin
@Serializable
data class StudentProgressDto(
    val user: UserDto,
    val totals: TotalsDto,
    @SerialName("by_day") val byDay: List<DayStatsDto>,
    @SerialName("by_type") val byType: Map<String, TypeStatsDto>,
    @SerialName("recent_attempts") val recentAttempts: List<AttemptDto>
)

@Serializable
data class DayStatsDto(
    val date: String,
    val attempts: Int,
    val completed: Int,
    @SerialName("avg_score") val avgScore: Float,
    val minutes: Int
)
```

---

### 💬 Exercise Endpoints (Existing - now with auth)

All existing endpoints now require authentication:

#### POST /chat
**Headers:** `Authorization: Bearer <access_token>`

#### POST /ask
**Headers:** `Authorization: Bearer <access_token>`

#### POST /roleplay/start
**Headers:** `Authorization: Bearer <access_token>`

#### POST /roleplay/turn
**Headers:** `Authorization: Bearer <access_token>`

#### POST /pronunciation/assess
**Headers:** `Authorization: Bearer <access_token>`

---

## 🔧 ANDROID IMPLEMENTATION

### 1. Dependencies (build.gradle.kts)

```kotlin
dependencies {
    // Ktor Client
    implementation("io.ktor:ktor-client-android:2.3.7")
    implementation("io.ktor:ktor-client-content-negotiation:2.3.7")
    implementation("io.ktor:ktor-serialization-kotlinx-json:2.3.7")
    implementation("io.ktor:ktor-client-logging:2.3.7")
    
    // Kotlin Serialization
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.2")
    
    // Encrypted SharedPreferences
    implementation("androidx.security:security-crypto:1.1.0-alpha06")
    
    // Compose Navigation
    implementation("androidx.navigation:navigation-compose:2.7.6")
    
    // ViewModel
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0")
}
```

---

### 2. AuthManager (Token Storage)

```kotlin
// app/src/main/java/com/example/myapplication/auth/AuthManager.kt

class AuthManager(context: Context) {
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()
    
    private val prefs = EncryptedSharedPreferences.create(
        context,
        "auth_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )
    
    fun saveTokens(accessToken: String, refreshToken: String, user: UserDto) {
        prefs.edit {
            putString("access_token", accessToken)
            putString("refresh_token", refreshToken)
            putString("user_id", user.id)
            putString("user_email", user.email)
            putString("user_display_name", user.displayName)
            putString("user_roles", user.roles.joinToString(","))
        }
    }
    
    fun getAccessToken(): String? = prefs.getString("access_token", null)
    fun getRefreshToken(): String? = prefs.getString("refresh_token", null)
    
    fun isLoggedIn(): Boolean = getAccessToken() != null
    
    fun isAdmin(): Boolean {
        val roles = prefs.getString("user_roles", "")?.split(",") ?: emptyList()
        return "admin" in roles
    }
    
    fun getUserId(): String? = prefs.getString("user_id", null)
    fun getUserEmail(): String? = prefs.getString("user_email", null)
    fun getUserDisplayName(): String? = prefs.getString("user_display_name", null)
    
    fun clear() {
        prefs.edit { clear() }
    }
}
```

---

### 3. AuthInterceptor (Auto Token Refresh)

```kotlin
// app/src/main/java/com/example/myapplication/auth/AuthInterceptor.kt

class AuthInterceptor(
    private val authManager: AuthManager,
    private val authApi: AuthApi
) : Interceptor {
    
    private val refreshLock = Mutex()
    
    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()
        
        // Add access token to request
        val accessToken = authManager.getAccessToken()
        val request = if (accessToken != null) {
            originalRequest.newBuilder()
                .header("Authorization", "Bearer $accessToken")
                .build()
        } else {
            originalRequest
        }
        
        // Execute request
        var response = chain.proceed(request)
        
        // If 401 and we have refresh token, try to refresh
        if (response.code == 401 && authManager.getRefreshToken() != null) {
            response.close()
            
            // Use mutex to prevent multiple simultaneous refresh attempts
            runBlocking {
                refreshLock.withLock {
                    // Check if another thread already refreshed
                    val currentToken = authManager.getAccessToken()
                    if (currentToken != accessToken) {
                        // Token was already refreshed by another request
                        val newRequest = originalRequest.newBuilder()
                            .header("Authorization", "Bearer $currentToken")
                            .build()
                        return@runBlocking chain.proceed(newRequest)
                    }
                    
                    // Try to refresh
                    try {
                        val refreshToken = authManager.getRefreshToken()!!
                        val tokenResponse = authApi.refresh(RefreshRequest(refreshToken))
                        
                        // Save new tokens
                        authManager.saveTokens(
                            tokenResponse.accessToken,
                            tokenResponse.refreshToken,
                            tokenResponse.user
                        )
                        
                        // Retry original request with new token
                        val newRequest = originalRequest.newBuilder()
                            .header("Authorization", "Bearer ${tokenResponse.accessToken}")
                            .build()
                        return@runBlocking chain.proceed(newRequest)
                        
                    } catch (e: Exception) {
                        // Refresh failed, logout user
                        authManager.clear()
                        throw e
                    }
                }
            }
        }
        
        return response
    }
}
```

---

### 4. API Client Setup

```kotlin
// app/src/main/java/com/example/myapplication/network/ApiClient.kt

object ApiClient {
    private const val BASE_URL = "https://bizeng-server.fly.dev"
    
    fun createClient(authManager: AuthManager, authApi: AuthApi): HttpClient {
        return HttpClient(Android) {
            install(ContentNegotiation) {
                json(Json {
                    ignoreUnknownKeys = true
                    isLenient = true
                    encodeDefaults = true
                })
            }
            
            install(Logging) {
                logger = Logger.ANDROID
                level = LogLevel.INFO
            }
            
            install(HttpTimeout) {
                requestTimeoutMillis = 30_000
                connectTimeoutMillis = 15_000
            }
            
            // Add auth interceptor
            install(HttpSend) {
                AuthInterceptor(authManager, authApi).intercept(it)
            }
            
            defaultRequest {
                url(BASE_URL)
            }

