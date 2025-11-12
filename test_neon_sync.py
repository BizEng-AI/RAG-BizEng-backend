"""
Test Neon PostgreSQL connection with psycopg driver
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def test_connection():
    """Test database connection safely"""
    url = os.getenv("DATABASE_URL")

    if not url:
        print("❌ DATABASE_URL not found in .env")
        return False

    print("Testing connection to Neon PostgreSQL...")
    print("Driver: psycopg")
    print()

    engine = None
    try:
        # Create engine with connection pooling
        engine = create_engine(url, pool_pre_ping=True, echo=True)

        # Test connection
        with engine.connect() as conn:
            # Get PostgreSQL version
            version = conn.execute(text("SELECT version()")).scalar_one()

            # Test simple query
            hello = conn.execute(text("SELECT 'hello world'")).scalar_one()

            print()
            print("=" * 60)
            print("✅ SUCCESS! Connection working!")
            print("=" * 60)
            print(f"PostgreSQL version: {version[:80]}...")
            print(f"Test query result: {hello}")
            print()

        return True

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ CONNECTION FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        return False
    finally:
        # Safely dispose engine only if it was created
        if engine is not None:
            engine.dispose()

if __name__ == "__main__":
    ok = test_connection()
    sys.exit(0 if ok else 1)

