"""
Student tracking endpoints - log attempts and activity events
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from db import get_db
from deps import get_current_user, require_student
from models import User, ExerciseAttempt, ActivityEvent
from schemas import (
    ExerciseAttemptIn, ExerciseAttemptUpdate, ExerciseAttemptOut,
    ActivityEventIn, ActivityEventOut
)
from tracking import track

router = APIRouter(prefix="/tracking", tags=["tracking"])


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
    db: Session = Depends(get_db)
):
    """
    Get my exercise attempts history

    - Students can view their own progress
    - Ordered by most recent first
    """
    attempts = db.query(ExerciseAttempt).filter(
        ExerciseAttempt.user_id == user.id
    ).order_by(ExerciseAttempt.started_at.desc()).all()

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
