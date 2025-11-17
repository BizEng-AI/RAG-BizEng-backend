"""
Admin monitoring endpoints for dashboard feeds (admin-only).
Returns small chart-ready arrays like [{"day":"YYYY-MM-DD","value":N}] or simple key-count maps.
Caching: simple in-memory TTL cache (60s) to avoid DB load.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from db import get_db
from deps import require_admin
from models import ActivityEvent, ExerciseAttempt, User, Role, RefreshToken, UserRole

router = APIRouter(prefix="/admin/monitor", tags=["admin-monitor"])

# Simple in-memory TTL cache
_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 60  # seconds
CACHE_HEADER = {"Cache-Control": "public, max-age=60, s-maxage=60"}


def _sanitize_days(days: int) -> int:
    try:
        value = int(days)
    except (TypeError, ValueError):
        value = 30
    return max(7, min(value, 180))


def _coerce_int(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return int(value)
    if isinstance(value, (float, int)):
        return int(value)
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_float(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _cached(key: str, compute_func):
    now = datetime.utcnow().timestamp()
    e = _CACHE.get(key)
    if e and now - e["ts"] < CACHE_TTL:
        return e["value"]
    val = compute_func()
    _CACHE[key] = {"ts": now, "value": val}
    return val


def _init_day_buckets(days: int = 30):
    today = datetime.utcnow().date()
    start = today - timedelta(days=days - 1)
    buckets = {(start + timedelta(days=i)).isoformat(): 0 for i in range(days)}
    return start, buckets


def _group_counts_by_day(queryset, date_attr_name: str, days: int = 30):
    """Helper to return list of {day, value} for last `days` days."""
    today = datetime.utcnow().date()
    start = today - timedelta(days=days - 1)

    # Build histogram dict with zeros
    out = { (start + timedelta(days=i)).isoformat(): 0 for i in range(days) }

    # Aggregate
    rows = (
        queryset
        .with_entities(func.date(getattr(queryset.column_descriptions[0]['entity'], date_attr_name)).label('day'), func.count().label('cnt'))
        .filter(getattr(queryset.column_descriptions[0]['entity'], date_attr_name) >= start)
        .group_by(func.date(getattr(queryset.column_descriptions[0]['entity'], date_attr_name)))
        .all()
    )

    # rows may be list of (day, cnt)
    for r in rows:
        try:
            d = r[0].isoformat() if hasattr(r[0], 'isoformat') else str(r[0])
            out[d] = int(r[1])
        except Exception:
            continue

    return [{"day": k, "value": out[k]} for k in sorted(out.keys())]


@router.get("/activity_events")
def get_activity_events(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Return counts of activity events per day for last 30 days."""
    def compute():
        try:
            # Using text SQL for simplicity and compatibility
            sql = text("""
                SELECT DATE(timestamp) as day, COUNT(*) as cnt
                FROM activity_events
                WHERE timestamp >= (CURRENT_DATE - INTERVAL '29 days')
                GROUP BY DATE(timestamp)
            """)
            res = db.execute(sql).fetchall()
            # build dict
            today = datetime.utcnow().date()
            start = today - timedelta(days=29)
            out = { (start + timedelta(days=i)).isoformat(): 0 for i in range(30) }
            for row in res:
                d = row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0])
                out[d] = int(row[1])
            return [{"day": k, "value": out[k]} for k in sorted(out.keys())]
        except Exception as e:
            # fallback empty
            return []

    payload = _cached("activity_events", compute)
    return JSONResponse(content=payload, headers=CACHE_HEADER)


@router.get("/exercise_attempts")
def get_exercise_attempts(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Return counts of exercise attempts per day for last 30 days."""
    def compute():
        try:
            sql = text("""
                SELECT DATE(started_at) as day, COUNT(*) as cnt
                FROM exercise_attempts
                WHERE started_at >= (CURRENT_DATE - INTERVAL '29 days')
                GROUP BY DATE(started_at)
            """)
            res = db.execute(sql).fetchall()
            today = datetime.utcnow().date(); start = today - timedelta(days=29)
            out = { (start + timedelta(days=i)).isoformat(): 0 for i in range(30) }
            for row in res:
                d = row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0])
                out[d] = int(row[1])
            return [{"day": k, "value": out[k]} for k in sorted(out.keys())]
        except Exception:
            return []

    payload = _cached("exercise_attempts", compute)
    return JSONResponse(content=payload, headers=CACHE_HEADER)


@router.get("/attempts_daily")
def attempts_daily(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Attempt counts per day for the last 30 days."""
    def compute():
        try:
            sql = text(
                """
                SELECT DATE(started_at) AS day, COUNT(*) AS cnt
                FROM exercise_attempts
                WHERE started_at >= (CURRENT_DATE - INTERVAL '29 days')
                GROUP BY DATE(started_at)
                ORDER BY DATE(started_at)
                """
            )
            rows = db.execute(sql).fetchall()
            _, buckets = _init_day_buckets()
            for row in rows:
                day = row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0])
                buckets[day] = int(row[1])
            return [{"day": day, "count": buckets[day]} for day in sorted(buckets.keys())]
        except Exception as e:
            print(f"[attempts_daily] Error: {e}", flush=True)
            return []

    payload = _cached("attempts_daily", compute)
    return JSONResponse(content=payload, headers=CACHE_HEADER)


@router.get("/users_signups")
def get_user_signups(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """User signups per day for last 30 days."""
    def compute():
        try:
            sql = text("""
                SELECT DATE(created_at) as day, COUNT(*) as cnt
                FROM users
                WHERE created_at >= (CURRENT_DATE - INTERVAL '29 days')
                GROUP BY DATE(created_at)
            """)
            res = db.execute(sql).fetchall()
            today = datetime.utcnow().date(); start = today - timedelta(days=29)
            out = { (start + timedelta(days=i)).isoformat(): 0 for i in range(30) }
            for row in res:
                d = row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0])
                out[d] = int(row[1])
            return [{"day": k, "value": out[k]} for k in sorted(out.keys())]
        except Exception:
            return []

    payload = _cached("users_signups", compute)
    return JSONResponse(content=payload, headers=CACHE_HEADER)


@router.get("/users_signups_daily")
def users_signups_daily(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """New user signups per day for the last 30 days."""
    def compute():
        try:
            sql = text(
                """
                SELECT DATE(created_at) AS day, COUNT(*) AS cnt
                FROM users
                WHERE created_at >= (CURRENT_DATE - INTERVAL '29 days')
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at)
                """
            )
            rows = db.execute(sql).fetchall()
            _, buckets = _init_day_buckets()
            for row in rows:
                day = row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0])
                buckets[day] = int(row[1])
            return [{"day": day, "count": buckets[day]} for day in sorted(buckets.keys())]
        except Exception as e:
            print(f"[users_signups_daily] Error: {e}", flush=True)
            return []

    payload = _cached("users_signups_daily", compute)
    return JSONResponse(content=payload, headers=CACHE_HEADER)


@router.get("/active_today")
def active_students_today(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Number of distinct students active today."""
    def compute():
        try:
            sql = text(
                """
                SELECT COUNT(DISTINCT user_id) AS cnt
                FROM activity_events
                WHERE timestamp >= CURRENT_DATE
                """
            )
            count = db.execute(sql).scalar() or 0
            return {
                "date": datetime.utcnow().date().isoformat(),
                "active_students": int(count)
            }
        except Exception as e:
            print(f"[active_today] Error: {e}", flush=True)
            return {
                "date": datetime.utcnow().date().isoformat(),
                "active_students": 0
            }

    payload = _cached("active_today", compute)
    return JSONResponse(content=payload, headers=CACHE_HEADER)


@router.get("/recent_attempts")
def recent_attempts(limit: int = 20, db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Return the most recent exercise attempts with student info."""
    safe_limit = max(1, min(limit, 100))
    sql = text(
        """
        SELECT ea.id, ea.exercise_type, ea.exercise_id, ea.score, ea.started_at, ea.finished_at,
               ea.duration_seconds, u.email AS student_email, COALESCE(u.display_name, '') AS student_name
        FROM exercise_attempts ea
        JOIN users u ON u.id = ea.user_id
        ORDER BY ea.started_at DESC NULLS LAST
        LIMIT :limit
        """
    )
    try:
        rows = db.execute(sql, {"limit": safe_limit}).fetchall()
        items = []
        for row in rows:
            data = row._mapping if hasattr(row, "_mapping") else None
            started = data["started_at"] if data else row[4]
            finished = data["finished_at"] if data else row[5]
            items.append({
                "attempt_id": int((data or row)["id"] if data else row[0]),
                "student_email": (data or row)["student_email"],
                "student_name": (data or row)["student_name"],
                "exercise_type": (data or row)["exercise_type"],
                "exercise_id": (data or row)["exercise_id"],
                "score": (data or row)["score"],
                "duration_seconds": (data or row)["duration_seconds"],
                "started_at": started.isoformat() if started else None,
                "finished_at": finished.isoformat() if finished else None,
            })
        return JSONResponse(content=items, headers=CACHE_HEADER)
    except Exception as e:
        print(f"[recent_attempts] Error: {e}", flush=True)
        return JSONResponse(content=[], headers=CACHE_HEADER)


@router.get("/roles")
def get_roles(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Return counts per role name."""
    def compute():
        try:
            rows = db.query(Role.name, func.count()).join(UserRole, isouter=True).group_by(Role.name).all()
            return [{"role": r[0], "count": int(r[1])} for r in rows]
        except Exception:
            # fallback: simple list
            try:
                rows = db.query(Role).all()
                return [{"role": r.name, "count": 0} for r in rows]
            except Exception:
                return []

    payload = _cached("roles", compute)
    return JSONResponse(content=payload, headers=CACHE_HEADER)


@router.get("/refresh_tokens")
def get_refresh_tokens(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Return counts of active vs revoked refresh tokens."""
    def compute():
        try:
            total = db.query(func.count(RefreshToken.id)).scalar() or 0
            revoked = db.query(func.count(RefreshToken.id)).filter(RefreshToken.revoked.is_(True)).scalar() or 0
            active = int(total) - int(revoked)
            return {"total": int(total), "active": int(active), "revoked": int(revoked)}
        except Exception:
            return {"total":0, "active":0, "revoked":0}

    payload = _cached("refresh_tokens", compute)
    return JSONResponse(content=payload, headers=CACHE_HEADER)


@router.get("/vw_attempts")
def get_vw_attempts(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Return a small sample from vw_attempts view, if available."""
    try:
        def compute():
            try:
                rows = db.execute(text("SELECT * FROM vw_attempts LIMIT 200")).fetchall()
                # convert to list of dicts (best-effort)
                out = []
                for r in rows:
                    try:
                        out.append(dict(r._mapping))
                    except Exception:
                        # fallback tuple -> map indices
                        out.append({str(i): v for i, v in enumerate(r)})
                return out
            except Exception as e:
                # View likely doesn't exist or query failed
                print(f"[vw_attempts] Warning: {e}", flush=True)
                return []

        payload = _cached("vw_attempts", compute)
        return JSONResponse(content=payload, headers=CACHE_HEADER)
    except Exception as e:
        print(f"[vw_attempts] Top-level error: {e}", flush=True)
        return JSONResponse(content=[], headers=CACHE_HEADER, status_code=200)


@router.get("/overview")
def get_overview(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Combined small payload with key datasets for dashboard charts."""
    def compute():
        # Call pure data functions directly (no FastAPI dependencies)
        try:
            # Activity events
            sql_ae = text("""
                SELECT DATE(timestamp) as day, COUNT(*) as cnt
                FROM activity_events
                WHERE timestamp >= (CURRENT_DATE - INTERVAL '29 days')
                GROUP BY DATE(timestamp)
            """)
            res_ae = db.execute(sql_ae).fetchall()
            today = datetime.utcnow().date()
            start = today - timedelta(days=29)
            out_ae = { (start + timedelta(days=i)).isoformat(): 0 for i in range(30) }
            for row in res_ae:
                d = row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0])
                out_ae[d] = int(row[1])
            activity_events = [{"day": k, "value": out_ae[k]} for k in sorted(out_ae.keys())]

            # Exercise attempts
            sql_ea = text("""
                SELECT DATE(started_at) as day, COUNT(*) as cnt
                FROM exercise_attempts
                WHERE started_at >= (CURRENT_DATE - INTERVAL '29 days')
                GROUP BY DATE(started_at)
            """)
            res_ea = db.execute(sql_ea).fetchall()
            out_ea = { (start + timedelta(days=i)).isoformat(): 0 for i in range(30) }
            for row in res_ea:
                d = row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0])
                out_ea[d] = int(row[1])
            exercise_attempts = [{"day": k, "value": out_ea[k]} for k in sorted(out_ea.keys())]

            # User signups
            sql_us = text("""
                SELECT DATE(created_at) as day, COUNT(*) as cnt
                FROM users
                WHERE created_at >= (CURRENT_DATE - INTERVAL '29 days')
                GROUP BY DATE(created_at)
            """)
            res_us = db.execute(sql_us).fetchall()
            out_us = { (start + timedelta(days=i)).isoformat(): 0 for i in range(30) }
            for row in res_us:
                d = row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0])
                out_us[d] = int(row[1])
            user_signups = [{"day": k, "value": out_us[k]} for k in sorted(out_us.keys())]

            # Roles
            roles_rows = db.execute(text("SELECT r.name, COUNT(ur.user_id) as cnt FROM roles r LEFT JOIN user_roles ur ON ur.role_id = r.id GROUP BY r.name")).fetchall()
            roles = [{"role": r[0], "count": int(r[1])} for r in roles_rows]

            # Refresh tokens
            total = db.query(func.count(RefreshToken.id)).scalar() or 0
            revoked = db.query(func.count(RefreshToken.id)).filter(RefreshToken.revoked.is_(True)).scalar() or 0
            active = int(total) - int(revoked)
            refresh_tokens = {"total": int(total), "active": int(active), "revoked": int(revoked)}

            return {
                "activity_events": activity_events,
                "exercise_attempts": exercise_attempts,
                "user_signups": user_signups,
                "roles": roles,
                "refresh_tokens": refresh_tokens,
            }
        except Exception as e:
            print(f"[overview] Error: {e}", flush=True)
            return {
                "activity_events": [],
                "exercise_attempts": [],
                "user_signups": [],
                "roles": [],
                "refresh_tokens": {"total": 0, "active": 0, "revoked": 0},
            }

    payload = _cached("overview", compute)
    return JSONResponse(content=payload, headers=CACHE_HEADER)


@router.get("/user_activity/{user_id}")
def user_activity(user_id: int, days: int = 30, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Detailed timeline of exercises for a single user."""
    safe_days = _sanitize_days(days)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sql = text(
        """
        SELECT
            ea.id,
            ea.exercise_type,
            ea.exercise_id,
            COALESCE(ea.duration_seconds, EXTRACT(EPOCH FROM (ea.finished_at - ea.started_at))::INT) AS duration_seconds,
            CASE WHEN ea.exercise_type = 'pronunciation' THEN ea.score END AS pronunciation_score,
            ea.score,
            ea.started_at,
            ea.finished_at
        FROM exercise_attempts ea
        WHERE ea.user_id = :user_id
          AND (
              ea.started_at IS NULL
              OR ea.started_at >= (CURRENT_DATE - (:days * INTERVAL '1 day'))
          )
        ORDER BY ea.started_at DESC NULLS LAST, ea.id DESC
        LIMIT 500
        """
    )

    rows = db.execute(sql, {"user_id": user_id, "days": safe_days}).fetchall()
    items: List[Dict[str, Any]] = []
    for row in rows:
        data = row._mapping if hasattr(row, "_mapping") else None
        duration_val = (data or row)["duration_seconds"] if data else row[3]
        pron_score_val = (data or row)["pronunciation_score"] if data else row[4]
        started = (data or row)["started_at"] if data else row[6]
        finished = (data or row)["finished_at"] if data else row[7]
        items.append({
            "attempt_id": int((data or row)["id"] if data else row[0]),
            "exercise_type": (data or row)["exercise_type"] if data else row[1],
            "exercise_id": (data or row)["exercise_id"] if data else row[2],
            "duration_seconds": _coerce_int(duration_val),
            "pronunciation_score": _coerce_float(pron_score_val),
            "score": _coerce_float((data or row)["score"] if data else row[5]),
            "started_at": started.isoformat() if started else None,
            "finished_at": finished.isoformat() if finished else None,
        })

    payload = {
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "group_name": user.group_number,
        },
        "items": items,
    }
    return JSONResponse(content=payload, headers=CACHE_HEADER)


@router.get("/users_activity")
def users_activity(days: int = 30, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Aggregate exercise stats per user for the lookback window."""
    safe_days = _sanitize_days(days)
    sql = text(
        """
        SELECT
            u.id AS user_id,
            u.email,
            COALESCE(u.display_name, '') AS display_name,
            u.group_number,
            COUNT(*) AS total_exercises,
            COUNT(*) FILTER (WHERE ea.exercise_type = 'pronunciation') AS pronunciation_count,
            COUNT(*) FILTER (WHERE ea.exercise_type = 'chat') AS chat_count,
            COUNT(*) FILTER (WHERE ea.exercise_type = 'roleplay') AS roleplay_count,
            SUM(COALESCE(ea.duration_seconds, EXTRACT(EPOCH FROM (ea.finished_at - ea.started_at))::INT)) AS total_duration_seconds,
            AVG(CASE WHEN ea.exercise_type = 'pronunciation' THEN ea.score END) AS avg_pronunciation_score
        FROM exercise_attempts ea
        JOIN users u ON u.id = ea.user_id
        WHERE (
            ea.started_at IS NULL
            OR ea.started_at >= (CURRENT_DATE - (:days * INTERVAL '1 day'))
        )
        GROUP BY u.id, u.email, u.display_name, u.group_number
        ORDER BY u.group_number NULLS LAST, u.email
        """
    )

    rows = db.execute(sql, {"days": safe_days}).fetchall()
    items: List[Dict[str, Any]] = []
    for row in rows:
        data = row._mapping if hasattr(row, "_mapping") else None
        get = (lambda key, idx: (data or row)[key] if data else row[idx])
        items.append({
            "user_id": int(get("user_id", 0)),
            "email": get("email", 1),
            "display_name": get("display_name", 2),
            "group_name": get("group_number", 3),
            "total_exercises": _coerce_int(get("total_exercises", 4)) or 0,
            "pronunciation_count": _coerce_int(get("pronunciation_count", 5)) or 0,
            "chat_count": _coerce_int(get("chat_count", 6)) or 0,
            "roleplay_count": _coerce_int(get("roleplay_count", 7)) or 0,
            "total_duration_seconds": _coerce_int(get("total_duration_seconds", 8)) or 0,
            "avg_pronunciation_score": _coerce_float(get("avg_pronunciation_score", 9)),
        })

    return JSONResponse(content=items, headers=CACHE_HEADER)


@router.get("/groups_activity")
def groups_activity(days: int = 30, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Aggregate exercise stats per group for the lookback window."""
    safe_days = _sanitize_days(days)
    sql = text(
        """
        SELECT
            COALESCE(u.group_number, 'Unassigned') AS group_name,
            COUNT(DISTINCT u.id) AS student_count,
            COUNT(*) AS total_exercises,
            COUNT(*) FILTER (WHERE ea.exercise_type = 'pronunciation') AS pronunciation_count,
            COUNT(*) FILTER (WHERE ea.exercise_type = 'chat') AS chat_count,
            COUNT(*) FILTER (WHERE ea.exercise_type = 'roleplay') AS roleplay_count,
            SUM(COALESCE(ea.duration_seconds, EXTRACT(EPOCH FROM (ea.finished_at - ea.started_at))::INT)) AS total_duration_seconds,
            AVG(CASE WHEN ea.exercise_type = 'pronunciation' THEN ea.score END) AS avg_pronunciation_score
        FROM exercise_attempts ea
        JOIN users u ON u.id = ea.user_id
        WHERE (
            ea.started_at IS NULL
            OR ea.started_at >= (CURRENT_DATE - (:days * INTERVAL '1 day'))
        )
        GROUP BY COALESCE(u.group_number, 'Unassigned')
        ORDER BY group_name
        """
    )

    rows = db.execute(sql, {"days": safe_days}).fetchall()
    items: List[Dict[str, Any]] = []
    for row in rows:
        data = row._mapping if hasattr(row, "_mapping") else None
        get = (lambda key, idx: (data or row)[key] if data else row[idx])
        items.append({
            "group_name": get("group_name", 0),
            "student_count": _coerce_int(get("student_count", 1)) or 0,
            "total_exercises": _coerce_int(get("total_exercises", 2)) or 0,
            "pronunciation_count": _coerce_int(get("pronunciation_count", 3)) or 0,
            "chat_count": _coerce_int(get("chat_count", 4)) or 0,
            "roleplay_count": _coerce_int(get("roleplay_count", 5)) or 0,
            "total_duration_seconds": _coerce_int(get("total_duration_seconds", 6)) or 0,
            "avg_pronunciation_score": _coerce_float(get("avg_pronunciation_score", 7)),
        })

    return JSONResponse(content=items, headers=CACHE_HEADER)


# Additional admin endpoints requested by the product owner

@router.get("/attempts")
def get_attempts(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Alias for exercise_attempts - counts per day."""
    def compute():
        try:
            sql = text("""
                SELECT DATE(started_at) as day, COUNT(*) as cnt
                FROM attempts
                WHERE started_at >= (CURRENT_DATE - INTERVAL '29 days')
                GROUP BY DATE(started_at)
            """)
            res = db.execute(sql).fetchall()
            today = datetime.utcnow().date(); start = today - timedelta(days=29)
            out = { (start + timedelta(days=i)).isoformat(): 0 for i in range(30) }
            for row in res:
                d = row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0])
                out[d] = int(row[1])
            return [{"day": k, "value": out[k]} for k in sorted(out.keys())]
        except Exception:
            return []

    payload = _cached("attempts", compute)
    return JSONResponse(content=payload, headers=CACHE_HEADER)


@router.get("/events")
def get_events(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Return top event types and daily counts."""
    def compute():
        try:
            top_sql = text("SELECT event_type, COUNT(*) as cnt FROM activity_events WHERE timestamp >= (CURRENT_DATE - INTERVAL '29 days') GROUP BY event_type ORDER BY cnt DESC LIMIT 20")
            top = db.execute(top_sql).fetchall()
            top_list = [{"event_type": r[0], "count": int(r[1])} for r in top]

            # daily histogram for total events
            day_sql = text("SELECT DATE(timestamp) as day, COUNT(*) as cnt FROM activity_events WHERE timestamp >= (CURRENT_DATE - INTERVAL '29 days') GROUP BY DATE(timestamp)")
            rows = db.execute(day_sql).fetchall()
            today = datetime.utcnow().date(); start = today - timedelta(days=29)
            out = { (start + timedelta(days=i)).isoformat(): 0 for i in range(30) }
            for row in rows:
                d = row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0])
                out[d] = int(row[1])
            daily = [{"day": k, "value": out[k]} for k in sorted(out.keys())]

            return {"top": top_list, "daily": daily}
        except Exception:
            return {"top": [], "daily": []}

    payload = _cached("events", compute)
    return JSONResponse(content=payload, headers=CACHE_HEADER)


@router.get("/sessions")
def get_sessions(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Session starts per day"""
    def compute():
        try:
            sql = text("""
                SELECT DATE(started_at) as day, COUNT(*) as cnt
                FROM sessions
                WHERE started_at >= (CURRENT_DATE - INTERVAL '29 days')
                GROUP BY DATE(started_at)
            """)
            res = db.execute(sql).fetchall()
            today = datetime.utcnow().date(); start = today - timedelta(days=29)
            out = { (start + timedelta(days=i)).isoformat(): 0 for i in range(30) }
            for row in res:
                d = row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0])
                out[d] = int(row[1])
            return [{"day": k, "value": out[k]} for k in sorted(out.keys())]
        except Exception:
            return []

    payload = _cached("sessions", compute)
    return JSONResponse(content=payload, headers=CACHE_HEADER)


@router.get("/users")
def get_users(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """User counts: total + signups per day"""
    def compute():
        try:
            total = db.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0] or 0
            # reuse signups histogram
            sql = text("SELECT DATE(created_at) as day, COUNT(*) as cnt FROM users WHERE created_at >= (CURRENT_DATE - INTERVAL '29 days') GROUP BY DATE(created_at)")
            rows = db.execute(sql).fetchall()
            today = datetime.utcnow().date(); start = today - timedelta(days=29)
            out = { (start + timedelta(days=i)).isoformat(): 0 for i in range(30) }
            for r in rows:
                d = r[0].isoformat() if hasattr(r[0], 'isoformat') else str(r[0])
                out[d] = int(r[1])
            daily = [{"day": k, "value": out[k]} for k in sorted(out.keys())]
            return {"total": int(total), "daily_signups": daily}
        except Exception:
            return {"total":0, "daily_signups": []}

    payload = _cached("users", compute)
    return JSONResponse(content=payload, headers=CACHE_HEADER)


@router.get("/user_roles")
def get_user_roles(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Counts of users per role"""
    def compute():
        try:
            rows = db.execute(text("SELECT r.name, COUNT(ur.user_id) as cnt FROM roles r LEFT JOIN user_roles ur ON ur.role_id = r.id GROUP BY r.name" )).fetchall()
            return [{"role": r[0], "count": int(r[1])} for r in rows]
        except Exception:
            return []

    payload = _cached("user_roles", compute)
    return JSONResponse(content=payload, headers=CACHE_HEADER)


@router.get("/playing_with_neon")
def get_playing_with_neon(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Return a few recent rows from playing_with_neon table (if present)."""
    def compute():
        try:
            rows = db.execute(text("SELECT * FROM playing_with_neon ORDER BY ts DESC LIMIT 100")).fetchall()
            out = []
            for r in rows:
                try:
                    out.append(dict(r._mapping))
                except Exception:
                    out.append({str(i): v for i, v in enumerate(r)})
            return out
        except Exception:
            return []

    payload = _cached("playing_with_neon", compute)
    return JSONResponse(content=payload, headers=CACHE_HEADER)


@router.get("/skill_map_id")
def get_skill_map_id(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Counts grouped by skill_map_id from exercise_attempts or activity_events."""
    def compute():
        try:
            rows = db.execute(text("SELECT skill_map_id, COUNT(*) as cnt FROM exercise_attempts WHERE skill_map_id IS NOT NULL GROUP BY skill_map_id ORDER BY cnt DESC LIMIT 200")).fetchall()
            return [{"skill_map_id": r[0], "count": int(r[1])} for r in rows]
        except Exception:
            return []

    payload = _cached("skill_map_id", compute)
    return JSONResponse(content=payload, headers=CACHE_HEADER)


@router.get("/skill_map_type")
def get_skill_map_type(db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Counts grouped by skill_map_type from exercise_attempts."""
    def compute():
        try:
            rows = db.execute(text("SELECT COALESCE(skill_map_type,'unknown') as t, COUNT(*) as cnt FROM exercise_attempts GROUP BY t ORDER BY cnt DESC LIMIT 50")).fetchall()
            return [{"skill_map_type": r[0], "count": int(r[1])} for r in rows]
        except Exception:
            return []

    payload = _cached("skill_map_type", compute)
    return JSONResponse(content=payload, headers=CACHE_HEADER)
