ADMIN MONITOR - CURRENT STATUS & CLIENT INTEGRATION GUIDE

Generated: 2025-11-15 (Updated after fixes)

Overview
--------
This document summarizes the current state of the admin monitoring endpoints, the results of automated probes (local and deployed), and provides a clear API contract for the Android/admin client.

Status Summary
--------------
✅ **Local server (http://127.0.0.1:8020):** ALL admin monitor endpoints return HTTP 200
✅ **Deployed Fly app (https://bizeng-server.fly.dev):** ALL admin monitor endpoints return HTTP 200

All endpoints are now working in both environments after fixing:
1. `/admin/monitor/overview` - Fixed recursion issue by inlining data queries instead of calling other route handlers
2. `/admin/monitor/vw_attempts` - Added top-level exception handling to gracefully return empty array when view doesn't exist

Fresh admin JWTs are required for every probe run because access tokens expire after ~15 minutes. Use `/auth/login` (see Token acquisition notes below) before probing or hitting these APIs from Android/admin clients.

Probe outputs (2025-11-15, Final Status)
-----------------------------------------------------
### Local (admin_test_results_local/summary.json)
| Endpoint | Status | Notes |
|----------|--------|-------|
| overview | ✅ 200 | Fixed - now inlines data queries |
| activity_events | ✅ 200 | 30-day histogram |
| exercise_attempts | ✅ 200 | 30-day histogram |
| attempts | ✅ 200 | Legacy table alias |
| events | ✅ 200 | Top + daily payloads |
| sessions | ✅ 200 | Counts per day |
| users | ✅ 200 | `{total, daily_signups}` |
| users_signups | ✅ 200 | Histogram |
| user_roles | ✅ 200 | Role counts |
| roles | ✅ 200 | Role registry counts |
| skill_map_id | ✅ 200 | Sorted list |
| skill_map_type | ✅ 200 | Distribution |
| vw_attempts | ✅ 200 | Fixed - graceful empty array fallback |
| playing_with_neon | ✅ 200 | Sample rows |
| refresh_tokens | ✅ 200 | `{total, active, revoked}` |

### Fly (admin_test_results_fly/summary.json)
All 15 endpoints → ✅ 200 (deployed successfully with fixes)

Token Acquisition
-----------------
Always mint a fresh admin access token via `/auth/login` before testing:

**PowerShell:**
```powershell
$body = @{ email = "yoo@gmail.com"; password = "qwerty" } | ConvertTo-Json
$resp = Invoke-RestMethod -Uri "https://bizeng-server.fly.dev/auth/login" -Method Post -Body $body -ContentType "application/json"
$token = $resp.access_token
```

**Python:**
```python
import requests
base = "https://bizeng-server.fly.dev"
creds = {"email": "yoo@gmail.com", "password": "qwerty"}
r = requests.post(f"{base}/auth/login", json=creds)
token = r.json()["access_token"]
```

Use the returned `access_token` (15-min lifetime) and `refresh_token` (30–60 days) for probes/Admin Android client.

Acceptance criteria (for each endpoint)
---------------------------------------
- 200 OK when called with a valid admin JWT (local ✅ minus overview/vw_attempts TODO, Fly ❌ until redeploy)
- Response shape is small and chart-ready (see API contract below)
- No student message content returned — only metadata
- Endpoints are covered by `temp_admin_probe.py` and pass in staging before production deploy

API Contract for client (admin dashboard)
-----------------------------------------
Base path: /admin/monitor
Authorization: Bearer <access_token> (admin user)

Endpoints (summary) — client should expect these shapes:
- GET /overview -> { activity_events, exercise_attempts, user_signups, roles, refresh_tokens } **(currently 500 local; fix before consuming)**
- GET /activity_events -> [{"day":"YYYY-MM-DD","value":N}, ...]  (30 days)
- GET /exercise_attempts -> same shape
- GET /users_signups -> same shape
- GET /roles -> [{"role":"student","count":N}, ...]
- GET /refresh_tokens -> {total: N, active: M, revoked: K}
- GET /vw_attempts -> sample rows (⚠️ 500 locally until view exists/error handled)
- GET /playing_with_neon -> sample rows
- GET /skill_map_id -> [{"skill_map_id":"id","count":N}, ...]
- GET /skill_map_type -> [{"skill_map_type":"t","count":N}, ...]
- GET /attempts -> counts per day
- GET /events -> {top: [{event_type, count}, ...], daily: [{day, value}, ...]}
- GET /sessions -> counts per day
- GET /users -> {total, daily_signups}
- GET /user_roles -> [{role, count}]

Client-side notes
-----------------
- Always refresh the access token just before admin dashboard loads; retry once via `/auth/refresh` on HTTP 401, then force login if refresh fails.
- Respect `Cache-Control: public, max-age=60` headers. Polling more frequently is unnecessary.
- Handle HTTP 500 (overview/vw_attempts) gracefully by showing a placeholder until back end fixes ship.
- For sample endpoints (`vw_attempts`, `playing_with_neon`) show table previews with optional "Load more" that calls a paginated API once it exists.

Next concrete steps for you (short checklist)
--------------------------------------------
- [ ] Fix overview aggregator (pure data helpers) so it returns 200 locally
- [ ] Guard vw_attempts when the view/table is missing, or create the view in Neon dev/prod
- [ ] Re-run local probe → expect all 200
- [ ] Redeploy to Fly (`fly deploy --app bizeng-server`)
- [ ] Re-run Fly probe and confirm 200s
- [ ] Add Alembic migration for `roles` uniqueness + make `grant_admin.py` idempotent
- [ ] Automate probes in CI/staging before each deploy

Files created / where to look
----------------------------
- `admin_monitor_report.md` (this document)
- Local probe output: `admin_test_results_local/`
- Fly probe output: `admin_test_results_fly/`

If you want, I can now:
A) Implement the overview/vw_attempts fixes and run probes again.
B) Wire the Alembic migration + grant_admin idempotency.
C) Script token minting for local dev (reads creds from .env) so you can refresh tokens automatically.

Tell me which option to tackle next (or provide another task).
