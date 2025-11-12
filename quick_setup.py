"""
Quick setup and test script for authentication system
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and print output"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print('='*60)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode == 0

def main():
    print("🚀 BizEng Authentication System - Quick Setup")
    print("=" * 60)

    # Step 1: Install dependencies
    if not run_command(
        "pip install passlib[bcrypt] python-jose[cryptography] sqlalchemy psycopg[binary] alembic",
        "📦 Installing dependencies..."
    ):
        print("❌ Failed to install dependencies")
        return False

    # Step 2: Test imports
    print("\n✅ Testing imports...")
    try:
        import passlib
        import jose
        import sqlalchemy
        import psycopg
        print("✅ All dependencies imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

    # Step 3: Test database connection
    print("\n🗄️  Testing database connection...")
    if run_command("python test_neon_sync.py", "Testing Neon PostgreSQL..."):
        print("✅ Database connection successful")
    else:
        print("⚠️  Database connection failed (may need configuration)")

    # Step 4: Start server (in background)
    print("\n🔥 Starting server...")
    print("Run in a separate terminal:")
    print("   uvicorn app:app --reload --port 8020")
    print("\nThen run:")
    print("   python test_auth_system.py")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

