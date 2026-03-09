"""
Server-side instrumentation helper for lightweight, non-blocking activity tracking.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional

from db import SessionLocal
from models import ActivityEvent

_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="tracking")


def _write_event_sync(
    user_id: int,
    event: str,
    feature: Optional[str],
    details: Dict[str, Any],
) -> int:
    db = SessionLocal()
    try:
        record = ActivityEvent(
            user_id=user_id,
            event_type=event,
            feature=feature or str(details.get("feature") or "unknown"),
            extra_metadata=details or None,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record.id
    finally:
        db.close()


def _retry_write_sync(
    user_id: int,
    event: str,
    feature: Optional[str],
    details: Dict[str, Any],
    retries: int = 3,
) -> None:
    backoff = 0.25
    for attempt in range(1, retries + 1):
        try:
            event_id = _write_event_sync(user_id, event, feature, details)
            print(f"[track] event='{event}' user={user_id} id={event_id}", flush=True)
            return
        except Exception as exc:
            print(f"[track] attempt={attempt} failed for event={event} user={user_id}: {exc}", flush=True)
            if attempt == retries:
                print(f"[track] giving up after {attempt} attempts for event={event}", flush=True)
                return
            time.sleep(backoff)
            backoff *= 2


def track(user_id: Optional[int], event: str, feature: Optional[str] = None, **details: Any) -> None:
    """Queue a best-effort analytics write without blocking the request path."""
    if user_id is None:
        return

    payload = dict(details) if details else {}
    try:
        _EXECUTOR.submit(_retry_write_sync, int(user_id), event, feature, payload)
    except Exception as exc:
        print(f"[track] failed to queue event={event} user={user_id}: {exc}", flush=True)
