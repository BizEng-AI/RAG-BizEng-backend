"""
Security utilities: password hashing, JWT token generation
"""
import uuid
import warnings
from datetime import datetime, timezone
from jose import jwt

# Suppress bcrypt version warning during import
warnings.filterwarnings('ignore', message='.*bcrypt version.*')

# Use CryptContext for better compatibility
from passlib.context import CryptContext

from settings import JWT_SECRET, JWT_ALG, ACCESS_EXPIRES, REFRESH_EXPIRES

# Create password context with bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Note: bcrypt has a 72-byte limit. We truncate if necessary.
    This is safe because 72 bytes is ~72 characters (for ASCII),
    which is already a very long password.
    """
    # Truncate to 72 bytes if necessary (bcrypt limit)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        password = password_bytes.decode('utf-8', errors='ignore')

    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its hash

    Note: Truncates to 72 bytes to match hash_password behavior
    """
    # Truncate to 72 bytes if necessary (bcrypt limit)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        password = password_bytes.decode('utf-8', errors='ignore')

    return pwd_context.verify(password, hashed)


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

