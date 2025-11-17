# Admin Monitor API — Dashboard data endpoints

This file documents the admin-only monitoring endpoints served at `/admin/monitor/*`.
These endpoints are intended to feed charts on the admin dashboard (small arrays / key-value lists).

Auth
----
- All endpoints require a valid Access JWT Bearer token for a user with the `admin` role.
- The FastAPI dependency `require_admin` (in `deps.py`) is used. It resolves the current user from the Authorization header using the `get_current_user` and checks the database for a role named `admin`.
- Example header: `Authorization: Bearer <ACCESS_TOKEN>`

Common response pattern
-----------------------
- Most endpoints return either:
  - A list of `{ "day": "YYYY-MM-DD", "value": N }` (chart-ready time series for last 30 days) or
  - A small array of `{ key, count }` objects for categorical charts
  - Or a compact map `{ total: N, daily_signups: [...] }` where appropriate
- Endpoints return `Cache-Control: public, max-age=60, s-maxage=60` header so the dashboard can cache results for 60s.

How to get an admin test token
-----------------------------
1. Register a user via `/auth/register` (or use existing user).
2. Promote that user to the `admin` role directly in the database for testing (one-liner SQL). Example (Postgres):

   -- find user id
   SELECT id, email FROM users WHERE email = 'your_test@example.com';

   -- add role row (if roles table uses id)
   INSERT INTO roles (name) VALUES ('admin') ON CONFLICT DO NOTHING;

   -- link user to role (assumes user_roles has user_id and role_id)
   INSERT INTO user_roles (user_id, role_id) SELECT 'THE_USER_ID', r.id FROM roles r WHERE r.name='admin' ON CONFLICT DO NOTHING;

3. Login at `/auth/login` to get `access_token` and `refresh_token`.

Quick curl patterns
-------------------
- Health check (public):

  curl -i https://<BASE>/health

- Admin overview (requires admin access):

  curl -i -H "Authorization: Bearer <ACCESS_TOKEN>" https://<BASE>/admin/monitor/overview

- Daily attempts (chart-ready 30 days):

  curl -H "Authorization: Bearer <ACCESS_TOKEN>" https://<BASE>/admin/monitor/attempts

- Top events + daily histogram:

  curl -H "Authorization: Bearer <ACCESS_TOKEN>" https://<BASE>/admin/monitor/events

- Sessions per day:

  curl -H "Authorization: Bearer <ACCESS_TOKEN>" https://<BASE>/admin/monitor/sessions

- Users totals + signups per day:

  curl -H "Authorization: Bearer <ACCESS_TOKEN>" https://<BASE>/admin/monitor/users

- User role counts:

  curl -H "Authorization: Bearer <ACCESS_TOKEN>" https://<BASE>/admin/monitor/user_roles

- Skill map aggregates (top ids/types):

  curl -H "Authorization: Bearer <ACCESS_TOKEN>" https://<BASE>/admin/monitor/skill_map_id
  curl -H "Authorization: Bearer <ACCESS_TOKEN>" https://<BASE>/admin/monitor/skill_map_type

- Sample view (vw_attempts):

  curl -H "Authorization: Bearer <ACCESS_TOKEN>" https://<BASE>/admin/monitor/vw_attempts

Cache header check
------------------
After a successful request you should see the header `Cache-Control: public, max-age=60, s-maxage=60` in the response.

What each endpoint returns (shape examples)
-------------------------------------------
1. GET /admin/monitor/activity_events
   - Returns: `[ {"day":"2025-11-01","value":12}, ... ]` (30 items)

2. GET /admin/monitor/exercise_attempts
   - Returns: `[ {"day":"2025-11-01","value":5}, ... ]`

3. GET /admin/monitor/attempts
   - Alias for `/exercise_attempts` (keeps compatibility with client naming)

4. GET /admin/monitor/events
   - Returns: `{ "top": [{"event_type":"exercise_started","count":120}, ...], "daily": [{"day":"2025-11-01","value":30}, ...] }`

5. GET /admin/monitor/sessions
   - Returns: daily session starts same time-series shape

6. GET /admin/monitor/users
   - Returns: `{ "total": 1234, "daily_signups": [{"day":"2025-11-01","value":10}, ...] }`

7. GET /admin/monitor/user_roles
   - Returns: `[ {"role":"student","count":1200}, {"role":"admin","count":2} ]`

8. GET /admin/monitor/playing_with_neon
   - Returns: small array of recent rows from that table; best-effort dicts

9. GET /admin/monitor/skill_map_id
   - Returns: `[{"skill_map_id": "ex-123", "count": 25}, ...]` (top ids)

10. GET /admin/monitor/skill_map_type
    - Returns: `[{"skill_map_type": "vocab", "count": 321}, ...]`

11. GET /admin/monitor/vw_attempts
    - Returns: sample rows from the view (best-effort dict mapping). Use for debugging only.

12. GET /admin/monitor/refresh_tokens
    - Returns: `{ "total": 45, "active": 43, "revoked": 2 }`

13. GET /admin/monitor/roles
    - Returns: `[ {"role":"student","count":1200}, {"role":"admin","count":2} ]` same as user_roles but sourced from roles table

14. GET /admin/monitor/overview
    - Returns: combined small payload:
      {
        "activity_events": [...],
        "exercise_attempts": [...],
        "user_signups": [...],
        "roles": [...],
        "refresh_tokens": {...}
      }

Security notes / behaviour
--------------------------
- `require_admin` checks the DB at request time. Even if a token contains `is_admin`, the DB gate prevents stale privileges from being exploited.
- Endpoints are read-only (GET) and designed to return aggregated metadata only — no message content or private PII.
- If you need to expose slightly more detail (e.g., recent attempts) prefer the `playing_with_neon` or `vw_attempts` endpoints which return anonymized rows.

Testing checklist (quick)
-------------------------
- [ ] Create a test user and promote to admin in DB
- [ ] Login and get access token
- [ ] Run `curl -i -H "Authorization: Bearer <token>" https://<BASE>/admin/monitor/overview`
  - Expect HTTP 200 + JSON + `Cache-Control` header
- [ ] Run same call without Authorization
  - Expect HTTP 401 or HTTP 403 depending on whether the Authorization header is missing or user isn't admin
- [ ] Verify shapes match the examples above
- [ ] Check logs on the server (uvicorn) for any query errors if an endpoint returns empty arrays unexpectedly

Troubleshooting
---------------
- If you receive 401: ensure token is valid and not expired
- If you receive 403: ensure the user has `admin` role in `user_roles` (DB)
- If you receive 500: check server logs and the SQL for the endpoint; the endpoints try to fail-safe and return empty arrays

Notes for Android / client team
------------------------------
- The dashboard should call `/overview` and use the included arrays for charts.
- Prefer calling `/overview` every 15–30s when admin is actively viewing; the server enforces a 60s cache so you will get fresh data no faster than that.
- Keep UI charts tolerant to empty arrays (server may return empty list when no data)

If you want, I can run the smoke tests against the deployed server and collect a sample response for each endpoint (requires a valid admin token for the protected endpoints).
