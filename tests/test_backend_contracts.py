from __future__ import annotations

import uuid


def _register_user(client, suffix: str):
    email = f"student-{suffix}@example.com"
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": "Test Student",
            "group_number": "A1",
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    token = payload["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


def test_health_does_not_require_qdrant(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["checks"]["database"] == "ok"
    assert payload["checks"]["vector_store"] == "not_probed"


def test_auth_profile_roundtrip(client):
    token, headers = _register_user(client, uuid.uuid4().hex[:8])
    assert token

    response = client.get("/me", headers=headers)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["email"].startswith("student-")
    assert "student" in payload["roles"]


def test_register_duplicate_email_returns_conflict(client):
    suffix = uuid.uuid4().hex[:8]
    email = f"student-{suffix}@example.com"

    first = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": "Test Student",
            "group_number": "A1",
        },
    )
    assert first.status_code == 201, first.text

    second = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": "Test Student",
            "group_number": "A1",
        },
    )
    assert second.status_code == 409, second.text
    assert second.json()["detail"] == "Email already registered"


def test_login_accepts_email_case_and_space_variants(client):
    suffix = uuid.uuid4().hex[:8]
    email = f"student-{suffix}@example.com"

    registered = client.post(
        "/auth/register",
        json={
            "email": email.upper(),
            "password": "password123",
            "display_name": "Test Student",
            "group_number": "A1",
        },
    )
    assert registered.status_code == 201, registered.text

    login = client.post(
        "/auth/login",
        json={"email": f"  {email.lower()}  ", "password": "password123"},
    )

    assert login.status_code == 200, login.text
    assert login.json()["access_token"]


def test_register_rejects_weak_password(client):
    response = client.post(
        "/auth/register",
        json={
            "email": f"student-{uuid.uuid4().hex[:8]}@example.com",
            "password": "short7",
            "display_name": "Test Student",
            "group_number": "A1",
        },
    )
    assert response.status_code == 422, response.text
    assert "Password must be at least 10 characters long and include both letters and numbers." in response.text


def test_register_rate_limit_returns_429(client, monkeypatch):
    import routers.auth as auth_module

    monkeypatch.setattr(auth_module, "AUTH_REGISTER_IP_LIMIT", 1)
    monkeypatch.setattr(auth_module, "AUTH_REGISTER_EMAIL_LIMIT", 10)

    first = client.post(
        "/auth/register",
        json={
            "email": f"student-{uuid.uuid4().hex[:8]}@example.com",
            "password": "password123",
            "display_name": "Test Student",
            "group_number": "A1",
        },
    )
    assert first.status_code == 201, first.text

    second = client.post(
        "/auth/register",
        json={
            "email": f"student-{uuid.uuid4().hex[:8]}@example.com",
            "password": "password123",
            "display_name": "Test Student",
            "group_number": "A1",
        },
    )
    assert second.status_code == 429, second.text
    assert "Too many sign-up attempts" in second.json()["detail"]


def test_register_hashes_passwords_and_refresh_tokens(client):
    suffix = uuid.uuid4().hex[:8]
    email = f"student-{suffix}@example.com"

    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": "Test Student",
            "group_number": "A1",
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()

    from db import SessionLocal
    from models import RefreshToken, User
    from security import hash_refresh_token

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        assert user is not None
        assert user.password_hash.startswith("$argon2id$")

        refresh_row = (
            db.query(RefreshToken)
            .filter(RefreshToken.user_id == user.id)
            .order_by(RefreshToken.id.desc())
            .first()
        )
        assert refresh_row is not None
        assert refresh_row.token == hash_refresh_token(payload["refresh_token"])
        assert refresh_row.token != payload["refresh_token"]
    finally:
        db.close()


def test_refresh_accepts_legacy_plaintext_refresh_tokens(client):
    suffix = uuid.uuid4().hex[:8]
    email = f"student-{suffix}@example.com"

    registered = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": "Test Student",
            "group_number": "A1",
        },
    )
    assert registered.status_code == 201, registered.text
    issued_refresh_token = registered.json()["refresh_token"]

    from db import SessionLocal
    from models import RefreshToken, User
    from security import hash_refresh_token

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        assert user is not None

        legacy_row = (
            db.query(RefreshToken)
            .filter(RefreshToken.user_id == user.id)
            .order_by(RefreshToken.id.desc())
            .first()
        )
        assert legacy_row is not None
        legacy_row.token = issued_refresh_token
        db.commit()
        legacy_row_id = legacy_row.id
        user_id = user.id
    finally:
        db.close()

    refreshed = client.post("/auth/refresh", json={"refresh_token": issued_refresh_token})
    assert refreshed.status_code == 200, refreshed.text
    rotated_payload = refreshed.json()
    assert rotated_payload["refresh_token"] != issued_refresh_token

    db = SessionLocal()
    try:
        revoked_row = db.get(RefreshToken, legacy_row_id)
        assert revoked_row is not None
        assert revoked_row.revoked is True

        rotated_row = (
            db.query(RefreshToken)
            .filter(RefreshToken.user_id == user_id)
            .order_by(RefreshToken.id.desc())
            .first()
        )
        assert rotated_row is not None
        assert rotated_row.token == hash_refresh_token(rotated_payload["refresh_token"])
    finally:
        db.close()


def test_login_rate_limit_returns_429_after_repeated_failures(client, monkeypatch):
    import routers.auth as auth_module

    suffix = uuid.uuid4().hex[:8]
    email = f"student-{suffix}@example.com"
    registered = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": "Test Student",
            "group_number": "A1",
        },
    )
    assert registered.status_code == 201, registered.text

    monkeypatch.setattr(auth_module, "AUTH_LOGIN_FAILURE_EMAIL_LIMIT", 2)
    monkeypatch.setattr(auth_module, "AUTH_LOGIN_FAILURE_IP_LIMIT", 10)

    first = client.post("/auth/login", json={"email": email, "password": "wrong-pass"})
    second = client.post("/auth/login", json={"email": email, "password": "wrong-pass"})
    third = client.post("/auth/login", json={"email": email, "password": "wrong-pass"})

    assert first.status_code == 401, first.text
    assert second.status_code == 401, second.text
    assert third.status_code == 429, third.text
    assert "Too many failed login attempts" in third.json()["detail"]


def test_tracking_attempts_android_contract(client):
    _, headers = _register_user(client, uuid.uuid4().hex[:8])

    start = client.post(
        "/tracking/attempts",
        headers=headers,
        json={"exercise_id": "chat_session", "exercise_type": "chat"},
    )
    assert start.status_code == 201, start.text
    started_payload = start.json()
    assert isinstance(started_payload["id"], str)
    assert started_payload["status"] == "started"
    assert started_payload["exercise_id"] == "chat_session"
    assert started_payload["started_at"]

    update = client.patch(
        f"/tracking/attempts/{started_payload['id']}",
        headers=headers,
        json={"status": "completed", "score": 82.5, "duration_sec": 12},
    )
    assert update.status_code == 200, update.text
    updated_payload = update.json()
    assert updated_payload["status"] == "completed"
    assert updated_payload["duration_sec"] == 12
    assert updated_payload["score"] == 82.5


def test_tracking_events_and_progress_contract(client):
    _, headers = _register_user(client, uuid.uuid4().hex[:8])

    start = client.post(
        "/tracking/attempts",
        headers=headers,
        json={"exercise_id": "chat_session", "exercise_type": "chat"},
    )
    assert start.status_code == 201, start.text

    event = client.post(
        "/tracking/events",
        headers=headers,
        json={
            "exercise_id": "chat_session",
            "event_type": "opened",
            "payload": {"exercise_type": "chat"},
        },
    )
    assert event.status_code == 201, event.text
    event_payload = event.json()
    assert event_payload["event_type"] == "opened"
    assert "ts" in event_payload

    progress = client.get("/tracking/my-progress?days=30", headers=headers)
    assert progress.status_code == 200, progress.text
    progress_payload = progress.json()
    assert set(progress_payload.keys()) == {"totals", "by_type", "recent_attempts"}
    assert progress_payload["totals"]["attempts"] >= 1
    assert "chat" in progress_payload["by_type"]
    assert isinstance(progress_payload["recent_attempts"], list)
    assert progress_payload["recent_attempts"][0]["started_at"]


def test_account_deletion_requires_current_password_and_removes_data(client):
    suffix = uuid.uuid4().hex[:8]
    email = f"student-{suffix}@example.com"
    registered = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": "Delete Me",
            "group_number": "A1",
        },
    )
    assert registered.status_code == 201, registered.text
    token = registered.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    roleplay = client.post(
        "/roleplay/start",
        json={
            "scenario_id": "transport_mode_comparison",
            "student_name": "Delete Me",
            "use_rag": False,
        },
        headers=headers,
    )
    assert roleplay.status_code == 200, roleplay.text
    session_id = roleplay.json()["session_id"]

    wrong_password = client.request(
        "DELETE",
        "/me",
        headers=headers,
        json={"current_password": "not-it", "confirm_phrase": "DELETE"},
    )
    assert wrong_password.status_code == 401, wrong_password.text

    deleted = client.request(
        "DELETE",
        "/me",
        headers=headers,
        json={"current_password": "password123", "confirm_phrase": "DELETE"},
    )
    assert deleted.status_code == 204, deleted.text

    me_after_delete = client.get("/me", headers=headers)
    assert me_after_delete.status_code == 401, me_after_delete.text

    from db import SessionLocal
    from models import User
    import roleplay_session

    db = SessionLocal()
    try:
        assert db.query(User).filter(User.email == email).first() is None
        assert roleplay_session.load_session(session_id) is None
    finally:
        db.close()


def test_public_legal_pages_are_available(client):
    privacy = client.get("/legal/privacy")
    assert privacy.status_code == 200, privacy.text
    assert "Privacy Policy" in privacy.text

    deletion_page = client.get("/legal/account-deletion")
    assert deletion_page.status_code == 200, deletion_page.text
    assert "Delete your BizEng Chatbot account" in deletion_page.text


def test_roleplay_start_accepts_use_rag_flag(client):
    _, headers = _register_user(client, uuid.uuid4().hex[:8])
    response = client.post(
        "/roleplay/start",
        json={
            "scenario_id": "transport_mode_comparison",
            "student_name": "Test Student",
            "use_rag": True,
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert isinstance(payload["session_id"], str)
    assert payload["scenario_title"] == "Transport Mode Comparison"
    assert payload["current_stage"]


def test_stt_rejects_non_audio_upload(client):
    _, headers = _register_user(client, uuid.uuid4().hex[:8])
    response = client.post(
        "/stt",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        headers=headers,
    )
    assert response.status_code == 415, response.text
    assert "Unsupported content type" in response.json()["detail"]


def test_stt_rejects_empty_audio_upload(client):
    _, headers = _register_user(client, uuid.uuid4().hex[:8])
    response = client.post(
        "/stt",
        files={"file": ("empty.wav", b"", "audio/wav")},
        headers=headers,
    )
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Uploaded audio file is empty"


def test_roleplay_turn_contract_returns_compact_correction_shape(client, monkeypatch):
    import roleplay_api

    _, headers = _register_user(client, uuid.uuid4().hex[:8])

    def fake_process_turn(_session, _message):
        return {
            "ai_message": "Thanks. Could you add one more detail about delivery risk?",
            "correction": {
                "error_type": "grammar",
                "original": "we discussed with client",
                "corrected": "we discussed this with the client",
                "explanation": "Use the object and article for natural phrasing.",
                "priority": "medium",
            },
            "current_stage": "development",
            "is_completed": False,
            "feedback": None,
        }

    monkeypatch.setattr(roleplay_api.engine, "process_turn", fake_process_turn)

    started = client.post(
        "/roleplay/start",
        json={"scenario_id": "international_business_meeting", "use_rag": True},
        headers=headers,
    )
    assert started.status_code == 200, started.text
    session_id = started.json()["session_id"]

    turn = client.post(
        "/roleplay/turn",
        json={"session_id": session_id, "message": "we discussed with client"},
        headers=headers,
    )
    assert turn.status_code == 200, turn.text
    payload = turn.json()
    assert payload["ai_message"]
    assert payload["correction"]["has_errors"] is True
    assert isinstance(payload["correction"]["errors"], list)
    assert payload["correction"]["errors"][0]["type"] == "grammar"
    assert "feedback" in payload


def test_chat_contract_relevance_gated_rag_fallback(client, app_module, monkeypatch):
    class _Message:
        content = "Use a clear agenda, confirm priorities, and summarize action owners."

    class _Choice:
        message = _Message()

    class _Response:
        choices = [_Choice()]

    class _Completions:
        @staticmethod
        def create(**_kwargs):
            return _Response()

    class _Chat:
        completions = _Completions()

    class _Client:
        chat = _Chat()

    monkeypatch.setattr(app_module, "ENABLE_TOPIC_RETRIEVAL", True)
    monkeypatch.setattr(
        app_module,
        "_retrieve_grounding",
        lambda query, k, max_context_chars: ("Meeting note context", ["lesson_3_handout"]),
    )
    monkeypatch.setattr(app_module, "get_chat_client", lambda: _Client())

    _, headers = _register_user(client, uuid.uuid4().hex[:8])
    response = client.post(
        "/chat",
        json={
            "messages": [{"role": "user", "content": "How should I open a contract negotiation meeting?"}],
            "k": 3,
            "maxContextChars": 800,
            "use_rag": True,
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["answer"]
    assert payload["sources"] == ["lesson_3_handout"]


def test_chat_requires_auth(client):
    response = client.post(
        "/chat",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "use_rag": False,
        },
    )
    assert response.status_code == 401, response.text
    assert response.json()["detail"] == "Missing authentication token"


def test_usage_me_returns_daily_remaining_budget(client):
    _, headers = _register_user(client, uuid.uuid4().hex[:8])

    response = client.get("/usage/me", headers=headers)

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ai"]["window"] == "day"
    assert payload["ai"]["limit"] >= 1
    assert payload["ai"]["used"] == 0
    assert payload["ai"]["remaining"] == payload["ai"]["limit"]
    assert payload["ai"]["unit_costs"]["chat"] >= 1
    assert payload["speech"]["window"] == "day"
    assert payload["speech"]["used_seconds"] == 0
    assert payload["speech"]["remaining_seconds"] == payload["speech"]["limit_seconds"]


def test_ask_returns_429_when_usage_budget_is_exceeded(client, app_module, monkeypatch):
    import usage_limits

    class _Message:
        content = "Keep the agenda short and confirm next steps."

    class _Choice:
        message = _Message()

    class _Response:
        choices = [_Choice()]

    class _Completions:
        @staticmethod
        def create(**_kwargs):
            return _Response()

    class _Chat:
        completions = _Completions()

    class _Client:
        chat = _Chat()

    token, headers = _register_user(client, uuid.uuid4().hex[:8])
    assert token

    monkeypatch.setattr(app_module, "get_chat_client", lambda: _Client())
    monkeypatch.setattr(usage_limits, "AI_DAILY_UNIT_LIMIT", 1)
    monkeypatch.setattr(usage_limits, "AI_MONTHLY_UNIT_LIMIT", 10)
    monkeypatch.setattr(usage_limits, "AI_GLOBAL_MONTHLY_UNIT_LIMIT", 1000)

    first = client.post("/ask", json={"query": "How do I start a meeting?"}, headers=headers)
    assert first.status_code == 200, first.text

    second = client.post("/ask", json={"query": "How do I end a meeting?"}, headers=headers)
    assert second.status_code == 429, second.text
    assert "Daily AI limit reached" in second.json()["detail"]


def test_ready_uses_local_retrieval_when_qdrant_is_unavailable(client, app_module, monkeypatch):
    monkeypatch.setattr(
        app_module,
        "qdrant_health",
        lambda: {
            "configured": True,
            "collection": "bizeng",
            "ok": False,
            "error": "UnexpectedResponse: 404",
        },
    )
    monkeypatch.setattr(
        app_module,
        "local_retrieval_health",
        lambda: {
            "ok": True,
            "backend": "local_lexical",
            "files": 5,
            "chunks": 120,
        },
    )

    response = client.get("/ready")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["checks"]["vector_store"]["ok"] is False
    assert payload["checks"]["local_store"]["ok"] is True
    assert payload["checks"]["preferred_retrieval_backend"] == "local_lexical"


def test_pronunciation_word_ipa_always_has_fallback(app_module):
    known = app_module.get_word_ipa("education", phonemes=None)
    unknown = app_module.get_word_ipa("coordination", phonemes=None)
    punctuated = app_module.get_word_ipa("delivery,", phonemes=None)

    assert isinstance(known, str) and known
    assert isinstance(unknown, str) and unknown
    assert isinstance(punctuated, str) and punctuated
