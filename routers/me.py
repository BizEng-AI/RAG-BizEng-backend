"""
User profile endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db
from deps import get_current_user
from models import User, UserRole
from schemas import MeOut

router = APIRouter(prefix="/me", tags=["profile"])


@router.get("", response_model=MeOut)
def get_my_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile

    - Requires authentication
    - Returns user info + roles
    """
    # Get user roles
    roles = [
        ur.role.name
        for ur in db.query(UserRole).filter(UserRole.user_id == user.id).all()
    ]

    return MeOut(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        group_number=user.group_number,
        roles=roles,
        created_at=user.created_at
    )

