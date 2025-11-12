"""
Complete system verification test
Tests database, imports, and basic functionality
"""
import sys
import os
import warnings

# Suppress bcrypt version warnings
warnings.filterwarnings('ignore', message='.*bcrypt.*')
warnings.filterwarnings('ignore', category=UserWarning, module='passlib')

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_environment():
    """Test environment variables"""
    print_section("1. ENVIRONMENT VARIABLES")

    from dotenv import load_dotenv
    load_dotenv()

    required_vars = [
        "DATABASE_URL",
        "JWT_SECRET",
        "QDRANT_URL",
        "QDRANT_API_KEY"
    ]

    all_ok = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Show first 50 chars for security
            display = value[:50] + "..." if len(value) > 50 else value
            # Mask secrets
            if "SECRET" in var or "KEY" in var:
                display = "***" + value[-4:] if len(value) > 4 else "***"
            print(f"  ✅ {var}: {display}")
        else:
            print(f"  ❌ {var}: NOT SET")
            all_ok = False

    return all_ok

def test_dependencies():
    """Test required dependencies"""
    print_section("2. DEPENDENCIES")

    dependencies = [
        ("fastapi", "FastAPI web framework"),
        ("sqlalchemy", "Database ORM"),
        ("psycopg", "PostgreSQL driver"),
        ("passlib", "Password hashing"),
        ("jose", "JWT tokens"),
        ("alembic", "Database migrations"),
        ("qdrant_client", "Vector database"),
        ("openai", "OpenAI/Azure client"),
    ]

    all_ok = True
    for module, description in dependencies:
        try:
            __import__(module)
            print(f"  ✅ {module:20s} - {description}")
        except ImportError:
            print(f"  ❌ {module:20s} - NOT INSTALLED")
            all_ok = False

    return all_ok

def test_database_connection():
    """Test database connection"""
    print_section("3. DATABASE CONNECTION")

    try:
        from sqlalchemy import create_engine, text
        url = os.getenv("DATABASE_URL")

        if not url:
            print("  ❌ DATABASE_URL not set")
            return False

        engine = None
        try:
            engine = create_engine(url, pool_pre_ping=True)

            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
                if result == 1:
                    print("  ✅ Database connection successful")

                    # Get version
                    version = conn.execute(text("SELECT version()")).scalar()
                    print(f"  ✅ PostgreSQL: {version.split(',')[0]}")
                    return True
                else:
                    print("  ❌ Unexpected result from database")
                    return False
        finally:
            if engine:
                engine.dispose()

    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        return False

def test_models():
    """Test database models"""
    print_section("4. DATABASE MODELS")

    try:
        from models import Base, User, Role, UserRole, RefreshToken, ExerciseAttempt, ActivityEvent

        models = [
            ("User", User),
            ("Role", Role),
            ("UserRole", UserRole),
            ("RefreshToken", RefreshToken),
            ("ExerciseAttempt", ExerciseAttempt),
            ("ActivityEvent", ActivityEvent),
        ]

        for name, model in models:
            print(f"  ✅ {name:20s} - {model.__tablename__}")

        print(f"  ✅ Total models: {len(models)}")
        return True

    except Exception as e:
        print(f"  ❌ Model import failed: {e}")
        return False

def test_security():
    """Test security functions"""
    print_section("5. SECURITY FUNCTIONS")

    try:
        from security import hash_password, verify_password, make_access_token, make_refresh_token

        # Test password hashing (use short password to avoid bcrypt 72-byte limit)
        password = "TestPass123"  # Short password within bcrypt limit
        hashed = hash_password(password)

        if verify_password(password, hashed):
            print("  ✅ Password hashing/verification works")
        else:
            print("  ❌ Password verification failed")
            return False

        # Test with wrong password
        if not verify_password("WrongPassword", hashed):
            print("  ✅ Password verification correctly rejects wrong password")
        else:
            print("  ❌ Password verification accepted wrong password")
            return False

        # Test JWT token creation
        token = make_access_token("test@example.com", ["student"])
        if token and len(token) > 50:
            print(f"  ✅ JWT token creation works (length: {len(token)})")
        else:
            print("  ❌ JWT token creation failed")
            return False

        # Test refresh token
        refresh = make_refresh_token()
        if refresh and len(refresh) == 32:  # UUID hex is 32 chars
            print(f"  ✅ Refresh token creation works")
        else:
            print("  ❌ Refresh token creation failed")
            return False

        return True

    except Exception as e:
        print(f"  ❌ Security test failed: {e}")
        return False

def test_routers():
    """Test router imports"""
    print_section("6. API ROUTERS")

    try:
        from routers import auth, me, admin, tracking

        routers = [
            ("auth", auth.router),
            ("me", me.router),
            ("admin", admin.router),
            ("tracking", tracking.router),
        ]

        for name, router in routers:
            print(f"  ✅ {name:20s} - {router.prefix}")

        return True

    except Exception as e:
        print(f"  ❌ Router import failed: {e}")
        return False

def test_app():
    """Test FastAPI app"""
    print_section("7. FASTAPI APPLICATION")

    try:
        from app import app

        # Check routes
        routes = [route.path for route in app.routes]

        # Check for key endpoints
        required_endpoints = [
            "/auth/register",
            "/auth/login",
            "/me",
            "/admin/dashboard",
            "/tracking/attempts",
        ]

        all_found = True
        for endpoint in required_endpoints:
            if any(endpoint in route for route in routes):
                print(f"  ✅ {endpoint}")
            else:
                print(f"  ❌ {endpoint} - NOT FOUND")
                all_found = False

        if all_found:
            print(f"  ✅ Total routes registered: {len(routes)}")
            return True
        else:
            return False

    except Exception as e:
        print(f"  ❌ App import failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "🧪" * 35)
    print("  COMPLETE SYSTEM VERIFICATION")
    print("🧪" * 35)

    tests = [
        ("Environment", test_environment),
        ("Dependencies", test_dependencies),
        ("Database", test_database_connection),
        ("Models", test_models),
        ("Security", test_security),
        ("Routers", test_routers),
        ("Application", test_app),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n  ❌ {name} test crashed: {e}")
            results[name] = False

    # Summary
    print_section("SUMMARY")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status:10s} - {name}")

    print()
    print(f"  Results: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("  🎉 ALL TESTS PASSED - SYSTEM READY!")
        print()
        print("  Next steps:")
        print("    1. Start server: uvicorn app:app --reload --port 8020")
        print("    2. Run API tests: python test_auth_system.py")
        print("    3. Deploy: fly deploy --app bizeng-server")
        return True
    else:
        print("  ⚠️  SOME TESTS FAILED - FIX ERRORS ABOVE")
        print()
        print("  Common fixes:")
        print("    - Install dependencies: pip install -r requirements.txt")
        print("    - Check .env file for missing variables")
        print("    - Verify DATABASE_URL is correct")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

