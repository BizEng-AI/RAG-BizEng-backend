# 📱 Android Admin Analytics Integration Guide
**Last updated:** November 15, 2025  \
**Backend base URL:** `https://bizeng-server.fly.dev`  
**Admin credentials (staging):** `yoo@gmail.com / qwerty`

This guide explains how the Android client should authenticate, call, and render the BizEng admin analytics endpoints now available on the server. It includes endpoint contracts, UI suggestions, caching rules, and troubleshooting tips so the Android app can implement the admin dashboard end-to-end.

---
## 1. Authentication Flow
1. **Login** via `POST /auth/login` with JSON body `{ "email": "...", "password": "..." }`.
2. Response includes:
   ```json
   {
     "access_token": "jwt...",
     "refresh_token": "opaque...",
     "token_type": "bearer",
     "user": {
       "id": 12,
       "email": "yoo@gmail.com",
       "roles": ["admin"]
     }
   }
   ```
3. Store the tokens securely (EncryptedSharedPreferences). Use the access token in `Authorization: Bearer <token>` for all admin requests.
4. On HTTP 401, call `POST /auth/refresh` with `{ "refresh": "..." }` once. If it fails, force re-login.

**Kotlin snippet (Retrofit + coroutines):**
```kotlin
interface AuthApi {
    @POST("/auth/login")
    suspend fun login(@Body body: LoginRequest): TokenResponse

    @POST("/auth/refresh")
    suspend fun refresh(@Body body: RefreshRequest): TokenResponse
}
```

---
## 2. Admin Analytics API Summary
Base path for every endpoint below: `https://bizeng-server.fly.dev/admin/monitor`

| Endpoint | Purpose | Response Shape | UI Suggestion |
|----------|---------|----------------|---------------|
| `GET /overview` | Bundles charts + totals (activity, attempts, signups, roles, refresh tokens) | `{ activity_events: [{day,value}], exercise_attempts: [...], user_signups: [...], roles: [{role,count}], refresh_tokens: {total,active,revoked} }` | Home overview screen with multi-chart carousel + stat cards |
| `GET /attempts_daily` | Attempts per day (30d) | `[ {"day": "2025-11-01", "count": 12}, ... ]` | Line/area chart with date axis |
| `GET /users_signups_daily` | New user signups per day (30d) | Same structure as above | Combined chart with attempts or separate card |
| `GET /active_today` | Count of distinct active students today | `{ "date": "2025-11-15", "active_students": 8 }` | KPI badge ("Active today") |
| `GET /recent_attempts?limit=20` | Latest attempts with metadata | `[ { "attempt_id": 99, "student_email": "...", "student_name": "...", "exercise_type": "roleplay", "exercise_id": "job_interview", "score": 0.82, "duration_seconds": 310, "started_at": "2025-11-12T10:15:00Z", "finished_at": "2025-11-12T10:20:00Z" }, ... ]` | RecyclerView table with student, exercise, score, timestamp |
| `GET /activity_events` | Histogram of events (legacy) | `[ {"day": "...", "value": n}, ... ]` | Optional chart |
| `GET /exercise_attempts` | Legacy alias (counts) | same as above | Legacy chart |
| `GET /attempts` | Historical counts from old `attempts` table | same as above | Only if needed |
| `GET /events` | `{ top: [{event_type,count}], daily: [{day,value}] }` | Top events list + chart |
| `GET /sessions` | Session starts per day | `[ {day,value} ]` | Chart |
| `GET /users` | `{ total: n, daily_signups: [{day,value}] }` | Total users widget + chart |
| `GET /users_signups` | Legacy histogram | `[ {day,value} ]` | Not necessary if using `/users_signups_daily` |
| `GET /user_roles` | `[ {role,count} ]` | Pie chart |
| `GET /roles` | Same as above (counts per role name) | `[ {role,count} ]` | Same as above |
| `GET /skill_map_id` | `[ {skill_map_id,count} ]` | Table or chips |
| `GET /skill_map_type` | `[ {skill_map_type,count} ]` | Chart |
| `GET /vw_attempts` | Sample rows from view (if exists) | `[{...}]` | Debug-only table |
| `GET /playing_with_neon` | Sample data | `[{...}]` | Optional |
| `GET /refresh_tokens` | `{ total, active, revoked }` | Token health widget |

All responses include `Cache-Control: public, max-age=60`. Don’t poll more than once per minute.

---
## 3. API Client Setup (Retrofit example)
```kotlin
interface AdminApi {
    @GET("/admin/monitor/overview")
    suspend fun overview(@Header("Authorization") token: String): OverviewDto

    @GET("/admin/monitor/attempts_daily")
    suspend fun attemptsDaily(@Header("Authorization") token: String): List<DayCountDto>

    @GET("/admin/monitor/users_signups_daily")
    suspend fun usersSignupsDaily(@Header("Authorization") token: String): List<DayCountDto>

    @GET("/admin/monitor/active_today")
    suspend fun activeToday(@Header("Authorization") token: String): ActiveTodayDto

    @GET("/admin/monitor/recent_attempts")
    suspend fun recentAttempts(
        @Header("Authorization") token: String,
        @Query("limit") limit: Int = 20
    ): List<RecentAttemptDto>
}
```

**DTO samples (Kotlin):**
```kotlin
@Serializable
data class DayCountDto(val day: String, val count: Int)

@Serializable
data class ActiveTodayDto(
    val date: String,
    @SerialName("active_students") val activeStudents: Int
)

@Serializable
data class RecentAttemptDto(
    @SerialName("attempt_id") val attemptId: Int,
    @SerialName("student_email") val studentEmail: String,
    @SerialName("student_name") val studentName: String,
    @SerialName("exercise_type") val exerciseType: String,
    @SerialName("exercise_id") val exerciseId: String?,
    val score: Float?,
    @SerialName("duration_seconds") val durationSeconds: Int?,
    @SerialName("started_at") val startedAt: String?,
    @SerialName("finished_at") val finishedAt: String?
)
```

### Auth Interceptor
```kotlin
class AuthInterceptor(
    private val authManager: AuthManager,
    private val authApi: AuthApi
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        var request = chain.request()
        authManager.accessToken()?.let { token ->
            request = request.newBuilder()
                .header("Authorization", "Bearer $token")
                .build()
        }

        val response = chain.proceed(request)
        if (response.code == 401 && authManager.refreshToken() != null) {
            response.close()
            val refreshResp = authApi.refresh(RefreshRequest(authManager.refreshToken()!!))
            authManager.saveTokens(refreshResp.access_token, refreshResp.refresh_token)
            val retryRequest = request.newBuilder()
                .header("Authorization", "Bearer ${refreshResp.access_token}")
                .build()
            return chain.proceed(retryRequest)
        }
        return response
    }
}
```

---
## 4. UI/UX Suggestions
1. **Overview screen:**
   - Hero cards for Active Today, Total Users, Refresh Token status.
   - Two charts: attempts vs signups per day (toggle).
   - Roles distribution pie chart.
2. **Recent Attempts tab:**
   - RecyclerView with student avatar/initial, email, exercise type, score, timestamp.
   - Filter by exercise type (chat, roleplay, pronunciation).
3. **Engagement tab:**
   - Use `event.top` for top feature usage list and `event.daily` for chart.
   - Show per-feature toggles (chat vs roleplay etc).
4. **Students tab:**
   - Use `/users` + `/users_signups_daily` for growth trends.
   - Provide quick filter to jump into student details screen.

All charts should respect the 30-day window; use the `day` field (ISO date) as x-axis, `count` or `value` as y-axis. For empty data, show friendly placeholder (“No activity yet”).

---
## 5. Caching & Offline Strategy
- Backend caches 60 seconds; app should match that TTL in memory.
- Use Room or in-memory store for last payload so admin can see previous data while loading.
- Add pull-to-refresh to force reload (bypass cache by ignoring TTL client-side).

---
## 6. Error Handling & Logging
| HTTP code | Meaning | UI action |
|-----------|---------|-----------|
| 200 | Success | Render data |
| 401 | Token expired / missing | Trigger refresh; if fails, log user out |
| 403 | Not admin | Show “Access restricted” (should not happen for admin users) |
| 404 | Endpoint missing | Report to backend (should not happen) |
| 500 | Backend error | Show retry CTA + send log via Crashlytics |

Log admin API calls with tag `AdminAnalyticsApi` including endpoint and success/failure to aid debugging.

---
## 7. Testing Checklist (Android)
1. Login as `yoo@gmail.com`.
2. Hit `/admin/monitor/overview` → verify charts render.
3. Hit `/admin/monitor/attempts_daily` & `/users_signups_daily` → verify combined chart.
4. Hit `/admin/monitor/active_today` → KPI updates.
5. Hit `/admin/monitor/recent_attempts` → recycler shows records.
6. Simulate expired token → ensure refresh flow triggers once.

Optional automated script (on Windows):
```powershell
python temp_admin_probe.py --token "<access_token>" `
    --base-url "https://bizeng-server.fly.dev" `
    --out admin_android_probe
```

---
## 8. Troubleshooting
| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| 401 everywhere | Token expired / missing | Re-login or refresh |
| 403 response | User lacks `admin` role | Ensure server user_roles table contains admin role |
| 404 on `/admin/monitor/*` | Old server build | Redeploy backend |
| 500 on attempts/signups | Neon connectivity issue or missing data | Check Fly logs (`fly logs -a bizeng-server`) |
| Empty charts | No activity yet | Encourage students to use app; data accumulates |

---
## 9. Reference Commands (for QA engineers)
```powershell
# Login & save token
$body = @{ email = "yoo@gmail.com"; password = "qwerty" } | ConvertTo-Json
$resp = Invoke-RestMethod -Uri "https://bizeng-server.fly.dev/auth/login" -Method Post -Body $body -ContentType "application/json"
$token = $resp.access_token

# Fetch overview
Invoke-RestMethod -Uri "https://bizeng-server.fly.dev/admin/monitor/overview" `
    -Headers @{ Authorization = "Bearer $token" }

# Attempts daily
Invoke-RestMethod -Uri "https://bizeng-server.fly.dev/admin/monitor/attempts_daily" `
    -Headers @{ Authorization = "Bearer $token" }

# Active today
Invoke-RestMethod -Uri "https://bizeng-server.fly.dev/admin/monitor/active_today" `
    -Headers @{ Authorization = "Bearer $token" }
```

---
## 10. Next Steps & Future Enhancements
- Add admin-only endpoints for granting/revoking roles (`/admin/users/grant_role`).
- Add pagination parameters to recent attempts (currently limit ≤100).
- Push websocket/SignalR updates for real-time dashboards (v2).

For any backend updates, check `ADMIN_ENDPOINTS_VERIFICATION.md` and `admin_monitor_report.md` for the latest contract before releasing an Android build.

---
## 11. Per-user and Per-group Exercise Analytics (NEW)
These admin-only endpoints surface the detailed exercise activity you requested (pronunciation/chat/roleplay counts, durations, scores). All require the same `Authorization: Bearer <access_token>` header and return `Cache-Control: public, max-age=60`.

### 11.1 `GET /admin/monitor/user_activity/{user_id}`
**Purpose:** Timeline of a single student’s exercises over the selected lookback window (default 30 days). Useful for a “Student detail” screen.

Query params: `days` (int, optional, 7–180, default 30)

Sample response:
```json
{
  "user": {
    "id": 42,
    "email": "student@example.com",
    "display_name": "Student 1",
    "group_name": "Group A"
  },
  "items": [
    {
      "attempt_id": 123,
      "exercise_type": "pronunciation",
      "exercise_id": "lesson_3_pron_1",
      "duration_seconds": 182,
      "pronunciation_score": 82.5,
      "score": 0.83,
      "started_at": "2025-11-12T10:15:00+00:00",
      "finished_at": "2025-11-12T10:18:02+00:00"
    }
  ]
}
```
**UI tips:** RecyclerView sorted by `started_at` descending, badges per `exercise_type`, show duration + pron score when not null. Provide pull-to-refresh + sticky header with student info.

### 11.2 `GET /admin/monitor/users_activity`
**Purpose:** Aggregate stats per student for the lookback window. Drives the “Students” tab/table.

Query params: `days` (int, optional, default 30)

Response array elements:
```json
{
  "user_id": 42,
  "email": "student@example.com",
  "display_name": "Student 1",
  "group_name": "Group A",
  "total_exercises": 25,
  "pronunciation_count": 10,
  "chat_count": 8,
  "roleplay_count": 7,
  "total_duration_seconds": 3600,
  "avg_pronunciation_score": 79.4
}
```
**UI tips:** Data table with sortable headers (group, total, avg score). Clicking a row should open the timeline screen (call `/user_activity/{id}`). Cache list locally for quick filtering.

### 11.3 `GET /admin/monitor/groups_activity`
**Purpose:** Aggregated metrics per group (or “Unassigned”). Drives the “Groups” overview screen.

Query params: `days` (int, optional, default 30)

Response array elements:
```json
{
  "group_name": "Group A",
  "student_count": 12,
  "total_exercises": 250,
  "pronunciation_count": 100,
  "chat_count": 80,
  "roleplay_count": 70,
  "total_duration_seconds": 20000,
  "avg_pronunciation_score": 81.2
}
```
**UI tips:** Card per group with sparkline / stacked bar. Tapping a group filters the students table client-side (by `group_name`).

### 11.4 Android DTOs / Retrofit definitions
```kotlin
@Serializable
data class UserActivityResponse(
    val user: UserSummaryDto,
    val items: List<UserActivityItemDto>
)

@Serializable
data class UserSummaryDto(
    val id: Long,
    val email: String,
    @SerialName("display_name") val displayName: String? = null,
    @SerialName("group_name") val groupName: String? = null
)

@Serializable
data class UserActivityItemDto(
    @SerialName("attempt_id") val attemptId: Long,
    @SerialName("exercise_type") val exerciseType: String,
    @SerialName("exercise_id") val exerciseId: String? = null,
    @SerialName("duration_seconds") val durationSeconds: Int? = null,
    @SerialName("pronunciation_score") val pronunciationScore: Float? = null,
    val score: Float? = null,
    @SerialName("started_at") val startedAt: String? = null,
    @SerialName("finished_at") val finishedAt: String? = null
)

@Serializable
data class UserActivitySummaryDto(
    @SerialName("user_id") val userId: Long,
    val email: String,
    @SerialName("display_name") val displayName: String? = null,
    @SerialName("group_name") val groupName: String? = null,
    @SerialName("total_exercises") val totalExercises: Int,
    @SerialName("pronunciation_count") val pronunciationCount: Int,
    @SerialName("chat_count") val chatCount: Int,
    @SerialName("roleplay_count") val roleplayCount: Int,
    @SerialName("total_duration_seconds") val totalDurationSeconds: Int,
    @SerialName("avg_pronunciation_score") val avgPronunciationScore: Float?
)

@Serializable
data class GroupActivitySummaryDto(
    @SerialName("group_name") val groupName: String,
    @SerialName("student_count") val studentCount: Int,
    @SerialName("total_exercises") val totalExercises: Int,
    @SerialName("pronunciation_count") val pronunciationCount: Int,
    @SerialName("chat_count") val chatCount: Int,
    @SerialName("roleplay_count") val roleplayCount: Int,
    @SerialName("total_duration_seconds") val totalDurationSeconds: Int,
    @SerialName("avg_pronunciation_score") val avgPronunciationScore: Float?
)
```
Retrofit additions:
```kotlin
interface AdminApi {
    @GET("/admin/monitor/user_activity/{user_id}")
    suspend fun userActivity(
        @Path("user_id") userId: Long,
        @Query("days") days: Int = 30
    ): UserActivityResponse

    @GET("/admin/monitor/users_activity")
    suspend fun usersActivity(@Query("days") days: Int = 30): List<UserActivitySummaryDto>

    @GET("/admin/monitor/groups_activity")
    suspend fun groupsActivity(@Query("days") days: Int = 30): List<GroupActivitySummaryDto>
}
```

### 11.5 UX & caching notes
- Keep the same 60s TTL caching as other admin feeds (store timestamp alongside payload).
- Provide lookback selector (7/30/90 days) and pass it via `days` query param.
- For students/groups tables, allow offline viewing by persisting the last payload in local storage (Room or serialized JSON).
- Handle 404 from `/user_activity` by showing “Student not found” and popping back.
- All endpoints return empty arrays when no data—show friendly placeholders (“No exercises yet in this range”).

