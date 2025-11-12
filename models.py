"""
Database models for authentication and student tracking
Enhanced for teacher/admin analytics with privacy protection
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey,
    UniqueConstraint, func, Text, Float, JSON
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """User accounts - both students and admins/teachers"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(120))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Student-specific fields (null for admin/teacher accounts)
    group_number = Column(String(50), nullable=True, index=True)  # For grouping students

    # Relationships
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    attempts = relationship("ExerciseAttempt", back_populates="user", cascade="all, delete-orphan")
    events = relationship("ActivityEvent", back_populates="user", cascade="all, delete-orphan")


class Role(Base):
    """User roles: 'admin' or 'student'"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)  # "admin", "student"

    users = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")


class UserRole(Base):
    """Many-to-many: users can have multiple roles"""
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")


class RefreshToken(Base):
    """JWT refresh tokens - server-side tracking for revocation"""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(Text, unique=True, nullable=False)  # Opaque UUID string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="tokens")


class ExerciseAttempt(Base):
    """
    Tracks student exercise attempts (chat, roleplay, pronunciation, etc.)
    NO content stored - only metadata for analytics
    """
    __tablename__ = "exercise_attempts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Exercise metadata
    exercise_type = Column(String(50), nullable=False, index=True)  # "chat", "roleplay", "pronunciation", "rag_qa"
    exercise_id = Column(String(100), nullable=True)  # e.g., scenario_id for roleplay

    # Timing
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Scoring (nullable for exercises without scores)
    score = Column(Float, nullable=True)  # 0.0 - 1.0 for percentage
    passed = Column(Boolean, nullable=True)

    # Extra metadata (JSON for flexibility) - renamed from 'metadata' to avoid SQLAlchemy reserved word
    extra_metadata = Column(JSON, nullable=True)  # e.g., {"corrections_count": 3, "hints_used": 1}

    # Privacy: NO message content, NO audio data, NO transcripts

    user = relationship("User", back_populates="attempts")

    def __repr__(self):
        return f"<ExerciseAttempt {self.exercise_type} by user {self.user_id}>"


class ActivityEvent(Base):
    """
    Lightweight activity tracking - which features students use
    For understanding feature adoption and engagement patterns
    """
    __tablename__ = "activity_events"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Event details
    event_type = Column(String(50), nullable=False, index=True)  # "opened_chat", "started_roleplay", "completed_pronunciation"
    feature = Column(String(50), nullable=False, index=True)  # "chat", "roleplay", "pronunciation", "rag_qa"
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Optional extra_metadata (e.g., {"scenario_id": "job_interview"})
    extra_metadata = Column(JSON, nullable=True)

    user = relationship("User", back_populates="events")

    def __repr__(self):
        return f"<ActivityEvent {self.event_type} by user {self.user_id}>"

