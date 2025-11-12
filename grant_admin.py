"""
Grant admin role to a user
Run this to make your first admin account
"""
from sqlalchemy.orm import Session
from db import engine, SessionLocal
from models import User, Role, UserRole

def grant_admin(email: str):
    """Grant admin role to user by email"""
    db = SessionLocal()
    try:
        # Find user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User not found: {email}")
            return

        # Find or create admin role
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(name="admin")
            db.add(admin_role)
            db.flush()

        # Check if already has admin role
        existing = db.query(UserRole).filter(
            UserRole.user_id == user.id,
            UserRole.role_id == admin_role.id
        ).first()

        if existing:
            print(f"⚠️  User {email} already has admin role")
        else:
            db.add(UserRole(user_id=user.id, role_id=admin_role.id))
            db.commit()
            print(f"✅ Granted admin role to {email}")
            print(f"   User ID: {user.id}")
            print(f"   User now has roles: {[ur.role.name for ur in user.roles]}")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python grant_admin.py <email>")
        print("Example: python grant_admin.py teacher@example.com")
        sys.exit(1)

    email = sys.argv[1]
    grant_admin(email)

