import os
from datetime import timedelta

from dotenv import load_dotenv

# Only load .env for local/dev runs. In Fly, rely on platform secrets.
if not os.getenv("FLY_APP_NAME"):
    load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# JWT Authentication
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
ACCESS_EXPIRES_MIN = int(os.getenv("ACCESS_EXPIRES_MIN", "15"))
REFRESH_EXPIRES_DAYS = int(os.getenv("REFRESH_EXPIRES_DAYS", "30"))
ACCESS_EXPIRES = timedelta(minutes=ACCESS_EXPIRES_MIN)
REFRESH_EXPIRES = timedelta(days=REFRESH_EXPIRES_DAYS)
PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "10"))
PASSWORD_MAX_LENGTH = int(os.getenv("PASSWORD_MAX_LENGTH", "128"))

# Qdrant Configuration (Cloud)
QDRANT_URL = os.getenv("QDRANT_URL", "").strip()
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

# Low-volume AI budget guards for the student pilot.
AI_USAGE_LIMITS_ENABLED = os.getenv("AI_USAGE_LIMITS_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
AI_5HOUR_UNIT_LIMIT = int(os.getenv("AI_5HOUR_UNIT_LIMIT", "0"))
AI_DAILY_UNIT_LIMIT = int(os.getenv("AI_DAILY_UNIT_LIMIT", "240"))
AI_WEEKLY_UNIT_LIMIT = int(os.getenv("AI_WEEKLY_UNIT_LIMIT", "1200"))
AI_MONTHLY_UNIT_LIMIT = int(os.getenv("AI_MONTHLY_UNIT_LIMIT", "4800"))
AI_GLOBAL_5HOUR_UNIT_LIMIT = int(os.getenv("AI_GLOBAL_5HOUR_UNIT_LIMIT", "2500"))
AI_GLOBAL_WEEKLY_UNIT_LIMIT = int(os.getenv("AI_GLOBAL_WEEKLY_UNIT_LIMIT", "6000"))
AI_GLOBAL_MONTHLY_UNIT_LIMIT = int(os.getenv("AI_GLOBAL_MONTHLY_UNIT_LIMIT", "22000"))
AI_SPEECH_USER_5HOUR_SECONDS_LIMIT = int(os.getenv("AI_SPEECH_USER_5HOUR_SECONDS_LIMIT", "0"))
AI_SPEECH_USER_DAILY_SECONDS_LIMIT = int(os.getenv("AI_SPEECH_USER_DAILY_SECONDS_LIMIT", "600"))
AI_SPEECH_USER_WEEKLY_SECONDS_LIMIT = int(os.getenv("AI_SPEECH_USER_WEEKLY_SECONDS_LIMIT", "1800"))
AI_SPEECH_USER_MONTHLY_SECONDS_LIMIT = int(os.getenv("AI_SPEECH_USER_MONTHLY_SECONDS_LIMIT", "6000"))
AI_SPEECH_GLOBAL_5HOUR_SECONDS_LIMIT = int(os.getenv("AI_SPEECH_GLOBAL_5HOUR_SECONDS_LIMIT", "14400"))
AI_SPEECH_GLOBAL_WEEKLY_SECONDS_LIMIT = int(os.getenv("AI_SPEECH_GLOBAL_WEEKLY_SECONDS_LIMIT", "54000"))
AI_SPEECH_GLOBAL_MONTHLY_SECONDS_LIMIT = int(os.getenv("AI_SPEECH_GLOBAL_MONTHLY_SECONDS_LIMIT", "180000"))
AI_OPENAI_AUDIO_ENDPOINTS_ENABLED = os.getenv("AI_OPENAI_AUDIO_ENDPOINTS_ENABLED", "false").lower() in {"1", "true", "yes", "on"}

# Basic auth throttles for a low-volume single-server deployment.
AUTH_REGISTER_IP_LIMIT = int(os.getenv("AUTH_REGISTER_IP_LIMIT", "5"))
AUTH_REGISTER_EMAIL_LIMIT = int(os.getenv("AUTH_REGISTER_EMAIL_LIMIT", "3"))
AUTH_REGISTER_WINDOW_SECONDS = int(os.getenv("AUTH_REGISTER_WINDOW_SECONDS", "3600"))
AUTH_LOGIN_FAILURE_IP_LIMIT = int(os.getenv("AUTH_LOGIN_FAILURE_IP_LIMIT", "12"))
AUTH_LOGIN_FAILURE_EMAIL_LIMIT = int(os.getenv("AUTH_LOGIN_FAILURE_EMAIL_LIMIT", "5"))
AUTH_LOGIN_FAILURE_WINDOW_SECONDS = int(os.getenv("AUTH_LOGIN_FAILURE_WINDOW_SECONDS", "900"))
ACCOUNT_DELETE_FAILURE_IP_LIMIT = int(os.getenv("ACCOUNT_DELETE_FAILURE_IP_LIMIT", "5"))
ACCOUNT_DELETE_FAILURE_EMAIL_LIMIT = int(os.getenv("ACCOUNT_DELETE_FAILURE_EMAIL_LIMIT", "3"))
ACCOUNT_DELETE_FAILURE_WINDOW_SECONDS = int(os.getenv("ACCOUNT_DELETE_FAILURE_WINDOW_SECONDS", "3600"))

APP_PUBLIC_NAME = os.getenv("APP_PUBLIC_NAME", "BizEng Chatbot")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "sanjarqodirjanov@gmail.com")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")


def is_production_environment() -> bool:
    environment = (os.getenv("ENVIRONMENT") or os.getenv("APP_ENV") or "").strip().lower()
    return bool(os.getenv("FLY_APP_NAME")) or environment in {"prod", "production"}


def _is_insecure_jwt_secret(secret: str | None) -> bool:
    if not secret:
        return True
    if len(secret) < 32:
        return True
    return secret in {
        "dev-secret-change-in-production",
        "change_this_to_very_long_random_string_in_production_at_least_32_chars",
    }


def validate_runtime_settings() -> None:
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is required")

    if is_production_environment() and _is_insecure_jwt_secret(JWT_SECRET):
        raise RuntimeError(
            "JWT_SECRET must be set to a unique 32+ character secret before starting the production server."
        )


# Determine which service to use
USE_AZURE = bool(AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT)
USE_AZURE_EMBEDDINGS = bool(AZURE_OPENAI_EMBEDDING_KEY and AZURE_OPENAI_EMBEDDING_ENDPOINT)

if USE_AZURE:
    print(f"[CONFIG] Using Azure OpenAI (Endpoint: {AZURE_OPENAI_ENDPOINT})")
    print(f"[CONFIG] Chat Deployment: {AZURE_OPENAI_CHAT_DEPLOYMENT}")
else:
    print("[CONFIG] Using OpenAI API (Fallback mode)")
    print(f"[CONFIG] Chat Model: {CHAT_MODEL}")

if USE_AZURE_EMBEDDINGS:
    print(f"[CONFIG] Using Azure Embeddings (Endpoint: {AZURE_OPENAI_EMBEDDING_ENDPOINT})")
    print(f"[CONFIG] Embedding Deployment: {AZURE_OPENAI_EMBEDDING_DEPLOYMENT}")
else:
    print("[CONFIG] Using OpenAI Embeddings (Fallback)")
    print(f"[CONFIG] Embedding Model: {EMBED_MODEL}")

if AZURE_SPEECH_KEY:
    print(f"[CONFIG] Azure Speech Service: {AZURE_SPEECH_REGION}")
else:
    print("[CONFIG] Azure Speech Service: NOT CONFIGURED")
