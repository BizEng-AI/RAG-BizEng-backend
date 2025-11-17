"""
admin_fix_and_token.py

- Removes role 'student' for a given email (if present) while keeping 'admin'
- Generates a signed access token for the user using project's security.make_access_token
- Writes a JSON report to admin_fix_result.json with before/after roles and token

Usage:
  python admin_fix_and_token.py yoo@gmail.com

Be careful: this script writes a token to disk for testing only. Delete the file after use.
"""
import sys, json
from db import SessionLocal
from models import User, Role, UserRole
from security import make_access_token

email = sys.argv[1] if len(sys.argv) > 1 else 'yoo@gmail.com'

out = {"email": email}

db = SessionLocal()
try:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        out["error"] = f"User not found: {email}"
    else:
        # capture before roles
        before = [ur.role.name for ur in user.roles]
        out["before_roles"] = before

        # ensure admin role exists
        admin_role = db.query(Role).filter(Role.name == 'admin').first()
        if not admin_role:
            admin_role = Role(name='admin')
            db.add(admin_role)
            db.flush()

        # remove student role mapping if present
        student_role = db.query(Role).filter(Role.name == 'student').first()
        removed = False
        if student_role:
            ur = db.query(UserRole).filter(UserRole.user_id == user.id, UserRole.role_id == student_role.id).first()
            if ur:
                db.delete(ur)
                db.commit()
                removed = True

        # refresh user roles
        user = db.query(User).filter(User.email == email).first()
        after = [ur.role.name for ur in user.roles]
        out["after_roles"] = after
        out["removed_student_role"] = removed

        # ensure admin present; if not, add
        if 'admin' not in after:
            ur = UserRole(user_id=user.id, role_id=admin_role.id)
            db.add(ur)
            db.commit()
            user = db.query(User).filter(User.email == email).first()
            after = [ur.role.name for ur in user.roles]
            out["after_roles"] = after

        # create access token for testing (roles list)
        token = make_access_token(user.email, after)
        out["access_token"] = token

finally:
    db.close()

with open('admin_fix_result.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2)

print('WROTE admin_fix_result.json')

