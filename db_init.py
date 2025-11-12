"""
Startup initialization for database
Creates tables and seeds default roles
"""
from db import engine, get_db
from models import Base, Role


def init_db():
    """Initialize database tables and seed roles"""
    # Create all tables (safe if using Alembic)
    Base.metadata.create_all(bind=engine)
    print("[startup] ✅ Database tables created/verified", flush=True)

    # Seed default roles
    with next(get_db()) as db:  # type: ignore
        for role_name in ("admin", "student"):
            if not db.query(Role).filter(Role.name == role_name).first():
                db.add(Role(name=role_name))
                print(f"[startup] Created role: {role_name}", flush=True)
        db.commit()

    print("[startup] ✅ Default roles seeded", flush=True)

