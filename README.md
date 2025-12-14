# BizEng Server

Backend server for BizEng - an AI-powered English learning platform for business professionals.

## Features

- **AI Chat Assistant**: Personalized English learning conversations
- **Roleplay Scenarios**: Practice real business situations
- **RAG-based Context**: Retrieve relevant content from curated business English materials
- **User Tracking**: Monitor learning progress and engagement
- **Admin Dashboard**: Manage users and monitor system usage

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (Neon)
- **Vector Store**: Qdrant Cloud
- **AI**: Azure OpenAI (GPT-4, text-embedding-3-large)
- **Deployment**: Fly.io

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL database (Neon recommended)
- Qdrant vector database
- Azure OpenAI API access

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.template` to `.env` and configure:
   ```bash
   cp .env.template .env
   ```

4. Set up environment variables in `.env`:
   - Database credentials (Neon)
   - Qdrant connection details
   - Azure OpenAI API keys
   - JWT secret

5. Ingest content into Qdrant:
   ```bash
   python ingest.py
   ```

6. Run the server:
   ```bash
   uvicorn app:app --reload
   ```

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - User login
- `POST /refresh` - Refresh access token

### Chat & Learning
- `POST /chat` - General chat with AI assistant
- `POST /search` - Search knowledge base
- `POST /tts` - Text-to-speech

### Roleplay
- `GET /roleplay/scenarios` - List available scenarios
- `POST /roleplay/start` - Start roleplay session
- `POST /roleplay/message` - Send message in roleplay
- `GET /roleplay/session/{id}` - Get session details
- `POST /roleplay/hint` - Get hint for current stage

### User
- `GET /me` - Get current user profile
- `GET /me/progress` - Get learning progress

### Admin
- `GET /admin/users` - List all users
- `GET /admin/monitor/*` - Various monitoring endpoints

## Project Structure

```
server/
├── app.py                 # Main FastAPI application
├── models.py             # Database models
├── schemas.py            # Pydantic schemas
├── security.py           # Authentication & authorization
├── settings.py           # Configuration
├── db.py                 # Database connection
├── deps.py               # Dependency injection
├── tracking.py           # User activity tracking
├── ingest.py             # Content ingestion script
├── routers/              # API route modules
│   ├── auth.py
│   ├── admin.py
│   ├── admin_monitor.py
│   ├── me.py
│   └── tracking.py
├── roleplay_engine.py    # Core roleplay logic
├── roleplay_session.py   # Session management
├── roleplay_scenarios.py # Scenario definitions
├── roleplay_referee.py   # Response evaluation
├── roleplay_api.py       # Roleplay API endpoints
└── sessions/             # Roleplay session storage
```

## Deployment

The server is configured for deployment on Fly.io:

```bash
flyctl deploy
```

## License

Proprietary - All rights reserved

## Contact

For questions or support, please contact the development team.

