"""
Admin endpoints for viewing student analytics
Privacy-protected: NO message content, audio, or transcripts
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta, timezone
from typing import Optional

from db import get_db
from deps import require_admin
from models import User, UserRole, Role, ExerciseAttempt, ActivityEvent
from schemas import (
    StudentListItem, StudentSummary, GroupSummary,
    AdminDashboard, AdminPracticeLogItem, ExerciseAttemptOut, ActivityEventOut
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=AdminDashboard)
def get_dashboard(_ = Depends(require_admin), db: Session = Depends(get_db)):
    """
    Admin dashboard overview

    - Total students count
    - Active students (last 7 days)
    - Total exercise attempts
    - Average completion rate
    - Most popular features
    """
    # Get student role ID
    student_role = db.query(Role).filter(Role.name == "student").first()
    if not student_role:
        return AdminDashboard(
            total_students=0,
            active_students_7d=0,
            total_attempts=0,
            avg_completion_rate=0.0,
            popular_features={}
        )

    # Total students
    total_students = db.query(User).join(UserRole).filter(
        UserRole.role_id == student_role.id
    ).count()

    # Active students (last 7 days)
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    active_students_7d = db.query(func.count(func.distinct(ActivityEvent.user_id))).filter(
        ActivityEvent.timestamp >= week_ago
    ).scalar()

    # Total attempts
    total_attempts = db.query(ExerciseAttempt).count()

    # Completion rate
    completed = db.query(ExerciseAttempt).filter(
        ExerciseAttempt.finished_at.isnot(None)
    ).count()
    avg_completion_rate = (completed / total_attempts * 100) if total_attempts > 0 else 0.0

    # Popular features
    popular_features = dict(
        db.query(
            ActivityEvent.feature,
            func.count(ActivityEvent.id)
        ).group_by(ActivityEvent.feature).all()
    )

    return AdminDashboard(
        total_students=total_students,
        active_students_7d=active_students_7d or 0,
        total_attempts=total_attempts,
        avg_completion_rate=round(avg_completion_rate, 2),
        popular_features=popular_features
    )


@router.get("/students", response_model=list[StudentListItem])
def list_students(
    group_number: Optional[str] = Query(None, description="Filter by group number"),
    _ = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List all students with optional group filter

    - Shows basic student info
    - Can filter by group_number
    """
    # Get student role
    student_role = db.query(Role).filter(Role.name == "student").first()
    if not student_role:
        return []

    # Query students
    query = db.query(User).join(UserRole).filter(
        UserRole.role_id == student_role.id
    )

    if group_number:
        query = query.filter(User.group_number == group_number)

    students = query.order_by(User.created_at.desc()).all()

    return [
        StudentListItem(
            id=s.id,
            email=s.email,
            display_name=s.display_name,
            group_number=s.group_number,
            created_at=s.created_at,
            is_active=s.is_active
        )
        for s in students
    ]


@router.get("/practice-log", response_model=list[AdminPracticeLogItem])
def get_practice_log(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=500),
    student_id: Optional[int] = Query(None),
    feature: Optional[str] = Query(None),
    _ = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Recent practice metadata for teacher review.

    Shows who used each feature, scenario/prompt metadata, time, duration,
    message counts, word counts, and hint counts. It does not return message
    text, audio, or transcripts.
    """
    start = datetime.now(timezone.utc) - timedelta(days=days)
    query = (
        db.query(ExerciseAttempt, User)
        .join(User, User.id == ExerciseAttempt.user_id)
        .filter(ExerciseAttempt.started_at >= start)
    )
    if student_id is not None:
        query = query.filter(ExerciseAttempt.user_id == student_id)
    if feature:
        query = query.filter(ExerciseAttempt.exercise_type == feature)

    rows = query.order_by(ExerciseAttempt.started_at.desc()).limit(limit).all()
    result: list[AdminPracticeLogItem] = []
    for attempt, user in rows:
        metadata = attempt.extra_metadata or {}
        status = str(metadata.get("status") or ("completed" if attempt.finished_at else "started"))
        result.append(
            AdminPracticeLogItem(
                attempt_id=attempt.id,
                user_id=user.id,
                email=user.email,
                display_name=user.display_name,
                group_number=user.group_number,
                exercise_type=attempt.exercise_type,
                exercise_id=attempt.exercise_id,
                scenario_id=metadata.get("scenario_id"),
                scenario_title=metadata.get("scenario_title"),
                prompt_title=metadata.get("prompt_title"),
                started_at=attempt.started_at,
                finished_at=attempt.finished_at,
                duration_seconds=attempt.duration_seconds,
                message_count=int(metadata.get("message_count") or metadata.get("user_message_count") or 0),
                word_count=int(metadata.get("word_count") or metadata.get("user_message_words") or 0),
                hint_count=int(metadata.get("hints_used") or metadata.get("hint_count") or 0),
                status=status,
                last_activity_at=metadata.get("last_activity_at"),
            )
        )
    return result


@router.get("/students/{student_id}", response_model=StudentSummary)
def get_student_summary(
    student_id: int,
    _ = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get detailed summary for a specific student

    - Exercise attempt statistics
    - Average score
    - Time spent
    - Feature usage breakdown
    - Last activity timestamp

    Privacy: NO message content shown
    """
    user = db.get(User, student_id)
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")

    # Total attempts
    attempts = db.query(ExerciseAttempt).filter(
        ExerciseAttempt.user_id == student_id
    ).all()

    total_attempts = len(attempts)
    completed_attempts = sum(1 for a in attempts if a.finished_at is not None)

    # Average score
    scores = [a.score for a in attempts if a.score is not None]
    avg_score = sum(scores) / len(scores) if scores else None

    # Total minutes
    durations = [a.duration_seconds for a in attempts if a.duration_seconds is not None]
    total_minutes = sum(durations) // 60 if durations else 0

    # Feature usage
    feature_counts = db.query(
        ExerciseAttempt.exercise_type,
        func.count(ExerciseAttempt.id)
    ).filter(
        ExerciseAttempt.user_id == student_id
    ).group_by(ExerciseAttempt.exercise_type).all()

    features_used = dict(feature_counts)

    # Last activity
    last_event = db.query(ActivityEvent).filter(
        ActivityEvent.user_id == student_id
    ).order_by(ActivityEvent.timestamp.desc()).first()

    last_active = last_event.timestamp if last_event else None

    return StudentSummary(
        student_id=user.id,
        email=user.email,
        display_name=user.display_name,
        group_number=user.group_number,
        total_attempts=total_attempts,
        completed_attempts=completed_attempts,
        avg_score=round(avg_score, 2) if avg_score is not None else None,
        total_minutes=total_minutes,
        features_used=features_used,
        last_active=last_active
    )


@router.get("/students/{student_id}/attempts", response_model=list[ExerciseAttemptOut])
def get_student_attempts(
    student_id: int,
    limit: int = Query(50, ge=1, le=200),
    _ = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get recent exercise attempts for a student

    - Shows metadata only (NO content)
    - Ordered by most recent first
    - Configurable limit
    """
    attempts = db.query(ExerciseAttempt).filter(
        ExerciseAttempt.user_id == student_id
    ).order_by(ExerciseAttempt.started_at.desc()).limit(limit).all()

    return [
        ExerciseAttemptOut(
            id=a.id,
            user_id=a.user_id,
            exercise_type=a.exercise_type,
            exercise_id=a.exercise_id,
            started_at=a.started_at,
            finished_at=a.finished_at,
            duration_seconds=a.duration_seconds,
            score=a.score,
            passed=a.passed,
            extra_metadata=a.extra_metadata
        )
        for a in attempts
    ]


@router.get("/groups", response_model=list[GroupSummary])
def get_group_summaries(_ = Depends(require_admin), db: Session = Depends(get_db)):
    """
    Get statistics by group

    - Student count per group
    - Total attempts
    - Average score
    - Most used feature
    """
    # Get student role
    student_role = db.query(Role).filter(Role.name == "student").first()
    if not student_role:
        return []

    rows = (
        db.query(
            User.group_number,
            User.id.label("student_id"),
            ExerciseAttempt.id.label("attempt_id"),
            ExerciseAttempt.exercise_type,
            ExerciseAttempt.score,
        )
        .join(UserRole, UserRole.user_id == User.id)
        .outerjoin(ExerciseAttempt, ExerciseAttempt.user_id == User.id)
        .filter(
            UserRole.role_id == student_role.id,
            User.group_number.isnot(None),
        )
        .all()
    )

    grouped: dict[str, dict] = {}
    for group_num, student_id, attempt_id, exercise_type, score in rows:
        bucket = grouped.setdefault(
            group_num,
            {"students": set(), "attempts": 0, "scores": [], "features": {}},
        )
        bucket["students"].add(student_id)
        if attempt_id is None:
            continue
        bucket["attempts"] += 1
        if score is not None:
            bucket["scores"].append(score)
        if exercise_type:
            bucket["features"][exercise_type] = bucket["features"].get(exercise_type, 0) + 1

    summaries = []
    for group_num, bucket in grouped.items():
        scores = bucket["scores"]
        features = bucket["features"]
        avg_score = sum(scores) / len(scores) if scores else None
        most_used = max(features.items(), key=lambda item: item[1])[0] if features else None
        summaries.append(
            GroupSummary(
                group_number=group_num,
                student_count=len(bucket["students"]),
                total_attempts=bucket["attempts"],
                avg_score=round(avg_score, 2) if avg_score is not None else None,
                most_used_feature=most_used,
            )
        )

    return sorted(summaries, key=lambda summary: (-summary.student_count, summary.group_number.lower()))

