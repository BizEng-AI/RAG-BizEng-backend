from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import User
from roleplay_session import delete_sessions_for_user
from security import verify_password


def _normalized_email(email: str) -> str:
    return email.strip().lower()


def authenticate_user_by_email_and_password(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(
        func.lower(func.trim(User.email)) == _normalized_email(email),
        User.is_active.is_(True),
    ).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def require_current_password(user: User, current_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect."
        )


def delete_user_account(db: Session, user: User) -> None:
    """
    Permanently delete a user account and all app-managed data we persist for it.
    """
    try:
        delete_sessions_for_user(user.id)
        db.delete(user)
        db.commit()
    except Exception:
        db.rollback()
        raise
