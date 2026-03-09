"""
Pydantic schemas for request and response validation.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterIn(BaseModel):
    """Student registration."""
    email: EmailStr
    password: str = Field(min_length=6)
    display_name: str = Field(min_length=2, max_length=120)
    group_number: Optional[str] = Field(default=None, max_length=50)


class LoginIn(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    """Refresh token request."""
    refresh_token: str


class MeOut(BaseModel):
    """Current user info."""
    id: int
    email: EmailStr
    display_name: Optional[str]
    group_number: Optional[str]
    roles: list[str]
    created_at: datetime


class StudentListItem(BaseModel):
    """Student in list view (for admin)."""
    id: int
    email: EmailStr
    display_name: Optional[str]
    group_number: Optional[str]
    created_at: datetime
    is_active: bool


class ExerciseAttemptIn(BaseModel):
    """Start an exercise attempt."""
    exercise_type: str = Field(..., description="chat, roleplay, pronunciation, rag_qa")
    exercise_id: Optional[str] = Field(None, description="e.g., scenario_id for roleplay")
    extra_metadata: Optional[dict] = None


class ExerciseAttemptUpdate(BaseModel):
    """Complete an exercise attempt."""
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    score: Optional[float] = Field(None, ge=0.0, le=100.0)
    passed: Optional[bool] = None
    extra_metadata: Optional[dict] = None
    status: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def map_legacy_fields(cls, data):
        if isinstance(data, dict) and "duration_seconds" not in data and "duration_sec" in data:
            data = dict(data)
            data["duration_seconds"] = data["duration_sec"]
        return data


class ExerciseAttemptOut(BaseModel):
    """Exercise attempt details."""
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


class TrackingAttemptCompatOut(BaseModel):
    """Compat response used by older Android tracking calls."""
    id: str
    exercise_id: Optional[str]
    exercise_type: str
    status: str
    score: Optional[float] = None
    duration_sec: Optional[int] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    user_id: Optional[int] = None
    duration_seconds: Optional[int] = None
    passed: Optional[bool] = None
    extra_metadata: Optional[dict] = None


class ActivityEventIn(BaseModel):
    """Log an activity event."""
    event_type: str = Field(..., description="opened_chat, started_roleplay, completed_pronunciation")
    feature: Optional[str] = Field(default=None, description="chat, roleplay, pronunciation, rag_qa")
    exercise_id: Optional[str] = None
    payload: Optional[dict] = None
    extra_metadata: Optional[dict] = None


class ActivityEventOut(BaseModel):
    """Activity event details."""
    id: int
    user_id: int
    event_type: str
    feature: str
    timestamp: datetime
    extra_metadata: Optional[dict]


class ActivityEventCompatOut(BaseModel):
    """Compat response used by older Android tracking calls."""
    id: int
    event_type: str
    ts: datetime
    feature: Optional[str] = None
    timestamp: Optional[datetime] = None
    extra_metadata: Optional[dict] = None


class ProgressTotalsOut(BaseModel):
    attempts: int = 0
    completed: int = 0
    avg_score: float = 0.0
    total_minutes: int = 0


class ProgressTypeStatsOut(BaseModel):
    attempts: int = 0
    avg_score: float = 0.0


class ProgressSummaryOut(BaseModel):
    totals: ProgressTotalsOut
    by_type: dict[str, ProgressTypeStatsOut]
    recent_attempts: list[TrackingAttemptCompatOut]


class StudentSummary(BaseModel):
    """Student progress summary for admin."""
    student_id: int
    email: EmailStr
    display_name: Optional[str]
    group_number: Optional[str]
    total_attempts: int
    completed_attempts: int
    avg_score: Optional[float]
    total_minutes: int
    features_used: dict[str, int]
    last_active: Optional[datetime]


class GroupSummary(BaseModel):
    """Group-level statistics."""
    group_number: str
    student_count: int
    total_attempts: int
    avg_score: Optional[float]
    most_used_feature: Optional[str]


class AdminDashboard(BaseModel):
    """Overall admin dashboard stats."""
    total_students: int
    active_students_7d: int
    total_attempts: int
    avg_completion_rate: float
    popular_features: dict[str, int]

