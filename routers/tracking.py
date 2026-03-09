"""
Student tracking endpoints - log attempts and activity events.
Includes compatibility responses used by the Android client.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from db import get_db
from deps import require_student
from models import ActivityEvent, ExerciseAttempt, User
from schemas import (
    ActivityEventCompatOut,
    ActivityEventIn,
    ExerciseAttemptIn,
    ExerciseAttemptOut,
    ExerciseAttemptUpdate,
    ProgressSummaryOut,
    ProgressTotalsOut,
    ProgressTypeStatsOut,
    TrackingAttemptCompatOut,
)
from tracking import track

router = APIRouter(prefix="/tracking", tags=["tracking"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)



def _infer_feature(exercise_id: Optional[str], payload: Optional[dict], explicit_feature: Optional[str]) -> str:
    if explicit_feature:
        return explicit_feature
    if payload and payload.get("exercise_type"):
        return str(payload["exercise_type"])
    normalized = (exercise_id or "").lower()
    if "roleplay" in normalized:
        return "roleplay"
    if "pron" in normalized:
        return "pronunciation"
    if "chat" in normalized:
        return "chat"
    if "rag" in normalized or "ask" in normalized:
        return "rag_qa"
    return "general"


def _attempt_status(attempt: ExerciseAttempt) -> str:
    metadata = attempt.extra_metadata or {}
    if isinstance(metadata, dict) and metadata.get("status"):
        return str(metadata["status"])
    if attempt.finished_at is None:
        return "started"
    if attempt.passed is False:
        return "abandoned"
    return "completed"



def _serialize_attempt_compat(attempt: ExerciseAttempt) -> dict:
    status = _attempt_status(attempt)
    return {
        "id": str(attempt.id),
        "user_id": attempt.user_id,
        "exercise_type": attempt.exercise_type,
        "exercise_id": attempt.exercise_id,
        "started_at": attempt.started_at,
        "finished_at": attempt.finished_at,
        "duration_seconds": attempt.duration_seconds,
        "duration_sec": attempt.duration_seconds,
        "score": attempt.score,
        "passed": attempt.passed,
        "extra_metadata": attempt.extra_metadata,
        "status": status,
    }



def _serialize_event_compat(event: ActivityEvent) -> dict:
    return {
        "id": event.id,
        "event_type": event.event_type,
        "ts": event.timestamp,
        "feature": event.feature,
        "timestamp": event.timestamp,
        "extra_metadata": event.extra_metadata,
    }



def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed



def _recent_attempts_query(db: Session, user_id: int, start: Optional[datetime], end: Optional[datetime]):
    query = db.query(ExerciseAttempt).filter(ExerciseAttempt.user_id == user_id)
    if start is not None:
        query = query.filter(ExerciseAttempt.started_at >= start)
    if end is not None:
        query = query.filter(ExerciseAttempt.started_at <= end)
    return query.order_by(ExerciseAttempt.started_at.desc())


# ============================================================================
# INTERNAL HELPERS (for exercise endpoints to call directly)
# ============================================================================


def create_attempt_internal(
    db: Session,
    user_id: int,
    exercise_type: str,
    exercise_id: str,
    extra_metadata: dict = None,
) -> ExerciseAttempt:
    attempt = ExerciseAttempt(
        user_id=user_id,
        exercise_type=exercise_type,
        exercise_id=exercise_id,
        started_at=_utcnow(),
        extra_metadata=extra_metadata,
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

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
    extra_metadata: dict = None,
) -> None:
    attempt = db.get(ExerciseAttempt, attempt_id)
    if not attempt:
        print(f"[tracking] warning: attempt {attempt_id} not found", flush=True)
        return

    attempt.finished_at = _utcnow()
    if duration_seconds is not None:
        attempt.duration_seconds = duration_seconds
    if score is not None:
        attempt.score = score
    if passed is not None:
        attempt.passed = passed
    if extra_metadata is not None:
        current = attempt.extra_metadata or {}
        current.update(extra_metadata)
        attempt.extra_metadata = current

    db.commit()

    try:
        track(
            attempt.user_id,
            "exercise_completed",
            feature=attempt.exercise_type,
            exercise_id=attempt.exercise_id,
            duration_seconds=duration_seconds,
            score=score,
        )
    except Exception:
        pass


@router.post("/attempts", response_model=TrackingAttemptCompatOut, status_code=201)
def start_attempt(
    payload: ExerciseAttemptIn,
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    attempt = ExerciseAttempt(
        user_id=user.id,
        exercise_type=payload.exercise_type,
        exercise_id=payload.exercise_id,
        extra_metadata=payload.extra_metadata,
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    try:
        track(user.id, "exercise_started", feature=attempt.exercise_type, exercise_id=attempt.exercise_id)
    except Exception:
        pass

    return _serialize_attempt_compat(attempt)


@router.patch("/attempts/{attempt_id}", response_model=TrackingAttemptCompatOut)
def finish_attempt(
    attempt_id: int,
    payload: ExerciseAttemptUpdate,
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    attempt = db.get(ExerciseAttempt, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your attempt")

    status_value = (payload.status or "").strip().lower()

    if payload.finished_at is not None:
        attempt.finished_at = payload.finished_at
    elif status_value in {"completed", "abandoned"} or any(
        value is not None for value in (payload.duration_seconds, payload.score, payload.passed)
    ):
        attempt.finished_at = _utcnow()

    if payload.duration_seconds is not None:
        attempt.duration_seconds = payload.duration_seconds
    if payload.score is not None:
        attempt.score = payload.score
    if payload.passed is not None:
        attempt.passed = payload.passed

    metadata = attempt.extra_metadata or {}
    if payload.extra_metadata:
        metadata.update(payload.extra_metadata)
    if status_value:
        metadata["status"] = status_value
        if status_value == "abandoned" and payload.passed is None:
            attempt.passed = False
    attempt.extra_metadata = metadata or None

    db.commit()
    db.refresh(attempt)

    try:
        event_name = "exercise_abandoned" if status_value == "abandoned" else "exercise_submitted"
        track(
            user.id,
            event_name,
            feature=attempt.exercise_type,
            exercise_id=attempt.exercise_id,
            score=attempt.score,
            duration_seconds=attempt.duration_seconds,
            status=status_value or _attempt_status(attempt),
        )
    except Exception:
        pass

    return _serialize_attempt_compat(attempt)


@router.post("/events", response_model=ActivityEventCompatOut, status_code=201)
def log_event(
    payload: ActivityEventIn,
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    feature = _infer_feature(payload.exercise_id, payload.payload, payload.feature)
    metadata = {}
    if payload.extra_metadata:
        metadata.update(payload.extra_metadata)
    if payload.payload:
        metadata.update(payload.payload)
    if payload.exercise_id:
        metadata.setdefault("exercise_id", payload.exercise_id)

    event = ActivityEvent(
        user_id=user.id,
        event_type=payload.event_type,
        feature=feature,
        extra_metadata=metadata or None,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    try:
        track(user.id, payload.event_type, feature=feature, **metadata)
    except Exception:
        pass

    return _serialize_event_compat(event)


@router.get("/my-progress", response_model=ProgressSummaryOut)
def get_my_progress(
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
    from_: Optional[str] = Query(default=None, alias="from"),
    to: Optional[str] = Query(default=None),
    days: Optional[int] = Query(default=None, ge=1, le=365),
):
    end = _parse_timestamp(to)
    if days is not None:
        start = _utcnow() - timedelta(days=days)
    else:
        start = _parse_timestamp(from_)
        if start is None and end is None:
            start = _utcnow() - timedelta(days=30)

    attempts = _recent_attempts_query(db, user.id, start, end).all()
    completed_attempts = [attempt for attempt in attempts if attempt.finished_at is not None]
    scored_attempts = [attempt.score for attempt in attempts if attempt.score is not None]

    by_type: dict[str, ProgressTypeStatsOut] = {}
    for exercise_type, count, avg_score in (
        db.query(
            ExerciseAttempt.exercise_type,
            func.count(ExerciseAttempt.id),
            func.avg(ExerciseAttempt.score),
        )
        .filter(ExerciseAttempt.user_id == user.id)
        .filter(ExerciseAttempt.started_at >= start if start is not None else True)
        .filter(ExerciseAttempt.started_at <= end if end is not None else True)
        .group_by(ExerciseAttempt.exercise_type)
        .all()
    ):
        by_type[exercise_type] = ProgressTypeStatsOut(
            attempts=int(count or 0),
            avg_score=float(avg_score or 0.0),
        )

    total_duration_seconds = sum(attempt.duration_seconds or 0 for attempt in attempts)
    recent_attempts = [_serialize_attempt_compat(attempt) for attempt in attempts[:10]]

    return ProgressSummaryOut(
        totals=ProgressTotalsOut(
            attempts=len(attempts),
            completed=len(completed_attempts),
            avg_score=float(sum(scored_attempts) / len(scored_attempts)) if scored_attempts else 0.0,
            total_minutes=total_duration_seconds // 60,
        ),
        by_type=by_type,
        recent_attempts=recent_attempts,
    )


@router.get("/my-attempts", response_model=list[ExerciseAttemptOut])
def get_my_attempts(
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    days: int = 30,
):
    safe_limit = max(1, min(limit, 200))
    safe_offset = max(0, offset)
    safe_days = max(1, min(int(days), 365))
    start = _utcnow() - timedelta(days=safe_days)

    attempts = (
        db.query(ExerciseAttempt)
        .filter(ExerciseAttempt.user_id == user.id, ExerciseAttempt.started_at >= start)
        .order_by(ExerciseAttempt.started_at.desc())
        .offset(safe_offset)
        .limit(safe_limit)
        .all()
    )

    return [
        ExerciseAttemptOut(
            id=attempt.id,
            user_id=attempt.user_id,
            exercise_type=attempt.exercise_type,
            exercise_id=attempt.exercise_id,
            started_at=attempt.started_at,
            finished_at=attempt.finished_at,
            duration_seconds=attempt.duration_seconds,
            score=attempt.score,
            passed=attempt.passed,
            extra_metadata=attempt.extra_metadata,
        )
        for attempt in attempts
    ]


@router.get("/summary")
def get_my_summary(
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
    days: int = 30,
):
    safe_days = max(1, min(int(days), 365))
    start = _utcnow() - timedelta(days=safe_days)

    total_exercises = int(
        db.query(func.count(ExerciseAttempt.id))
        .filter(ExerciseAttempt.user_id == user.id, ExerciseAttempt.started_at >= start)
        .scalar()
        or 0
    )
    pronunciation_count = int(
        db.query(func.count(ExerciseAttempt.id))
        .filter(
            ExerciseAttempt.user_id == user.id,
            ExerciseAttempt.exercise_type == "pronunciation",
            ExerciseAttempt.started_at >= start,
        )
        .scalar()
        or 0
    )
    chat_count = int(
        db.query(func.count(ExerciseAttempt.id))
        .filter(
            ExerciseAttempt.user_id == user.id,
            ExerciseAttempt.exercise_type == "chat",
            ExerciseAttempt.started_at >= start,
        )
        .scalar()
        or 0
    )
    roleplay_count = int(
        db.query(func.count(ExerciseAttempt.id))
        .filter(
            ExerciseAttempt.user_id == user.id,
            ExerciseAttempt.exercise_type == "roleplay",
            ExerciseAttempt.started_at >= start,
        )
        .scalar()
        or 0
    )
    total_duration = int(
        db.query(func.coalesce(func.sum(ExerciseAttempt.duration_seconds), 0))
        .filter(ExerciseAttempt.user_id == user.id, ExerciseAttempt.started_at >= start)
        .scalar()
        or 0
    )
    avg_pron = (
        db.query(func.avg(ExerciseAttempt.score))
        .filter(
            ExerciseAttempt.user_id == user.id,
            ExerciseAttempt.exercise_type == "pronunciation",
            ExerciseAttempt.started_at >= start,
        )
        .scalar()
    )

    return {
        "user_id": user.id,
        "email": user.email,
        "group_number": getattr(user, "group_number", None),
        "total_exercises": total_exercises,
        "pronunciation_count": pronunciation_count,
        "chat_count": chat_count,
        "roleplay_count": roleplay_count,
        "total_duration_seconds": total_duration,
        "avg_pronunciation_score": float(avg_pron) if avg_pron is not None else None,
    }


