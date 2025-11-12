### "Deployment not found" Error
Check Azure deployment names match your setup:
- Chat: `gpt-35-turbo` (not `gpt-3.5-turbo`)
- Embeddings: `text-embedding-3-small`

### 500 Errors on /chat
1. Verify Azure OpenAI key is correct
2. Check deployment name matches
3. Ensure network connectivity to Azure
4. Check server logs for full error

### Ngrok Connection Issues
- Ngrok free tier has 2-hour session limit
- Update URL in Android app after restart
- For production, use stable domain/IP

## Contributing

1. Create feature branch: `git checkout -b feature/auth-system`
2. Make changes and commit: `git commit -m "Add authentication"`
3. Push to GitHub: `git push origin feature/auth-system`
4. Create Pull Request

## License

Proprietary - BizEng-AI

## Support

For issues and questions:
- GitHub Issues: https://github.com/BizEng-AI/backend/issues
- Email: support@bizeng.com

## Roadmap

- [ ] Authentication & role-based access control
- [ ] Student progress tracking dashboard
- [ ] Admin user management
- [ ] Content filter optimization
- [ ] Performance optimization for Postgres
- [ ] Automated testing suite
- [ ] API documentation (Swagger)
- [ ] Rate limiting & abuse prevention
- [ ] Analytics & reporting

---

**Last Updated:** November 7, 2025  
**Current Status:** Production-ready (without auth system)  
**Next Phase:** Authentication & Admin Dashboard
# BizEng Backend Server

## ⚠️ SECURITY REMINDER

**🔐 Before Publishing / Sharing Repository:**
- [ ] **Rotate Qdrant API key** (takes 60 seconds in Qdrant Cloud dashboard)
- [ ] **Rotate all Azure OpenAI keys** (Azure Portal → Regenerate keys)
- [ ] **Rotate Azure Speech key**
- [ ] Verify `.gitignore` is protecting sensitive files
- [ ] Search codebase for any hardcoded credentials: `git grep -i "key\|secret\|password"`
- [ ] Review all markdown documentation for embedded credentials

**📍 Current Status:** 
- Development keys are in use (configured Nov 10, 2025)
- All credentials are in `.env` (gitignored)
- Setup documentation contains example credentials (gitignored)

**🔄 Key Rotation Guide:**
1. Qdrant Cloud: Dashboard → API Keys → Create new → Copy → Update `.env` and Fly.io secrets
2. Azure OpenAI: Azure Portal → Your resource → Keys → Regenerate Key 1 → Update `.env`
3. Fly.io: `fly secrets set QDRANT_API_KEY="new_key" AZURE_OPENAI_KEY="new_key" --app bizeng-server`

---

Production-ready FastAPI server for the Business English learning platform. Provides RAG-backed Q&A, roleplay scenarios, pronunciation assessment, and student progress tracking.

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+ (or SQLite for development)
- Azure OpenAI, Speech, and Qdrant accounts

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/BizEng-AI/backend.git
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.template .env
# Edit .env with your Azure keys and database URL
```

5. **Initialize database** (future: with Alembic migrations)
```bash
# For now, database tables are created on app startup
```

6. **Run the server**
```bash
uvicorn app:app --host 0.0.0.0 --port 8020 --reload
```

Server will be available at `http://localhost:8020`

## Project Structure

```
backend/
├── app.py                    # Main FastAPI application
├── settings.py              # Configuration & environment variables
├── models.py                # SQLAlchemy ORM models (future)
├── auth.py                  # Authentication utilities (future)
├── database.py              # Database connection & sessions (future)
├── requirements.txt         # Python dependencies
├── .env.template            # Environment variable template
├── .gitignore              # Git ignore rules
├── routers/                 # API endpoint routers (future)
│   ├── auth.py             # Authentication endpoints
│   ├── exercises.py        # Exercise catalog
│   ├── attempts.py         # Progress tracking
│   ├── events.py           # Analytics logging
│   └── admin.py            # Admin dashboard
├── roleplay_api.py         # Roleplay endpoints
├── roleplay_engine.py      # Roleplay logic
├── roleplay_referee.py     # Grammar/correction referee
├── roleplay_scenarios.py   # Scenario definitions
├── ingest.py               # Data ingestion utilities
├── start_server.py         # Server startup script
└── README.md               # This file
```

## Core Features

### 1. Chat & RAG
- **POST /chat** - Free-form chat with AI assistant
- **POST /ask** - RAG-backed Q&A using Qdrant vector database
- Uses Azure OpenAI for chat (Sweden Central region)
- Uses Azure Embeddings for vector search (UAE North region)

### 2. Roleplay Scenarios
- **POST /roleplay/start** - Begin a roleplay session
- **POST /roleplay/turn** - Submit a turn and get AI response + corrections
- Scenarios: job interviews, client meetings, complaints, team meetings, phone calls
- Grammar/register/vocabulary feedback

### 3. Pronunciation Assessment
- **POST /pronunciation/assess** - Detailed pronunciation analysis
- **POST /pronunciation/quick-check** - Quick pass/fail check
- Uses Azure Speech Service (East Asia region)
- Returns: accuracy score, fluency, completeness, word-level feedback

### 4. Speech Services
- **POST /stt** - Speech-to-text (via Whisper or Azure)
- **POST /tts** - Text-to-speech audio generation

### 5. Student Progress Tracking (Future)
- **POST /attempts** - Log exercise attempt
- **PATCH /attempts/{id}** - Complete attempt with score
- **POST /events** - Log user interactions
- **GET /progress/my-stats** - Student views own progress
- **GET /admin/students** - Admin views all students
- **GET /admin/students/{id}/summary** - Admin views student details

## Authentication (Future Implementation)

See [AUTH_ADMIN_SYSTEM_PLAN.md](../AUTH_ADMIN_SYSTEM_PLAN.md) for complete authentication architecture.

### Token Strategy
- **Access tokens**: 30 minutes (short-lived)
- **Refresh tokens**: 45 days (rotated on each use)
- JWT-based with Argon2id password hashing
- RBAC with database verification

### Roles
- `student` - Default role, access learning features
- `admin` - Access admin dashboard and user management

## API Endpoints

### Health
- `GET /health` - Server health check
- `GET /version` - API version info

### Chat & RAG
- `POST /chat` - Chat endpoint
- `POST /ask` - RAG Q&A endpoint
- `GET /debug/search?q=query&k=5` - Debug vector search
- `POST /debug/embed` - Debug embedding service

### Roleplay
- `POST /roleplay/start` - Start session
- `POST /roleplay/turn` - Submit turn
- `GET /roleplay/sessions` - List active sessions
- `DELETE /roleplay/session/{session_id}` - Delete session

### Pronunciation
- `POST /pronunciation/assess` - Full assessment
- `POST /pronunciation/quick-check` - Quick check
- `GET /pronunciation/test` - Test service

### Speech
- `POST /stt` - Speech to text
- `POST /tts` - Text to speech

### Admin (Future)
- `POST /auth/login` - Login
- `POST /auth/refresh` - Refresh token
- `POST /auth/logout` - Logout
- `POST /auth/register` - Admin creates user
- `GET /admin/students` - List students
- `GET /admin/students/{id}/summary` - Student stats
- `GET /admin/export.csv` - CSV export

## Azure Services Configuration

### Chat Service (Sweden Central)
```
Endpoint: https://sanja-mh654t02-swedencentral.cognitiveservices.azure.com/
Deployment: gpt-35-turbo
API Version: 2024-12-01-preview
```

### Embeddings Service (UAE North)
```
Endpoint: https://sanja-mh6697hv-uaenorth.cognitiveservices.azure.com/
Deployment: text-embedding-3-small
API Version: 2024-02-15-preview
```

### Speech Service (East Asia)
```
Region: eastasia
Endpoint: https://eastasia.api.cognitive.microsoft.com/
```

## Development

### Running Tests
```bash
pytest
```

### Database Migrations (Future)
```bash
alembic upgrade head  # Apply migrations
alembic downgrade -1  # Rollback
```

### Starting Fresh
```bash
rm bizeng.db  # Delete SQLite database
python app.py  # Restart (creates new DB)
```

## Environment Variables

See `.env.template` for all available configuration options.

**Critical variables:**
- `AZURE_OPENAI_KEY` - Chat service key
- `AZURE_EMBEDDINGS_KEY` - Embeddings service key
- `AZURE_SPEECH_KEY` - Speech service key
- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - JWT signing key (generate with `openssl rand -hex 32`)

## Deployment

### Production Checklist
- [ ] Use PostgreSQL (not SQLite)
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure all Azure keys in .env
- [ ] Generate strong SECRET_KEY
- [ ] Enable HTTPS
- [ ] Set up firewall rules
- [ ] Configure CORS for Android app domain
- [ ] Set up error logging (Sentry, etc.)
- [ ] Configure automated backups

### Using Ngrok for Testing
```bash
# Install ngrok: https://ngrok.com/
ngrok http 8020
# Share the URL with Android app
```

### Docker Deployment (Example)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Architecture

```
Android App
    ↓ (HTTPS + JWT)
FastAPI Server (8020)
    ├─ Chat/RAG
    │   ├→ Azure OpenAI (Sweden)
    │   └→ Azure Embeddings (UAE)
    ├─ Roleplay
    │   ├→ Azure OpenAI (Sweden)
    │   └→ Grammar Referee
    ├─ Pronunciation
    │   └→ Azure Speech (East Asia)
    ├─ Database (future)
    │   └→ PostgreSQL
    └─ Qdrant Vector DB
        └→ Business English documents
```

## Security

- ✅ All secrets in .env (never committed)
- ✅ CORS configured for allowed origins
- ✅ Rate limiting (future)
- ✅ Input validation on all endpoints
- ✅ Argon2id password hashing (future)
- ✅ JWT with short expiry (future)
- ✅ No sensitive data in logs

## Troubleshooting


