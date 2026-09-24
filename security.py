"""
Security utilities: password hashing, refresh-token hashing, JWT token generation.
"""
import hashlib
import uuid

import bcrypt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerificationError, VerifyMismatchError
from datetime import datetime, timezone
from jose import jwt

from settings import (
    ACCESS_EXPIRES,
    JWT_ALG,
    JWT_SECRET,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    REFRESH_EXPIRES,
)


PASSWORD_HASHER = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)

PASSWORD_POLICY_HINT = (
    f"Password must be at least {PASSWORD_MIN_LENGTH} characters long and include both letters and numbers."
)


def validate_new_password(password: str) -> str:
    """
    Enforce the app's password policy for newly chosen passwords.
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(PASSWORD_POLICY_HINT)
    if len(password) > PASSWORD_MAX_LENGTH:
        raise ValueError(f"Password must be {PASSWORD_MAX_LENGTH} characters or fewer.")
    if not any(char.isalpha() for char in password):
        raise ValueError(PASSWORD_POLICY_HINT)
    if not any(char.isdigit() for char in password):
        raise ValueError(PASSWORD_POLICY_HINT)
    return password


def hash_password(password: str) -> str:
    """
    Hash a password using Argon2id.

    Args:
        password: Plain text password

    Returns:
        Argon2id hash as string
    """
    return PASSWORD_HASHER.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its stored hash.

    New hashes use Argon2id. Legacy bcrypt hashes remain supported so
    existing users are not locked out during rollout.

    Args:
        password: Plain text password to check
        hashed: Stored password hash string

    Returns:
        True if password matches, False otherwise
    """
    if not hashed:
        return False

    if hashed.startswith("$argon2id$"):
        try:
            return PASSWORD_HASHER.verify(hashed, password)
        except (InvalidHash, VerificationError, VerifyMismatchError):
            return False

    password_bytes = password.encode("utf-8")
    hashed_bytes = hashed.encode("utf-8")
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    try:
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (TypeError, ValueError):
        return False


def needs_password_rehash(hashed: str) -> bool:
    """
    Return True when a stored password should be upgraded.
    """
    if not hashed:
        return True

    if not hashed.startswith("$argon2id$"):
        return True

    try:
        return PASSWORD_HASHER.check_needs_rehash(hashed)
    except InvalidHash:
        return True


def hash_refresh_token(token: str) -> str:
    """
    Hash opaque refresh tokens before storing them at rest.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def make_access_token(sub: str, roles: list[str]) -> str:
    """
    Create JWT access token

    Args:
        sub: User email (subject)
        roles: List of role names ["student"] or ["admin", "student"]

    Returns:
        Encoded JWT token
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "roles": roles,
        "iat": int(now.timestamp()),
        "exp": int((now + ACCESS_EXPIRES).timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def make_refresh_token() -> str:
    """
    Create opaque refresh token (stored server-side)

    Returns:
        Random UUID hex string
    """
    return uuid.uuid4().hex


def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token

    Args:
        token: JWT token string

    Returns:
        Token payload dict

    Raises:
        JWTError: If token is invalid or expired
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])

