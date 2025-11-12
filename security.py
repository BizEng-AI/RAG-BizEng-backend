"""
Security utilities: password hashing, JWT token generation
Uses bcrypt directly (no passlib) to avoid compatibility issues
"""
import uuid
import bcrypt
from datetime import datetime, timezone
from jose import jwt

from settings import JWT_SECRET, JWT_ALG, ACCESS_EXPIRES, REFRESH_EXPIRES


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt directly

    Args:
        password: Plain text password

    Returns:
        Bcrypt hash as string
    """
    # Convert to bytes
    password_bytes = password.encode('utf-8')

    # Truncate to 72 bytes if necessary (bcrypt limit)
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Return as string
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its bcrypt hash

    Args:
        password: Plain text password to check
        hashed: Bcrypt hash string

    Returns:
        True if password matches, False otherwise
    """
    # Convert to bytes
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')

    # Truncate to 72 bytes if necessary (bcrypt limit)
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    # Verify
    return bcrypt.checkpw(password_bytes, hashed_bytes)


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

