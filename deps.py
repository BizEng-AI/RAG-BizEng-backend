"""
FastAPI dependencies for authentication and RBAC
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from jose import JWTError

from db import get_db
from models import User, UserRole
from security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token

    Raises:
        HTTPException: 401 if token is missing, invalid, or user not found
    """
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token"
        )

    token = creds.credentials

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Verify token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong token type"
        )

    # Get user from database
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = db.query(User).filter(
        User.email == email,
        User.is_active.is_(True)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return user


def require_roles(*required: str):
    """
    Dependency factory for RBAC

    Usage:
        @app.get("/admin/dashboard")
        def dashboard(user = Depends(require_roles("admin"))):
            ...

    Args:
        *required: Role names that are allowed (any match grants access)

    Returns:
        Dependency function that returns User or raises 403
    """
    def wrapper(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Get user's role names
        user_roles = db.query(UserRole).filter(
            UserRole.user_id == user.id
        ).all()

        user_role_names = {ur.role.name for ur in user_roles}

        # Check if user has any of the required roles
        if not any(role in user_role_names for role in required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(required)}"
            )

        return user

    return wrapper


# Common dependencies
require_admin = require_roles("admin")
require_student = require_roles("student", "admin")  # Admins can act as students

