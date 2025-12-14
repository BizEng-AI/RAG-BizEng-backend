# BizEng - Business English Learning Platform
Backend API server for the BizEng English learning application.
## Features
- User authentication and authorization
- RAG-based chat with business English content
- Interactive roleplay scenarios
- Student progress tracking
- Admin monitoring dashboard
## Tech Stack
- FastAPI
- PostgreSQL (Neon)
- Qdrant Vector Database
- Azure OpenAI
- JWT Authentication
## Setup
1. Install dependencies:
`
pip install -r requirements.txt
`
2. Configure environment variables (see .env.template)
3. Run the server:
`
uvicorn app:app --host 0.0.0.0 --port 8000
`
## Deployment
Deployed on Fly.io. See ly.toml for configuration.
## API Documentation
Once running, visit /docs for interactive API documentation.
