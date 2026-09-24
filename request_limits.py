"""
Small in-memory sliding-window request throttles.

This is enough for a single low-volume Fly instance. If you later scale to
multiple instances, move these counters into Redis or the primary database.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request

_WINDOWS: dict[str, deque[float]] = defaultdict(deque)
_LOCK = Lock()


def _bucket(scope: str, key: str) -> str:
    return f"{scope}:{key}"


def _prune(entries: deque[float], *, now: float, window_seconds: int) -> None:
    cutoff = now - window_seconds
    while entries and entries[0] <= cutoff:
        entries.popleft()


def count_hits(scope: str, key: str, *, window_seconds: int) -> int:
    now = time.monotonic()
    bucket = _bucket(scope, key)
    with _LOCK:
        entries = _WINDOWS.get(bucket)
        if not entries:
            return 0
        _prune(entries, now=now, window_seconds=window_seconds)
        if not entries:
            _WINDOWS.pop(bucket, None)
            return 0
        return len(entries)


def record_hit(scope: str, key: str, *, window_seconds: int) -> int:
    now = time.monotonic()
    bucket = _bucket(scope, key)
    with _LOCK:
        entries = _WINDOWS[bucket]
        _prune(entries, now=now, window_seconds=window_seconds)
        entries.append(now)
        return len(entries)


def reset_key(scope: str, key: str) -> None:
    with _LOCK:
        _WINDOWS.pop(_bucket(scope, key), None)


def clear_all_limits() -> None:
    with _LOCK:
        _WINDOWS.clear()


def extract_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        candidate = forwarded_for.split(",")[0].strip()
        if candidate:
            return candidate
    if request.client and request.client.host:
        return request.client.host
    return "unknown"
