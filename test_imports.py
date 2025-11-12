"""
Simple test to verify imports
"""
print("Testing imports...")

try:
    print("1. Testing settings...")
    from settings import DATABASE_URL, JWT_SECRET
    print(f"   ✅ DATABASE_URL: {DATABASE_URL[:50]}...")
    print(f"   ✅ JWT_SECRET: {'set' if JWT_SECRET else 'not set'}")
except Exception as e:
    print(f"   ❌ Settings error: {e}")

try:
    print("\n2. Testing db...")
    from db import engine, get_db
    print("   ✅ DB module imported")
except Exception as e:
    print(f"   ❌ DB error: {e}")

try:
    print("\n3. Testing models...")
    from models import Base, User, Role
    print("   ✅ Models imported")
except Exception as e:
    print(f"   ❌ Models error: {e}")

try:
    print("\n4. Testing security...")
    from security import hash_password, make_access_token
    print("   ✅ Security module imported")
except Exception as e:
    print(f"   ❌ Security error: {e}")

try:
    print("\n5. Testing routers...")
    from routers import auth, me, admin, tracking
    print("   ✅ All routers imported")
except Exception as e:
    print(f"   ❌ Router error: {e}")

try:
    print("\n6. Creating database tables...")
    from db import engine
    from models import Base
    Base.metadata.create_all(bind=engine)
    print("   ✅ Tables created/verified")
except Exception as e:
    print(f"   ❌ Table creation error: {e}")

try:
    print("\n7. Testing app import...")
    from app import app
    print("   ✅ App imported successfully")
except Exception as e:
    print(f"   ❌ App import error: {e}")

print("\n" + "="*60)
print("Import test complete!")
print("="*60)

