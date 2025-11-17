import json
from db import SessionLocal
from models import User
import sys

email = sys.argv[1] if len(sys.argv) > 1 else 'yoo@gmail.com'

db = SessionLocal()
try:
    user = db.query(User).filter(User.email == email).first()
    out = {"email": email}
    if not user:
        out["found"] = False
    else:
        out["found"] = True
        out["id"] = user.id
        out["roles"] = [ur.role.name for ur in user.roles]
    with open('roles_output.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
finally:
    db.close()

print('WROTE roles_output.json')
