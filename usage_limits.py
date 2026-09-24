"""
DB-backed usage caps for paid AI features.

These defaults are intentionally conservative for a small pilot so one user,
or a sudden burst of traffic, cannot unexpectedly exhaust the Azure/OpenAI budget.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import AIUsageEvent
from settings import (
    AI_5HOUR_UNIT_LIMIT,
    AI_DAILY_UNIT_LIMIT,
    AI_GLOBAL_5HOUR_UNIT_LIMIT,
    AI_GLOBAL_MONTHLY_UNIT_LIMIT,
    AI_GLOBAL_WEEKLY_UNIT_LIMIT,
    AI_MONTHLY_UNIT_LIMIT,
    AI_SPEECH_GLOBAL_5HOUR_SECONDS_LIMIT,
    AI_SPEECH_GLOBAL_MONTHLY_SECONDS_LIMIT,
    AI_SPEECH_GLOBAL_WEEKLY_SECONDS_LIMIT,
    AI_SPEECH_USER_5HOUR_SECONDS_LIMIT,
    AI_SPEECH_USER_DAILY_SECONDS_LIMIT,
    AI_SPEECH_USER_MONTHLY_SECONDS_LIMIT,
    AI_SPEECH_USER_WEEKLY_SECONDS_LIMIT,
    AI_USAGE_LIMITS_ENABLED,
    AI_WEEKLY_UNIT_LIMIT,
)

ROUTE_UNIT_COSTS: dict[str, int] = {
    "ask": 1,
    "chat": 2,
    "roleplay_turn": 2,
    "roleplay_hint": 1,
    "stt": 2,
    "tts": 1,
    "pronunciation_assess": 1,
    "pronunciation_quick_check": 1,
}

ROUTE_LABELS: dict[str, str] = {
    "ask": "coaching questions",
    "chat": "chat messages",
    "roleplay_turn": "roleplay turns",
    "roleplay_hint": "roleplay hints",
    "stt": "speech-to-text requests",
    "tts": "text-to-speech requests",
    "pronunciation_assess": "pronunciation assessments",
    "pronunciation_quick_check": "pronunciation quick checks",
}

SPEECH_ROUTES = {"pronunciation_assess", "pronunciation_quick_check", "stt"}


def _utc_now() -> datetime:
    # SQLite stores CURRENT_TIMESTAMP in UTC, so we normalize to a naive UTC timestamp for comparisons.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _day_start(now: datetime) -> datetime:
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _five_hour_start(now: datetime) -> datetime:
    return now - timedelta(hours=5)


def _week_start(now: datetime) -> datetime:
    return _day_start(now) - timedelta(days=now.weekday())


def _next_day_start(now: datetime) -> datetime:
    return _day_start(now) + timedelta(days=1)


def _next_week_start(now: datetime) -> datetime:
    return _week_start(now) + timedelta(days=7)


def _month_start(now: datetime) -> datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _next_month_start(now: datetime) -> datetime:
    if now.month == 12:
        return now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)


def _sum_units(db: Session, *, since: datetime, user_id: Optional[int] = None) -> int:
    query = db.query(func.coalesce(func.sum(AIUsageEvent.units), 0)).filter(AIUsageEvent.created_at >= since)
    if user_id is not None:
        query = query.filter(AIUsageEvent.user_id == user_id)
    return int(query.scalar() or 0)


def _sum_speech_seconds(db: Session, *, since: datetime, user_id: Optional[int] = None) -> float:
    query = db.query(AIUsageEvent.extra_metadata).filter(
        AIUsageEvent.created_at >= since,
        AIUsageEvent.route.in_(SPEECH_ROUTES),
    )
    if user_id is not None:
        query = query.filter(AIUsageEvent.user_id == user_id)

    total = 0.0
    for (metadata,) in query.all():
        if not isinstance(metadata, dict):
            continue
        try:
            total += max(0.0, float(metadata.get("audio_seconds") or 0))
        except (TypeError, ValueError):
            continue
    return total


def _limit_error(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)


def get_user_daily_usage_summary(db: Session, *, user_id: int) -> dict:
    now = _utc_now()
    day_start = _day_start(now)
    next_day = _next_day_start(now)
    used_today = _sum_units(db, since=day_start, user_id=user_id)
    speech_seconds_today = _sum_speech_seconds(db, since=day_start, user_id=user_id)
    ai_remaining = max(0, AI_DAILY_UNIT_LIMIT - used_today) if AI_DAILY_UNIT_LIMIT > 0 else None
    speech_remaining = (
        max(0.0, AI_SPEECH_USER_DAILY_SECONDS_LIMIT - speech_seconds_today)
        if AI_SPEECH_USER_DAILY_SECONDS_LIMIT > 0
        else None
    )

    return {
        "ai": {
            "window": "day",
            "limit": AI_DAILY_UNIT_LIMIT if AI_DAILY_UNIT_LIMIT > 0 else None,
            "used": used_today,
            "remaining": ai_remaining,
            "reset_at": f"{next_day.isoformat()}Z",
            "unit_costs": ROUTE_UNIT_COSTS,
            "route_labels": ROUTE_LABELS,
        },
        "speech": {
            "window": "day",
            "limit_seconds": AI_SPEECH_USER_DAILY_SECONDS_LIMIT
            if AI_SPEECH_USER_DAILY_SECONDS_LIMIT > 0
            else None,
            "used_seconds": speech_seconds_today,
            "remaining_seconds": speech_remaining,
            "reset_at": f"{next_day.isoformat()}Z",
        },
    }


def consume_ai_units(
    db: Session,
    *,
    user_id: int,
    route: str,
    extra_metadata: Optional[dict] = None,
) -> None:
    if not AI_USAGE_LIMITS_ENABLED:
        return

    units = ROUTE_UNIT_COSTS.get(route)
    if units is None:
        raise RuntimeError(f"Unknown AI usage route: {route}")

    now = _utc_now()
    five_hour_start = _five_hour_start(now)
    day_start = _day_start(now)
    next_day = _next_day_start(now)
    week_start = _week_start(now)
    next_week = _next_week_start(now)
    month_start = _month_start(now)
    next_month = _next_month_start(now)
    route_label = ROUTE_LABELS.get(route, route.replace("_", " "))

    used_last_five_hours = _sum_units(db, since=five_hour_start, user_id=user_id)
    if AI_5HOUR_UNIT_LIMIT > 0 and used_last_five_hours + units > AI_5HOUR_UNIT_LIMIT:
        raise _limit_error(
            f"Five-hour AI limit reached for {route_label}. Try again after some recent usage leaves the 5-hour window."
        )

    used_today = _sum_units(db, since=day_start, user_id=user_id)
    if AI_DAILY_UNIT_LIMIT > 0 and used_today + units > AI_DAILY_UNIT_LIMIT:
        raise _limit_error(
            f"Daily AI limit reached for {route_label}. Try again after {next_day.isoformat()}Z."
        )

    used_this_week = _sum_units(db, since=week_start, user_id=user_id)
    if AI_WEEKLY_UNIT_LIMIT > 0 and used_this_week + units > AI_WEEKLY_UNIT_LIMIT:
        raise _limit_error(
            f"Weekly AI limit reached for {route_label}. Try again after {next_week.date().isoformat()}."
        )

    used_this_month = _sum_units(db, since=month_start, user_id=user_id)
    if AI_MONTHLY_UNIT_LIMIT > 0 and used_this_month + units > AI_MONTHLY_UNIT_LIMIT:
        raise _limit_error(
            f"Monthly AI limit reached for {route_label}. Try again after {next_month.date().isoformat()}."
        )

    global_five_hour_units = _sum_units(db, since=five_hour_start)
    if AI_GLOBAL_5HOUR_UNIT_LIMIT > 0 and global_five_hour_units + units > AI_GLOBAL_5HOUR_UNIT_LIMIT:
        raise _limit_error(
            "The class five-hour AI safety limit is reached. Try again after some recent usage leaves the 5-hour window."
        )

    global_week_units = _sum_units(db, since=week_start)
    if AI_GLOBAL_WEEKLY_UNIT_LIMIT > 0 and global_week_units + units > AI_GLOBAL_WEEKLY_UNIT_LIMIT:
        raise _limit_error(
            f"The class weekly AI safety limit is reached. Try again after {next_week.date().isoformat()}."
        )

    global_month_units = _sum_units(db, since=month_start)
    if AI_GLOBAL_MONTHLY_UNIT_LIMIT > 0 and global_month_units + units > AI_GLOBAL_MONTHLY_UNIT_LIMIT:
        raise _limit_error(
            f"The class monthly AI safety limit is reached. Try again after {next_month.date().isoformat()}."
        )

    metadata = extra_metadata or {}
    speech_seconds = 0.0
    if route in SPEECH_ROUTES:
        try:
            speech_seconds = max(0.0, float(metadata.get("audio_seconds") or 0))
        except (TypeError, ValueError):
            speech_seconds = 0.0

        if AI_SPEECH_USER_5HOUR_SECONDS_LIMIT > 0:
            user_five_hour_seconds = _sum_speech_seconds(db, since=five_hour_start, user_id=user_id)
            if user_five_hour_seconds + speech_seconds > AI_SPEECH_USER_5HOUR_SECONDS_LIMIT:
                raise _limit_error(
                    "Five-hour speech practice limit reached. Try again after a short break or use chat/roleplay practice."
                )

        if AI_SPEECH_USER_DAILY_SECONDS_LIMIT > 0:
            user_day_seconds = _sum_speech_seconds(db, since=day_start, user_id=user_id)
            if user_day_seconds + speech_seconds > AI_SPEECH_USER_DAILY_SECONDS_LIMIT:
                raise _limit_error(
                    "Daily speech practice limit reached. Try again tomorrow or use chat/roleplay practice."
                )

        if AI_SPEECH_USER_WEEKLY_SECONDS_LIMIT > 0:
            user_week_seconds = _sum_speech_seconds(db, since=week_start, user_id=user_id)
            if user_week_seconds + speech_seconds > AI_SPEECH_USER_WEEKLY_SECONDS_LIMIT:
                raise _limit_error(
                    f"Weekly speech practice limit reached. Try again after {next_week.date().isoformat()}."
                )

        if AI_SPEECH_USER_MONTHLY_SECONDS_LIMIT > 0:
            user_month_seconds = _sum_speech_seconds(db, since=month_start, user_id=user_id)
            if user_month_seconds + speech_seconds > AI_SPEECH_USER_MONTHLY_SECONDS_LIMIT:
                raise _limit_error(
                    f"Monthly speech practice limit reached. Try again after {next_month.date().isoformat()}."
                )

        if AI_SPEECH_GLOBAL_5HOUR_SECONDS_LIMIT > 0:
            global_five_hour_seconds = _sum_speech_seconds(db, since=five_hour_start)
            if global_five_hour_seconds + speech_seconds > AI_SPEECH_GLOBAL_5HOUR_SECONDS_LIMIT:
                raise _limit_error(
                    "The class five-hour speech safety limit is reached. Try again after some recent recordings leave the 5-hour window."
                )

        if AI_SPEECH_GLOBAL_WEEKLY_SECONDS_LIMIT > 0:
            global_week_seconds = _sum_speech_seconds(db, since=week_start)
            if global_week_seconds + speech_seconds > AI_SPEECH_GLOBAL_WEEKLY_SECONDS_LIMIT:
                raise _limit_error(
                    f"The class weekly speech safety limit is reached. Try again after {next_week.date().isoformat()}."
                )

        if AI_SPEECH_GLOBAL_MONTHLY_SECONDS_LIMIT > 0:
            global_month_seconds = _sum_speech_seconds(db, since=month_start)
            if global_month_seconds + speech_seconds > AI_SPEECH_GLOBAL_MONTHLY_SECONDS_LIMIT:
                raise _limit_error(
                    f"The class monthly speech free-tier budget is exhausted. Try again after {next_month.date().isoformat()}."
                )

    db.add(
        AIUsageEvent(
            user_id=user_id,
            route=route,
            units=units,
            extra_metadata=metadata or None,
        )
    )
    db.commit()
