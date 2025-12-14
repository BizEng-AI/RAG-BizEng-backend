"""
Student tracking endpoints - log attempts and activity events
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func

from db import get_db
from deps import get_current_user, require_student
from models import User, ExerciseAttempt, ActivityEvent
from schemas import (
    ExerciseAttemptIn, ExerciseAttemptUpdate, ExerciseAttemptOut,
    ActivityEventIn, ActivityEventOut
)
from tracking import track

router = APIRouter(prefix="/tracking", tags=["tracking"])


# ============================================================================
# INTERNAL HELPERS (for exercise endpoints to call directly)
# ============================================================================

def create_attempt_internal(
    db: Session,
    user_id: int,
    exercise_type: str,
    exercise_id: str,
    extra_metadata: dict = None
) -> ExerciseAttempt:
    """
    Internal helper to create an exercise attempt without going through HTTP endpoint.
    Used by chat/roleplay/pronunciation endpoints to record attempts.

    Args:
        db: Database session
        user_id: ID of user doing the exercise
        exercise_type: "chat", "roleplay", or "pronunciation"
        exercise_id: Unique identifier for this specific exercise instance
        extra_metadata: Optional additional data

    Returns:
        Created ExerciseAttempt object
    """
    attempt = ExerciseAttempt(
        user_id=user_id,
        exercise_type=exercise_type,
        exercise_id=exercise_id,
        started_at=datetime.utcnow(),
        extra_metadata=extra_metadata
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    # Instrument
    try:
        track(user_id, "exercise_started", feature=exercise_type, exercise_id=exercise_id)
    except Exception:
        pass

    return attempt


def finish_attempt_internal(
    db: Session,
    attempt_id: int,
    duration_seconds: int = None,
    score: float = None,
    passed: bool = None,
    extra_metadata: dict = None
) -> None:
    """
    Internal helper to finish an exercise attempt.
    Used by chat/roleplay/pronunciation endpoints to record completion.

    Args:
        db: Database session
        attempt_id: ID of the attempt to finish
        duration_seconds: How long the exercise took
        score: Score achieved (0-100 for pronunciation, null for chat/roleplay)
        passed: Whether the user passed (optional)
        extra_metadata: Additional completion data
    """
    attempt = db.get(ExerciseAttempt, attempt_id)

    if not attempt:
        print(f"[tracking] Warning: Attempt {attempt_id} not found", flush=True)
        return

    # Update fields
    attempt.finished_at = datetime.utcnow()

    if duration_seconds is not None:
        attempt.duration_seconds = duration_seconds

    if score is not None:
        attempt.score = score

    if passed is not None:
        attempt.passed = passed

    if extra_metadata is not None:
        if attempt.extra_metadata:
            attempt.extra_metadata.update(extra_metadata)
        else:
            attempt.extra_metadata = extra_metadata

    db.commit()

    # Instrument completion
    try:
        track(
            attempt.user_id,
            "exercise_completed",
            feature=attempt.exercise_type,
            exercise_id=attempt.exercise_id,
            duration_seconds=duration_seconds,
            score=score
        )
    except Exception:
        pass


@router.post("/attempts", response_model=ExerciseAttemptOut, status_code=201)
def start_attempt(
    payload: ExerciseAttemptIn,
    user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Start a new exercise attempt

    - Called when student begins an exercise
    - Returns attempt ID for later completion

    Privacy: NO content stored, only metadata
    """
    attempt = ExerciseAttempt(
        user_id=user.id,
        exercise_type=payload.exercise_type,
        exercise_id=payload.exercise_id,
        extra_metadata=payload.extra_metadata
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    # instrument
    try:
        track(user.id, "exercise_started", feature=attempt.exercise_type, exercise_id=attempt.exercise_id)
    except Exception:
        pass

    return ExerciseAttemptOut(
        id=attempt.id,
        user_id=attempt.user_id,
        exercise_type=attempt.exercise_type,
        exercise_id=attempt.exercise_id,
        started_at=attempt.started_at,
        finished_at=attempt.finished_at,
        duration_seconds=attempt.duration_seconds,
        score=attempt.score,
        passed=attempt.passed,
        extra_metadata=attempt.extra_metadata
    )


@router.patch("/attempts/{attempt_id}", response_model=ExerciseAttemptOut)
def finish_attempt(
    attempt_id: int,
    payload: ExerciseAttemptUpdate,
    user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Complete an exercise attempt with final score/duration

    - Updates attempt with completion data
    - Only owner can update their attempts
    """
    attempt = db.get(ExerciseAttempt, attempt_id)

    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your attempt")

    # Update fields
    if payload.finished_at:
        attempt.finished_at = payload.finished_at
    else:
        attempt.finished_at = datetime.utcnow()

    if payload.duration_seconds is not None:
        attempt.duration_seconds = payload.duration_seconds

    if payload.score is not None:
        attempt.score = payload.score

    if payload.passed is not None:
        attempt.passed = payload.passed

    if payload.extra_metadata is not None:
        attempt.extra_metadata = payload.extra_metadata
    db.commit()
    db.refresh(attempt)

    # instrument completion
    try:
        track(user.id, "exercise_submitted", feature=attempt.exercise_type,
              exercise_id=attempt.exercise_id, score=attempt.score, duration_seconds=attempt.duration_seconds)
    except Exception:
        pass

    return ExerciseAttemptOut(
        id=attempt.id,
        user_id=attempt.user_id,
        exercise_type=attempt.exercise_type,
        exercise_id=attempt.exercise_id,
        started_at=attempt.started_at,
        finished_at=attempt.finished_at,
        duration_seconds=attempt.duration_seconds,
        score=attempt.score,
        passed=attempt.passed,
        extra_metadata=attempt.extra_metadata
    )


@router.post("/events", response_model=ActivityEventOut, status_code=201)
def log_event(
    payload: ActivityEventIn,
    user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Log an activity event

    - Lightweight tracking of feature usage
    - Examples: "opened_chat", "started_roleplay", "completed_pronunciation"

    Privacy: NO content stored, only event type and timestamp
    """
    event = ActivityEvent(
        user_id=user.id,
        event_type=payload.event_type,
        feature=payload.feature,
        extra_metadata=payload.extra_metadata
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    # instrument (also track) - duplicate to tracking table for consistency
    try:
        track(user.id, payload.event_type, feature=payload.feature, **(payload.extra_metadata or {}))
    except Exception:
        pass

    return ActivityEventOut(
        id=event.id,
        user_id=event.user_id,
        event_type=event.event_type,
        feature=event.feature,
        timestamp=event.timestamp,
        extra_metadata=event.extra_metadata
    )


@router.get("/my-attempts", response_model=list[ExerciseAttemptOut])
def get_my_attempts(
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    days: int = 30,
):
    """
    Get my exercise attempts history with optional pagination and day filter

    - Students can view their own progress
    - Ordered by most recent first
    - Query params: limit, offset, days (last N days)
    """
    # sanitize inputs
    safe_limit = max(1, min(limit, 200))
    safe_offset = max(0, offset)
    try:
        days = int(days)
    except Exception:
        days = 30
    days = max(1, min(days, 365))

    start = None
    if days:
        start = datetime.utcnow() - timedelta(days=days)

    q = db.query(ExerciseAttempt).filter(ExerciseAttempt.user_id == user.id)
    if start:
        q = q.filter(ExerciseAttempt.started_at >= start)

    attempts = q.order_by(ExerciseAttempt.started_at.desc()).offset(safe_offset).limit(safe_limit).all()

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


# Note: GET /tracking/attempts conflicts with POST /tracking/attempts
# Android should use /tracking/my-attempts instead


@router.get("/summary")
def get_my_summary(
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
    days: int = 30,
):
    """
    Return compact summary of the current user's activity over the last `days` days.
    """
    try:
        days = int(days)
    except Exception:
        days = 30
    days = max(1, min(days, 365))
    start = datetime.utcnow() - timedelta(days=days)

    total_exercises = int(db.query(func.count(ExerciseAttempt.id)).filter(
        ExerciseAttempt.user_id == user.id,
        ExerciseAttempt.started_at >= start
    ).scalar() or 0)

    pronunciation_count = int(db.query(func.count(ExerciseAttempt.id)).filter(
        ExerciseAttempt.user_id == user.id,
        ExerciseAttempt.exercise_type == 'pronunciation',
        ExerciseAttempt.started_at >= start
    ).scalar() or 0)

    chat_count = int(db.query(func.count(ExerciseAttempt.id)).filter(
        ExerciseAttempt.user_id == user.id,
        ExerciseAttempt.exercise_type == 'chat',
        ExerciseAttempt.started_at >= start
    ).scalar() or 0)

    roleplay_count = int(db.query(func.count(ExerciseAttempt.id)).filter(
        ExerciseAttempt.user_id == user.id,
        ExerciseAttempt.exercise_type == 'roleplay',
        ExerciseAttempt.started_at >= start
    ).scalar() or 0)

    # Sum duration_seconds (nullable)
    total_duration = db.query(func.coalesce(func.sum(ExerciseAttempt.duration_seconds), 0)).filter(
        ExerciseAttempt.user_id == user.id,
        ExerciseAttempt.started_at >= start
    ).scalar() or 0
    total_duration = int(total_duration)

    # Average pronunciation score (score is 0..1 in model)
    avg_pron = db.query(func.avg(ExerciseAttempt.score)).filter(
        ExerciseAttempt.user_id == user.id,
        ExerciseAttempt.exercise_type == 'pronunciation',
        ExerciseAttempt.started_at >= start
    ).scalar()
    avg_pron = float(avg_pron) if avg_pron is not None else None

    return {
        "user_id": user.id,
        "email": user.email,
        "group_number": getattr(user, 'group_number', None),
        "total_exercises": total_exercises,
        "pronunciation_count": pronunciation_count,
        "chat_count": chat_count,
        "roleplay_count": roleplay_count,
        "total_duration_seconds": total_duration,
        "avg_pronunciation_score": avg_pron
    }
