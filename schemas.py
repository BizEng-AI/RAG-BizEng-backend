"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class RegisterIn(BaseModel):
    """Student registration"""
    email: EmailStr
    password: str = Field(min_length=6)
    display_name: str = Field(min_length=2, max_length=120)
    group_number: Optional[str] = Field(default=None, max_length=50)


class LoginIn(BaseModel):
    """Login request"""
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    """Refresh token request"""
    refresh_token: str


# ============================================================================
# USER SCHEMAS
# ============================================================================

class MeOut(BaseModel):
    """Current user info"""
    id: int
    email: EmailStr
    display_name: Optional[str]
    group_number: Optional[str]
    roles: list[str]
    created_at: datetime


class StudentListItem(BaseModel):
    """Student in list view (for admin)"""
    id: int
    email: EmailStr
    display_name: Optional[str]
    group_number: Optional[str]
    created_at: datetime
    is_active: bool


# ============================================================================
# EXERCISE TRACKING SCHEMAS
# ============================================================================

class ExerciseAttemptIn(BaseModel):
    """Start an exercise attempt"""
    exercise_type: str = Field(..., description="chat, roleplay, pronunciation, rag_qa")
    exercise_id: Optional[str] = Field(None, description="e.g., scenario_id for roleplay")
    extra_metadata: Optional[dict] = None


class ExerciseAttemptUpdate(BaseModel):
    """Complete an exercise attempt"""
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    score: Optional[float] = Field(None, ge=0.0, le=1.0)
    passed: Optional[bool] = None
    extra_metadata: Optional[dict] = None


class ExerciseAttemptOut(BaseModel):
    """Exercise attempt details"""
    id: int
    user_id: int
    exercise_type: str
    exercise_id: Optional[str]
    started_at: datetime
    finished_at: Optional[datetime]
    duration_seconds: Optional[int]
    score: Optional[float]
    passed: Optional[bool]
    extra_metadata: Optional[dict]


class ActivityEventIn(BaseModel):
    """Log an activity event"""
    event_type: str = Field(..., description="opened_chat, started_roleplay, completed_pronunciation")
    feature: str = Field(..., description="chat, roleplay, pronunciation, rag_qa")
    extra_metadata: Optional[dict] = None


class ActivityEventOut(BaseModel):
    """Activity event details"""
    id: int
    user_id: int
    event_type: str
    feature: str
    timestamp: datetime
    extra_metadata: Optional[dict]


# ============================================================================
# ADMIN ANALYTICS SCHEMAS
# ============================================================================

class StudentSummary(BaseModel):
    """Student progress summary for admin"""
    student_id: int
    email: EmailStr
    display_name: Optional[str]
    group_number: Optional[str]

    # Aggregate stats
    total_attempts: int
    completed_attempts: int
    avg_score: Optional[float]
    total_minutes: int

    # Feature usage
    features_used: dict[str, int]  # {"chat": 5, "roleplay": 3}

    # Recent activity
    last_active: Optional[datetime]


class GroupSummary(BaseModel):
    """Group-level statistics"""
    group_number: str
    student_count: int
    total_attempts: int
    avg_score: Optional[float]
    most_used_feature: Optional[str]


class AdminDashboard(BaseModel):
    """Overall admin dashboard stats"""
    total_students: int
    active_students_7d: int
    total_attempts: int
    avg_completion_rate: float
    popular_features: dict[str, int]

