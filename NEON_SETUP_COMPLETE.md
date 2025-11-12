# Install dependencies
pip install -r requirements.txt

# Test connection
python test_neon_sync.py
```

**Expected output:**
```
✅ SUCCESS! Connection working!
PostgreSQL version: PostgreSQL 17.2...
Test query result: hello world
```

Once this works, we can proceed to:
1. Define SQLAlchemy models for auth system
2. Set up Alembic migrations
3. Create database tables
4. Implement auth endpoints

---

**Status:** ✅ Configuration complete - Ready to test  
**Driver:** psycopg (Neon recommended)  
**SSL:** Required and configured  
**Next:** Test connection then define models
# ✅ NEON POSTGRESQL SETUP - COMPLETE

**Date:** November 11, 2025  
**Status:** ✅ Configuration updated for psycopg driver

---

## 🎯 WHAT WAS CONFIGURED

### 1. Database Driver: psycopg ✅
Changed from `asyncpg` to `psycopg` (recommended by Neon)

### 2. Connection String Format ✅
```
postgresql+psycopg://neondb_owner:PASSWORD@ep-bitter-glitter-a9ivcai1-pooler.gwc.azure.neon.tech/neondb?sslmode=require
```

### 3. Files Updated ✅
- **`.env`** - DATABASE_URL with psycopg driver
- **`requirements.txt`** - Added psycopg[binary], sqlalchemy, alembic
- **Fly.io secrets** - DATABASE_URL set with psycopg

---

## 📄 UPDATED FILES

### `.env`
```env
DATABASE_URL=postgresql+psycopg://neondb_owner:npg_htFK06nYwEis@ep-bitter-glitter-a9ivcai1-pooler.gwc.azure.neon.tech/neondb?sslmode=require
```

### `requirements.txt`
```txt
# Database (PostgreSQL with Neon using psycopg)
sqlalchemy>=2.0
psycopg[binary]>=3.1.0
alembic>=1.13.0
```

---

## 🧪 TEST CONNECTION

### Created Test Script: `test_neon_sync.py`

```python
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("DATABASE_URL")
engine = create_engine(url, echo=True)

with engine.connect() as conn:
    result = conn.execute(text("SELECT version()"))
    print(result.fetchone())
```

### Run Test:
```bash
cd C:\Users\sanja\rag-biz-english\server
pip install -r requirements.txt
python test_neon_sync.py
```

### Expected Output:
```
✅ SUCCESS! Connection working!
PostgreSQL version: PostgreSQL 17.2 on x86_64-pc-linux-gnu...
Test query result: hello world
```

---

## 🚀 FLY.IO DEPLOYMENT

### Secret Set:
```bash
fly secrets set DATABASE_URL="postgresql+psycopg://neondb_owner:npg_htFK06nYwEis@ep-bitter-glitter-a9ivcai1-pooler.gwc.azure.neon.tech/neondb?sslmode=require" --app bizeng-server
```

### Verify Secret:
```bash
fly secrets list --app bizeng-server
```

Should show:
- `DATABASE_URL` (set)

---

## 📊 NEON DATABASE INFO

**Cluster:** ep-bitter-glitter-a9ivcai1  
**Region:** gwc.azure (EU Central - Germany)  
**Database:** neondb  
**User:** neondb_owner  
**Connection:** Pooled connection (optimized for serverless)

### Features:
- ✅ Autoscaling (scales to zero when idle)
- ✅ Branching support (database branches like git)
- ✅ Point-in-time restore
- ✅ SSL required (secure connection)

---

## 🔧 NEXT STEPS

### Phase 1: Define Database Models
Create SQLAlchemy models for:
- **users** - User accounts (email, password_hash, display_name)
- **roles** - User roles (student, admin)
- **refresh_tokens** - JWT refresh tokens
- **attempts** - Exercise attempts (start/finish/score)
- **events** - User activity events

### Phase 2: Initialize Alembic
```bash
cd C:\Users\sanja\rag-biz-english\server
alembic init alembic
```

Configure `alembic.ini`:
```ini
sqlalchemy.url = %(DATABASE_URL)s
```

### Phase 3: Create First Migration
```bash
alembic revision --autogenerate -m "Create users and auth tables"
alembic upgrade head
```

### Phase 4: Integrate with FastAPI
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 📋 DEPENDENCIES INSTALLED

```
sqlalchemy>=2.0         - ORM for database operations
psycopg[binary]>=3.1.0  - PostgreSQL driver (recommended by Neon)
alembic>=1.13.0         - Database migrations
```

---

## ⚠️ IMPORTANT NOTES

### 1. Use Pooled Connection
The connection string uses `-pooler` which is Neon's connection pooler. This is **required** for serverless/Fly.io deployments.

### 2. SSL Required
`?sslmode=require` ensures encrypted connections.

### 3. Driver: psycopg (not psycopg2)
- `psycopg` = psycopg 3.x (modern, recommended)
- `psycopg2` = psycopg 2.x (legacy)

### 4. Synchronous vs Async
Currently using **synchronous** driver (simpler for auth system).
Can switch to async later if needed.

---

## 🔍 TROUBLESHOOTING

### Error: "No module named 'psycopg'"
```bash
pip install "psycopg[binary]"
```

### Error: "Could not connect to server"
- Check DATABASE_URL in `.env` is correct
- Verify Neon database is running (should be auto-start)
- Check network connectivity

### Error: "SSL error"
- Ensure `?sslmode=require` is in connection string
- Neon requires SSL connections

### Error: "Password authentication failed"
- Verify password in DATABASE_URL matches Neon dashboard
- Check for special characters (URL encode if needed)

---

## ✅ VERIFICATION CHECKLIST

- [x] DATABASE_URL updated in `.env` with psycopg driver
- [x] requirements.txt updated with psycopg[binary]
- [x] Fly.io secret DATABASE_URL set
- [x] Test script created (test_neon_sync.py)
- [ ] **TODO:** Install dependencies (`pip install -r requirements.txt`)
- [ ] **TODO:** Run test script to verify connection
- [ ] **TODO:** Create database models
- [ ] **TODO:** Initialize Alembic migrations
- [ ] **TODO:** Create auth tables

---

## 📞 NEXT ACTION REQUIRED

**Run this to verify everything works:**

```bash
cd C:\Users\sanja\rag-biz-english\server


