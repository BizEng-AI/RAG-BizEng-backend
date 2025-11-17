"""
admin_test_runner.py

Usage (run locally on machine with DB access and network to server):
  python admin_test_runner.py --email yoo@gmail.com --password "YourPassword" --base-url https://bizeng-server.fly.dev

What it does:
- Connects to the project's DB via SessionLocal
- Removes the 'student' role mapping for the given email (if present)
- Ensures the 'admin' role exists and is assigned to the user
- Logs in to the server's /auth/login to obtain an access token
- Calls all admin-only endpoints and writes JSON responses to admin_test_results/<endpoint>.json
- Prints a concise summary report

NOTE: This script is for testing and debugging only. It writes token and outputs to disk; delete files after use.
"""
import os
import sys
import argparse
import json
from time import sleep
from pathlib import Path

import requests
from db import SessionLocal
from models import User, Role, UserRole
from sqlalchemy.exc import SQLAlchemyError

ADMIN_ENDPOINTS = [
    "overview",
    "activity_events",
    "exercise_attempts",
    "attempts",
    "events",
    "sessions",
    "users",
    "users_signups",
    "user_roles",
    "roles",
    "skill_map_id",
    "skill_map_type",
    "vw_attempts",
    "playing_with_neon",
    "refresh_tokens",
]


def fix_roles(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return {"error": "user_not_found"}

        before = [ur.role.name for ur in user.roles]

        # Ensure admin role exists
        admin_role = db.query(Role).filter(Role.name == 'admin').first()
        if not admin_role:
            admin_role = Role(name='admin')
            db.add(admin_role)
            db.flush()

        # Remove student role mapping if present
        student_role = db.query(Role).filter(Role.name == 'student').first()
        removed_student = False
        if student_role:
            ur = db.query(UserRole).filter(UserRole.user_id == user.id, UserRole.role_id == student_role.id).first()
            if ur:
                db.delete(ur)
                db.commit()
                removed_student = True

        # Ensure admin mapping
        admin_map = db.query(UserRole).filter(UserRole.user_id == user.id, UserRole.role_id == admin_role.id).first()
        if not admin_map:
            db.add(UserRole(user_id=user.id, role_id=admin_role.id))
            db.commit()

        # refresh
        user = db.query(User).filter(User.email == email).first()
        after = [ur.role.name for ur in user.roles]

        return {"before": before, "after": after, "removed_student": removed_student}

    except SQLAlchemyError as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


def login_and_get_token(base_url: str, email: str, password: str):
    url = base_url.rstrip('/') + '/auth/login'
    try:
        r = requests.post(url, json={"email": email, "password": password}, timeout=15)
    except Exception as e:
        return {"error": f"request_failed: {e}"}

    if r.status_code != 200:
        return {"error": f"login_failed", "status_code": r.status_code, "body": r.text}

    try:
        data = r.json()
    except Exception as e:
        return {"error": "invalid_json", "body": r.text}

    access = data.get('access_token') or data.get('access') or data.get('token')
    refresh = data.get('refresh_token') or data.get('refresh')
    return {"access": access, "refresh": refresh, "raw": data}


def call_admin_endpoints(base_url: str, access_token: str, out_dir: Path):
    headers = {"Authorization": f"Bearer {access_token}"}
    summary = {}
    out_dir.mkdir(parents=True, exist_ok=True)

    for ep in ADMIN_ENDPOINTS:
        url = base_url.rstrip('/') + f'/admin/monitor/{ep}'
        try:
            r = requests.get(url, headers=headers, timeout=20)
            status = r.status_code
            try:
                j = r.json()
            except Exception:
                j = {"text": r.text}
            # Save
            fname = out_dir / f"{ep}.json"
            with open(fname, 'w', encoding='utf-8') as f:
                json.dump({"status": status, "body": j}, f, indent=2, ensure_ascii=False)
            summary[ep] = {"status": status, "file": str(fname)}
        except Exception as e:
            summary[ep] = {"error": str(e)}
        # be polite
        sleep(0.2)

    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--email', required=True)
    p.add_argument('--password', required=True)
    p.add_argument('--base-url', default=os.environ.get('BASE_URL', 'https://bizeng-server.fly.dev'))
    p.add_argument('--out', default='admin_test_results')
    args = p.parse_args()

    print('Fixing roles for', args.email)
    res = fix_roles(args.email)
    print('Role fix result:', res)

    if 'error' in res:
        print('Aborting due to error')
        sys.exit(1)

    print('Logging in to obtain token...')
    tok = login_and_get_token(args.base_url, args.email, args.password)
    if 'error' in tok or not tok.get('access'):
        print('Login failed or token missing:', tok)
        sys.exit(1)

    access = tok['access']
    print('Got access token (len):', len(access))

    out_dir = Path(args.out)
    print('Calling admin endpoints and saving into', out_dir)
    summary = call_admin_endpoints(args.base_url, access, out_dir)

    report = {
        'role_fix': res,
        'login': {k: v for k, v in tok.items() if k != 'raw'},
        'endpoints': summary,
    }

    with open('admin_test_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print('WROTE admin_test_report.json')
    print('Done. Check admin_test_results/ and admin_test_report.json')


if __name__ == '__main__':
    main()

