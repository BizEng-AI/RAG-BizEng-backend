import os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()  # loads .env in this folder

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# JWT Authentication
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
ACCESS_EXPIRES_MIN = int(os.getenv("ACCESS_EXPIRES_MIN", "15"))
REFRESH_EXPIRES_DAYS = int(os.getenv("REFRESH_EXPIRES_DAYS", "30"))
ACCESS_EXPIRES = timedelta(minutes=ACCESS_EXPIRES_MIN)
REFRESH_EXPIRES = timedelta(days=REFRESH_EXPIRES_DAYS)

# Qdrant Configuration (Cloud)
QDRANT_URL = os.getenv("QDRANT_URL", "https://9963ec6f-613b-4fc2-84a7-cdcd7712fed8.eu-central-1-0.aws.cloud.qdrant.io")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "bizeng")

# Azure OpenAI Configuration - Chat (Sweden Central)
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-35-turbo")

# Azure OpenAI Configuration - Embeddings (UAE North - separate region)
AZURE_OPENAI_EMBEDDING_KEY = os.getenv("AZURE_OPENAI_EMBEDDING_KEY", AZURE_OPENAI_KEY)
AZURE_OPENAI_EMBEDDING_ENDPOINT = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT", AZURE_OPENAI_ENDPOINT)
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")

# Azure Speech Service Configuration (for pronunciation assessment)
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "eastasia")

# Fallback to OpenAI if Azure not configured
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")

# Determine which service to use
USE_AZURE = bool(AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT)
USE_AZURE_EMBEDDINGS = bool(AZURE_OPENAI_EMBEDDING_KEY and AZURE_OPENAI_EMBEDDING_ENDPOINT)

if USE_AZURE:
    print(f"[CONFIG] Using Azure OpenAI (Endpoint: {AZURE_OPENAI_ENDPOINT})")
    print(f"[CONFIG] Chat Deployment: {AZURE_OPENAI_CHAT_DEPLOYMENT}")
else:
    print(f"[CONFIG] Using OpenAI API (Fallback mode)")
    print(f"[CONFIG] Chat Model: {CHAT_MODEL}")

if USE_AZURE_EMBEDDINGS:
    print(f"[CONFIG] Using Azure Embeddings (Endpoint: {AZURE_OPENAI_EMBEDDING_ENDPOINT})")
    print(f"[CONFIG] Embedding Deployment: {AZURE_OPENAI_EMBEDDING_DEPLOYMENT}")
else:
    print(f"[CONFIG] Using OpenAI Embeddings (Fallback)")
    print(f"[CONFIG] Embedding Model: {EMBED_MODEL}")

if AZURE_SPEECH_KEY:
    print(f"[CONFIG] Azure Speech Service: {AZURE_SPEECH_REGION}")
else:
    print("[CONFIG] Azure Speech Service: NOT CONFIGURED")
