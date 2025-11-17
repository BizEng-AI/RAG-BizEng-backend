"""
modify_roles.py

Usage:
  python modify_roles.py add <email> <role>
  python modify_roles.py remove <email> <role>

Runs against the same DB configured by the project's SessionLocal.
"""
from sqlalchemy.orm import Session
from db import SessionLocal
from models import User, Role, UserRole
import sys


def add_role(email: str, role_name: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"User not found: {email}")
            return 1
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(name=role_name)
            db.add(role)
            db.flush()
        existing = db.query(UserRole).filter(UserRole.user_id == user.id, UserRole.role_id == role.id).first()
        if existing:
            print(f"User {email} already has role {role_name}")
            return 0
        ur = UserRole(user_id=user.id, role_id=role.id)
        db.add(ur)
        db.commit()
        print(f"Added role '{role_name}' to user {email}")
        # show roles
        roles = [ur.role.name for ur in user.roles]
        print("User roles now:", roles)
        return 0
    except Exception as e:
        print("Error:", e)
        db.rollback()
        return 2
    finally:
        db.close()


def remove_role(email: str, role_name: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"User not found: {email}")
            return 1
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            print(f"Role not found: {role_name}")
            return 1
        ur = db.query(UserRole).filter(UserRole.user_id == user.id, UserRole.role_id == role.id).first()
        if not ur:
            print(f"User {email} does not have role {role_name}")
            return 0
        db.delete(ur)
        db.commit()
        print(f"Removed role '{role_name}' from user {email}")
        # refresh roles list
        user = db.query(User).filter(User.email == email).first()
        roles = [r.role.name for r in user.roles]
        print("User roles now:", roles)
        return 0
    except Exception as e:
        print("Error:", e)
        db.rollback()
        return 2
    finally:
        db.close()


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    email = sys.argv[2]
    role = sys.argv[3]
    if cmd == 'add':
        sys.exit(add_role(email, role))
    elif cmd == 'remove':
        sys.exit(remove_role(email, role))
    else:
        print('Unknown command', cmd)
        sys.exit(1)

