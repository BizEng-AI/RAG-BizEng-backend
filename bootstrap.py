"""
Database bootstrap helpers.
"""
from __future__ import annotations

from db import SessionLocal, engine
from models import Base, Role


DEFAULT_ROLES = ("admin", "student")


def init_db() -> None:
    """Create tables and ensure base roles exist."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        for role_name in DEFAULT_ROLES:
            existing = db.query(Role).filter(Role.name == role_name).first()
            if not existing:
                db.add(Role(name=role_name))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
