"""
Authentication endpoints: register, login, refresh, logout
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db import get_db
from models import User, Role, UserRole, RefreshToken
from schemas import RegisterIn, LoginIn, TokenOut, RefreshIn
from security import hash_password, verify_password, make_access_token, make_refresh_token
from tracking import track

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    """
    Register a new student account

    - Email must be unique
    - Password minimum 6 characters
    - Automatically assigned 'student' role
    - Returns access + refresh tokens
    """
    # Check if email already exists
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        group_number=payload.group_number
    )
    db.add(user)
    db.flush()  # Get user.id

    # Assign 'student' role (create role if doesn't exist)
    student_role = db.query(Role).filter(Role.name == "student").first()
    if not student_role:
        student_role = Role(name="student")
        db.add(student_role)
        db.flush()

    db.add(UserRole(user_id=user.id, role_id=student_role.id))

    # Generate tokens
    roles = ["student"]
    access_token = make_access_token(user.email, roles)
    refresh_token = make_refresh_token()

    db.add(RefreshToken(user_id=user.id, token=refresh_token))
    db.commit()

    # Instrument: user registered
    try:
        track(user.id, "user_registered", feature="auth", email=payload.email)
    except Exception:
        pass

    return TokenOut(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    """
    Login with email and password

    - Returns new access + refresh tokens
    - Previous tokens remain valid until expiry
    """
    # Find user
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Get user roles
    role_names = [ur.role.name for ur in user.roles]

    # Generate tokens
    access_token = make_access_token(user.email, role_names)
    refresh_token = make_refresh_token()

    db.add(RefreshToken(user_id=user.id, token=refresh_token))
    db.commit()

    # Instrument: user login
    try:
        track(user.id, "user_login", feature="auth")
    except Exception:
        pass

    return TokenOut(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenOut)
def refresh_token(payload: RefreshIn, db: Session = Depends(get_db)):
    """
    Get new access token using refresh token

    - Rotates refresh token (old one is revoked)
    - Returns new access + refresh tokens
    - Refresh tokens expire after 30 days
    """
    from datetime import datetime, timezone
    from settings import REFRESH_EXPIRES

    # Find refresh token
    token_row = db.query(RefreshToken).filter(
        RefreshToken.token == payload.refresh_token,
        RefreshToken.revoked.is_(False)
    ).first()

    if not token_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Check if token has expired (30 days)
    now = datetime.now(timezone.utc)
    token_age = now - token_row.created_at.replace(tzinfo=timezone.utc)
    if token_age > REFRESH_EXPIRES:
        # Mark as revoked and reject
        token_row.revoked = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )

    # Get user and roles
    user = db.get(User, token_row.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    role_names = [ur.role.name for ur in user.roles]

    # Generate new tokens
    access_token = make_access_token(user.email, role_names)
    new_refresh_token = make_refresh_token()

    # Revoke old refresh token (rotation)
    token_row.revoked = True

    # Create new refresh token
    db.add(RefreshToken(user_id=user.id, token=new_refresh_token))
    db.commit()

    # Instrument: token rotated
    try:
        track(user.id, "refresh_rotated", feature="auth")
    except Exception:
        pass

    return TokenOut(
        access_token=access_token,
        refresh_token=new_refresh_token
    )


@router.post("/logout")
def logout(payload: RefreshIn, db: Session = Depends(get_db)):
    """
    Logout by revoking refresh token

    - Access token remains valid until expiry (stateless)
    - Refresh token is immediately revoked
    """
    token_row = db.query(RefreshToken).filter(
        RefreshToken.token == payload.refresh_token
    ).first()

    if token_row:
        token_row.revoked = True
        db.commit()

        # Instrument: logout
        try:
            track(token_row.user_id, "user_logout", feature="auth")
        except Exception:
            pass

    return {"message": "Logged out successfully"}
