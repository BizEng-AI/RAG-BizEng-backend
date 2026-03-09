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
