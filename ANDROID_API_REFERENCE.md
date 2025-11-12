Android ↔ Server API Reference

This file documents all public endpoints the Android client uses (and should use) with request/response shapes, required auth, and notes for implementation.

Base URL
- Local dev: http://localhost:8020
- Prod: https://<your-ngrok-or-fly-url>

Authentication
- All protected endpoints require Authorization: Bearer <access_token>
- Tokens returned by /auth/register and /auth/login: {"access_token":"...","refresh_token":"..."}
- On 401: use /auth/refresh with the refresh_token to rotate tokens.

Quick tips for Android
- Use JSON bodies (no form-data) for auth, attempts, events.
- Store tokens in EncryptedSharedPreferences.
- Implement an OkHttp interceptor to attach the Authorization header and perform one automatic refresh on 401.

Endpoints

1) Health
- GET /health
- Auth: none
- Response: {"status":"nowwww"}

2) Version
- GET /version
- Auth: none
- Response: {"version":"0.1.0","env":"dev","debug":true}

3) Debug Embedding
- POST /debug/embed
- Auth: none
- Body: {"text":"Test string"}
- Response: {"dim":1536}

4) Debug Search
- GET /debug/search?q=...&k=5
- Auth: none
- Response: {"items":[{"score":0.85,"src":"unit_1_page_3","unit":"1","snippet":"..."}]}

---
AUTH

5) Register
- POST /auth/register
- Auth: none
- Body: {"email":"a@b.com","password":"Secret123","display_name":"John"}
- Response: {"access_token":"...","refresh_token":"..."}
- Notes: Server must return both tokens. Android should validate presence before storing.

6) Login
- POST /auth/login
- Auth: none
- Body: {"email":"a@b.com","password":"Secret123"}
- Response: {"access_token":"...","refresh_token":"..."}

7) Refresh
- POST /auth/refresh
- Auth: none (send refresh token in body)
- Body: {"refresh_token":"..."}
- Response: {"access_token":"...","refresh_token":"..."}
- Notes: Server rotates refresh tokens; update stored tokens.

8) Logout
- POST /auth/logout
- Body: {"refresh_token":"..."}
- Response: {"message":"Logged out successfully"}

---
CHAT

9) Free Chat
- POST /chat
- Auth: optional (recommended: send access token)
- Body: {"messages":[{"role":"user","content":"Hi"}],"k":5,"maxContextChars":6000}
- Response: {"answer":"...","sources":[]}
- Notes: messages.role must be one of ["user","assistant","system"]. Server sanitizes and trims history.
- Errors:
  - 401 Unauthorized: refresh token flow
  - 500 Internal: check server logs; Android should show friendly message and retry logic.

---
RAG / ASK

10) Ask (RAG)
- POST /ask
- Auth: optional
- Body: {"query":"What is business English?","k":5,"max_context_chars":6000}
- Response: {"answer":"...","sources":["unit_1_page_3"]}
- Notes: Server handles content filter fallbacks; Android displays answer + sources.

---
ROLEPLAY

11) List Scenarios
- GET /roleplay/scenarios
- Auth: optional
- Response: {"scenarios":[{...}]}

12) Scenario Details
- GET /roleplay/scenarios/{id}
- Auth: optional
- Response: detailed scenario object

13) Start Roleplay
- POST /roleplay/start
- Auth: optional (send user if logged in)
- Body: {"scenario_id":"job_interview","student_name":"John"}
- Response: {
    "session_id":"uuid",
    "scenario_title":"Job Interview",
    "scenario_description":"...",
    "context":"...",
    "student_role":"Job Candidate",
    "ai_role":"Hiring Manager",
    "current_stage":"opening",
    "initial_message":"Good morning..."
  }
- Notes: Android should store session_id and use it for /turn

14) Submit Turn
- POST /roleplay/turn
- Auth: optional
- Body: {"session_id":"uuid","message":"Hello"}
- Response: {
    "ai_message":"That's great...",
    "correction":{
       "has_errors":false,
       "errors":[],
       "feedback":null
    },
    "current_stage":"opening",
    "is_completed":false,
    "feedback":null
  }
- Notes: Android must handle both correction present/absent cases.

15) Hint
- POST /roleplay/hint
- Body: {"session_id":"uuid"}
- Response: {"hint":"Try to mention your experience","hints_used":1}

16) Session Info
- GET /roleplay/session/{session_id}
- Response: detailed session object (dialogue history in server format)

---
TRACKING (Client telemetry)

17) Start Attempt
- POST /tracking/attempts
- Auth: required (student or admin acting as student)
- Body: {"exercise_type":"roleplay","exercise_id":"job_interview","extra_metadata":{}}
- Response: ExerciseAttemptOut with id, started_at
- Notes: Android should call when user starts an exercise and store attempt id.

18) Finish Attempt
- PATCH /tracking/attempts/{id}
- Auth: required
- Body: {"status":"completed","score":0.87,"duration_seconds":312,"extra_metadata":{}}
- Response: updated attempt

19) Log Event
- POST /tracking/events
- Auth: required
- Body: {"event_type":"opened_chat","feature":"chat","extra_metadata":{}}
- Response: ActivityEventOut
- Notes: Use for lightweight telemetry: chat_opened, chat_message, rag_search, audio_used

20) Get My Attempts
- GET /tracking/my-attempts
- Auth: required
- Response: List of attempts for current user

---
PRONUNCIATION & SPEECH

21) Pronunciation Assess
- POST /pronunciation/assess
- Auth: optional
- multipart form: file field "audio" (wav), form field "reference_text"
- Response: PronunciationResult with per-word IPA, phonemes, accuracy scores, feedback
- Notes: Android should upload audio as multipart/form-data.

22) Pronunciation Quick Check
- POST /pronunciation/quick-check
- multipart form: audio + reference_text
- Response: {"score":82.3,"feedback":"Good pronunciation!","transcript":"Hello","needs_practice":false}

23) Pronunciation Test
- GET /pronunciation/test
- Response: service status and region

---
ADMIN

24) Admin Dashboard
- GET /admin/dashboard
- Auth: required (admin)
- Response: totals, active_students_7d, total_attempts, avg_completion_rate, popular_features

25) List Students
- GET /admin/students?group_number=...
- Auth: admin
- Response: list of students with basic metadata

26) Student Summary
- GET /admin/students/{student_id}
- Auth: admin
- Response: summary stats (no message content)

27) Student Attempts
- GET /admin/students/{student_id}/attempts?limit=50
- Auth: admin
- Response: list of ExerciseAttemptOut entries

28) Groups
- GET /admin/groups
- Auth: admin
- Response: group summaries

---
ERROR HANDLING
- 401 Unauthorized: refresh token flow. If refresh fails, force logout.
- 403 Forbidden: insufficient role/permission.
- 404 Not Found: resource not found (session, attempt, scenario)
- 500 Server Error: show friendly retry UI and report to diagnostics.

IMPLEMENTATION NOTES FOR ANDROID
- Use JSON for all POST/PATCH bodies except speech endpoints (multipart).
- Attach Authorization header for protected endpoints.
- Store access token expiry and refresh proactively if you can (refresh a minute before expiry).
- For telemetry, send best-effort events; if offline, buffer locally and upload when online.

EXAMPLES (curl)
- Login:
  curl -X POST http://localhost:8020/auth/login -H "Content-Type: application/json" -d '{"email":"a@b.com","password":"Secret123"}'

- Chat:
  curl -X POST http://localhost:8020/chat -H "Content-Type: application/json" -d '{"messages":[{"role":"user","content":"Hello"}]}'

- Start roleplay:
  curl -X POST http://localhost:8020/roleplay/start -H "Content-Type: application/json" -d '{"scenario_id":"job_interview","student_name":"Test"}'

---
If you'd like, I can now:
- Generate typed DTO classes for Android (Kotlin serializable data classes) matching server response models.
- Create a small `API_CHECKLIST.md` you can send to Android devs to verify each endpoint.


