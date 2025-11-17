"""
Quick endpoint smoke tests for local server (http://localhost:8020 by default).
Run: python test_endpoints_quick.py

Checks: /health, /version, /auth/register, /auth/login, /auth/refresh,
/chat, /ask, /roleplay/scenarios, /roleplay/start, /roleplay/turn,
/tracking/attempts (start & finish), /tracking/events, /pronunciation/test

This is non-invasive and prints useful diagnostics.
"""
import requests
import os
import time
import uuid

BASE = os.getenv("BASE_URL", "http://localhost:8020")
HEADERS_JSON = {"Content-Type": "application/json"}

def safe_print(step, resp=None, extra=None):
    print(f"== {step} ==")
    if isinstance(resp, requests.Response):
        print(f"Status: {resp.status_code}")
        try:
            print("JSON:", resp.json())
        except Exception:
            print("Text:", resp.text[:500])
    elif isinstance(resp, Exception):
        print("Error:", resp)
    if extra:
        print(extra)
    print()

ok = True

# 1. Health
try:
    r = requests.get(f"{BASE}/health", timeout=8)
    safe_print("health", r)
    if r.status_code != 200:
        ok = False
except Exception as e:
    safe_print("health", e)
    ok = False

# 2. Version
try:
    r = requests.get(f"{BASE}/version", timeout=8)
    safe_print("version", r)
    if r.status_code != 200:
        ok = False
except Exception as e:
    safe_print("version", e)
    ok = False

# Prepare unique user
uniq = str(uuid.uuid4())[:8]
email = f"test+{uniq}@example.com"
password = "Test12345!"

tokens = {}

# 3. Register
try:
    payload = {"email": email, "password": password, "display_name": "SmokeTester"}
    r = requests.post(f"{BASE}/auth/register", json=payload, headers=HEADERS_JSON, timeout=12)
    safe_print("auth/register", r)
    if r.status_code == 201:
        data = r.json()
        tokens['access'] = data.get('access_token')
        tokens['refresh'] = data.get('refresh_token')
    else:
        ok = False
except Exception as e:
    safe_print("auth/register", e)
    ok = False

# 4. Login (in case register returned non-201)
if not tokens.get('access'):
    try:
        payload = {"email": email, "password": password}
        r = requests.post(f"{BASE}/auth/login", json=payload, headers=HEADERS_JSON, timeout=10)
        safe_print("auth/login", r)
        if r.status_code == 200:
            data = r.json()
            tokens['access'] = data.get('access_token')
            tokens['refresh'] = data.get('refresh_token')
        else:
            ok = False
    except Exception as e:
        safe_print("auth/login", e)
        ok = False

AUTH_HDR = {"Authorization": f"Bearer {tokens.get('access')}"} if tokens.get('access') else {}

# 5. Refresh
if tokens.get('refresh'):
    try:
        payload = {"refresh_token": tokens['refresh']}
        r = requests.post(f"{BASE}/auth/refresh", json=payload, headers=HEADERS_JSON, timeout=10)
        safe_print("auth/refresh", r)
        if r.status_code == 200:
            data = r.json()
            tokens['access'] = data.get('access_token')
            tokens['refresh'] = data.get('refresh_token')
            AUTH_HDR = {"Authorization": f"Bearer {tokens.get('access')}"}
        else:
            # not fatal
            pass
    except Exception as e:
        safe_print("auth/refresh", e)

# 6. Chat
try:
    body = {"messages": [{"role": "user", "content": "Hello, how do I open a meeting politely?"}], "k": 3}
    headers = {**HEADERS_JSON, **AUTH_HDR}
    r = requests.post(f"{BASE}/chat", json=body, headers=headers, timeout=20)
    safe_print("chat", r)
    if r.status_code != 200:
        ok = False
except Exception as e:
    safe_print("chat", e)
    ok = False

# 7. Ask (RAG)
try:
    body = {"query": "What are the stages of a business meeting?", "k": 5}
    headers = {**HEADERS_JSON}
    r = requests.post(f"{BASE}/ask", json=body, headers=headers, timeout=30)
    safe_print("ask", r)
    if r.status_code != 200:
        ok = False
except Exception as e:
    safe_print("ask", e)
    ok = False

# 8. Roleplay scenarios
scenario_id = None
try:
    r = requests.get(f"{BASE}/roleplay/scenarios", timeout=10)
    safe_print("roleplay/scenarios", r)
    if r.status_code == 200:
        data = r.json()
        # try to pick first scenario id
        scenarios = data.get('scenarios') or data.get('scenarios', [])
        if isinstance(scenarios, list) and len(scenarios) > 0:
            # items may be dicts with 'id' or 'scenario_id'
            first = scenarios[0]
            if isinstance(first, dict):
                scenario_id = first.get('id') or first.get('scenario_id')
            else:
                scenario_id = None
    else:
        ok = False
except Exception as e:
    safe_print("roleplay/scenarios", e)
    ok = False

# 9. Start roleplay
session_id = None
if scenario_id:
    try:
        payload = {"scenario_id": scenario_id, "student_name": "Tester"}
        r = requests.post(f"{BASE}/roleplay/start", json=payload, headers=HEADERS_JSON, timeout=15)
        safe_print("roleplay/start", r)
        if r.status_code == 200:
            data = r.json()
            session_id = data.get('session_id')
        else:
            ok = False
    except Exception as e:
        safe_print("roleplay/start", e)
        ok = False

# 10. Roleplay turn
if session_id:
    try:
        payload = {"session_id": session_id, "message": "Hello, I'm ready to practice."}
        r = requests.post(f"{BASE}/roleplay/turn", json=payload, headers=HEADERS_JSON, timeout=20)
        safe_print("roleplay/turn", r)
        if r.status_code != 200:
            ok = False
    except Exception as e:
        safe_print("roleplay/turn", e)
        ok = False

# 11. Tracking: start attempt
attempt_id = None
if tokens.get('access'):
    try:
        payload = {"exercise_type": "roleplay", "exercise_id": session_id or "manual_test", "extra_metadata": {}}
        headers = {**HEADERS_JSON, **AUTH_HDR}
        r = requests.post(f"{BASE}/tracking/attempts", json=payload, headers=headers, timeout=10)
        safe_print("tracking/start_attempt", r)
        if r.status_code in (200, 201):
            attempt_id = r.json().get('id')
        else:
            ok = False
    except Exception as e:
        safe_print("tracking/start_attempt", e)
        ok = False

# 12. Tracking: finish attempt
if attempt_id and tokens.get('access'):
    try:
        payload = {"status": "completed", "score": 0.8, "duration_seconds": 120}
        headers = {**HEADERS_JSON, **AUTH_HDR}
        r = requests.patch(f"{BASE}/tracking/attempts/{attempt_id}", json=payload, headers=headers, timeout=10)
        safe_print("tracking/finish_attempt", r)
        if r.status_code != 200:
            ok = False
    except Exception as e:
        safe_print("tracking/finish_attempt", e)
        ok = False

# 13. Tracking: log event
if tokens.get('access'):
    try:
        payload = {"event_type": "opened_chat", "feature": "chat", "extra_metadata": {"screen":"chat"}}
        headers = {**HEADERS_JSON, **AUTH_HDR}
        r = requests.post(f"{BASE}/tracking/events", json=payload, headers=headers, timeout=8)
        safe_print("tracking/log_event", r)
        if r.status_code not in (200,201):
            ok = False
    except Exception as e:
        safe_print("tracking/log_event", e)
        ok = False

# 14. Pronunciation test
try:
    r = requests.get(f"{BASE}/pronunciation/test", timeout=8)
    safe_print("pronunciation/test", r)
    if r.status_code != 200:
        ok = False
except Exception as e:
    safe_print("pronunciation/test", e)
    ok = False

print("\nSUMMARY: ", "OK" if ok else "SOME FAILURES")

if not ok:
    raise SystemExit(1)

