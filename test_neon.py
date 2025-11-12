"""
Test Neon PostgreSQL async connection
This confirms your database connection and SSL are working correctly.
"""
import os
import asyncio
import re
from sqlalchemy import text
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

async def async_main():
    # Get DATABASE_URL from .env
    url = os.getenv("DATABASE_URL")

    if not url:
        print("❌ DATABASE_URL not found in .env")
        return

    # Convert postgresql:// to postgresql+asyncpg://
    async_url = re.sub(r"^postgresql:", "postgresql+asyncpg:", url)

    print(f"Testing connection to: {async_url[:50]}...")
    print()

    # Create async engine
    engine = create_async_engine(async_url, echo=True)

    try:
        # Test connection with a simple query
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 'hello world'"))
            data = result.fetchall()
            print()
            print("=" * 60)
            print("✅ SUCCESS! Connection working!")
            print("=" * 60)
            print(f"Result: {data}")
            print()

            # Also test database info
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchall()
            print(f"PostgreSQL version: {version[0][0][:50]}...")

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ CONNECTION FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        print()

    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(async_main())

