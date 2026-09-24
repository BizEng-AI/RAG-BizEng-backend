from __future__ import annotations

import importlib
import sys
import bcrypt
from datetime import datetime
from pathlib import Path

import pytest

import roleplay_session
from security import hash_password, needs_password_rehash, verify_password


def _reload_settings_module(monkeypatch, **env_vars):
    for key, value in env_vars.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)

    sys.modules.pop("settings", None)
    return importlib.import_module("settings")


def test_production_settings_require_real_jwt_secret(monkeypatch, tmp_path):
    settings = _reload_settings_module(
        monkeypatch,
        DATABASE_URL=f"sqlite:///{(tmp_path / 'prod.db').as_posix()}",
        JWT_SECRET="dev-secret-change-in-production",
        FLY_APP_NAME=None,
        ENVIRONMENT="production",
        APP_ENV=None,
    )

    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        settings.validate_runtime_settings()


def test_production_settings_accept_real_jwt_secret(monkeypatch, tmp_path):
    settings = _reload_settings_module(
        monkeypatch,
        DATABASE_URL=f"sqlite:///{(tmp_path / 'prod.db').as_posix()}",
        JWT_SECRET="this-is-a-realistic-production-secret-1234",
        FLY_APP_NAME=None,
        ENVIRONMENT="production",
        APP_ENV=None,
    )

    settings.validate_runtime_settings()


def test_roleplay_sessions_use_timezone_aware_timestamps():
    session = roleplay_session.create_session("transport_mode_comparison", student_name="Release Test")
    try:
        started_at = datetime.fromisoformat(session.started_at)
        updated_at = datetime.fromisoformat(session.updated_at)

        assert started_at.tzinfo is not None
        assert updated_at.tzinfo is not None

        session.add_turn("student", "Let's compare rail and air freight.")
        turn_timestamp = datetime.fromisoformat(session.dialogue_history[-1].timestamp)
        assert turn_timestamp.tzinfo is not None
    finally:
        roleplay_session.delete_session(session.session_id)


def test_roleplay_session_loader_returns_none_for_corrupt_file():
    corrupt_path = Path(roleplay_session.SESSIONS_DIR) / "corrupt-test-session.json"
    corrupt_path.write_text("{not valid json", encoding="utf-8")
    try:
        assert roleplay_session.load_session("corrupt-test-session") is None
        assert roleplay_session.list_user_sessions() is not None
    finally:
        corrupt_path.unlink(missing_ok=True)


def test_password_hashing_uses_argon2id_and_supports_verification():
    hashed = hash_password("password123")

    assert hashed.startswith("$argon2id$")
    assert verify_password("password123", hashed) is True
    assert verify_password("wrong-password", hashed) is False
    assert needs_password_rehash(hashed) is False


def test_legacy_bcrypt_passwords_still_verify_but_require_rehash():
    legacy_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")

    assert verify_password("password123", legacy_hash) is True
    assert needs_password_rehash(legacy_hash) is True


def test_malformed_legacy_password_hash_fails_closed():
    assert verify_password("password123", "not-a-supported-hash") is False
