# ...new file...
"""
Server-side instrumentation helper for lightweight, non-blocking activity tracking.

Provides:
- async def track(user_id: int|None, event: str, feature: str | None = None, **details)
  -> fire-and-forget, retries on error, writes to activity_events table (JSON metadata)

Design:
- Uses SQLAlchemy SessionLocal from db.py (synchronous DB) but performs DB writes in a thread
  via asyncio.to_thread so the FastAPI event loop isn't blocked.
- Retries with exponential backoff (3 attempts) on transient errors.
- Minimal: does not raise; logs errors to stdout.
"""
from __future__ import annotations
import asyncio
import json
import time
from typing import Any, Dict, Optional

from db import SessionLocal
from models import ActivityEvent


async def _write_event_to_db(user_id: Optional[int], event: str, feature: Optional[str], details: Dict[str, Any]):
    """Blocking DB write wrapped by asyncio.to_thread"""
    def _sync_write():
        db = SessionLocal()
        try:
            ev = ActivityEvent(
                user_id=user_id if user_id is not None else -1,
                event_type=event,
                feature=feature or (details.get("feature") if details else None) or "unknown",
                extra_metadata=details or None,
            )
            db.add(ev)
            db.commit()
            # refresh to get id/timestamp if caller ever needs it
            db.refresh(ev)
            return ev.id
        finally:
            db.close()

    return await asyncio.to_thread(_sync_write)


async def _retry_write(user_id: Optional[int], event: str, feature: Optional[str], details: Dict[str, Any], retries: int = 3):
    backoff = 0.5
    for attempt in range(1, retries + 1):
        try:
            ev_id = await _write_event_to_db(user_id, event, feature, details)
            print(f"[track] event='{event}' user={user_id} id={ev_id}", flush=True)
            return ev_id
        except Exception as e:
            print(f"[track] attempt={attempt} failed for event={event} user={user_id}: {e}", flush=True)
            if attempt == retries:
                print(f"[track] giving up after {attempt} attempts for event={event}", flush=True)
                return None
            await asyncio.sleep(backoff)
            backoff *= 2


def track(user_id: Optional[int], event: str, feature: Optional[str] = None, **details: Any) -> None:
    """
    Public helper: schedule a non-blocking write of an activity event.

    Usage:
        track(user.id, "user_login")
        track(user.id, "exercise_started", feature="roleplay", exercise_id="job_interview")

    Notes:
    - This function is fire-and-forget: it schedules a background task and returns immediately.
    - It is safe to call from synchronous endpoints as well as async endpoints.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # not in an event loop (e.g., startup scripts) -> run write synchronously in a thread
        asyncio.run(_retry_write(user_id, event, feature, details))
        return

    # schedule background task
    loop.create_task(_retry_write(user_id, event, feature, details))

