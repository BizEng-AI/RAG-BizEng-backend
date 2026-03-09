"""
Lazy accessors for external services.

These helpers avoid network calls during module import so the API can boot
quickly and degrade gracefully when optional dependencies are misconfigured.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Optional

import azure.cognitiveservices.speech as speechsdk
from openai import AzureOpenAI, OpenAI
from qdrant_client import QdrantClient

from settings import (
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_CHAT_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_ENDPOINT,
    AZURE_OPENAI_EMBEDDING_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_SPEECH_KEY,
    AZURE_SPEECH_REGION,
    CHAT_MODEL,
    EMBED_MODEL,
    OPENAI_API_KEY,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    QDRANT_URL,
    USE_AZURE,
    USE_AZURE_EMBEDDINGS,
)


def _masked(value: Optional[str], keep: int = 12) -> str:
    if not value:
        return "<missing>"
    return value[:keep] + "..."


@lru_cache(maxsize=1)
def get_chat_client() -> OpenAI | AzureOpenAI:
    if USE_AZURE:
        if not AZURE_OPENAI_KEY or not AZURE_OPENAI_ENDPOINT:
            raise RuntimeError("Azure chat is enabled but AZURE_OPENAI_KEY or AZURE_OPENAI_ENDPOINT is missing")
        print(f"[services] chat_client=azure endpoint={_masked(AZURE_OPENAI_ENDPOINT)}", flush=True)
        return AzureOpenAI(
            api_key=AZURE_OPENAI_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
        )

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing")

    print("[services] chat_client=openai", flush=True)
    return OpenAI(api_key=OPENAI_API_KEY)


@lru_cache(maxsize=1)
def get_embed_client() -> OpenAI | AzureOpenAI:
    if USE_AZURE_EMBEDDINGS:
        if not AZURE_OPENAI_EMBEDDING_KEY or not AZURE_OPENAI_EMBEDDING_ENDPOINT:
            raise RuntimeError(
                "Azure embeddings are enabled but AZURE_OPENAI_EMBEDDING_KEY or AZURE_OPENAI_EMBEDDING_ENDPOINT is missing"
            )
        print(
            f"[services] embed_client=azure endpoint={_masked(AZURE_OPENAI_EMBEDDING_ENDPOINT)}",
            flush=True,
        )
        return AzureOpenAI(
            api_key=AZURE_OPENAI_EMBEDDING_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_EMBEDDING_ENDPOINT,
        )

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing")

    print("[services] embed_client=openai", flush=True)
    return OpenAI(api_key=OPENAI_API_KEY)


@lru_cache(maxsize=1)
def get_audio_client() -> OpenAI | AzureOpenAI:
    if OPENAI_API_KEY:
        print("[services] audio_client=openai", flush=True)
        return OpenAI(api_key=OPENAI_API_KEY)

    if not USE_AZURE:
        return get_chat_client()

    raise RuntimeError("Audio endpoints require OPENAI_API_KEY when chat is configured for Azure OpenAI")


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    if not QDRANT_URL:
        raise RuntimeError("QDRANT_URL is missing")

    print(f"[services] qdrant_client url={_masked(QDRANT_URL, keep=36)} collection={QDRANT_COLLECTION}", flush=True)
    return QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=30,
    )


@lru_cache(maxsize=1)
def get_speech_config() -> Optional[speechsdk.SpeechConfig]:
    if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        print("[services] speech_config=disabled", flush=True)
        return None

    print(f"[services] speech_config region={AZURE_SPEECH_REGION}", flush=True)
    return speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)


@lru_cache(maxsize=1)
def get_qdrant_collection_info() -> Any:
    return get_qdrant_client().get_collection(QDRANT_COLLECTION)


def get_chat_model_name() -> str:
    return AZURE_OPENAI_CHAT_DEPLOYMENT if USE_AZURE else CHAT_MODEL


def get_embed_model_name() -> str:
    return AZURE_OPENAI_EMBEDDING_DEPLOYMENT if USE_AZURE_EMBEDDINGS else EMBED_MODEL


def expected_embedding_dim() -> int:
    return 3072 if "3-large" in get_embed_model_name() else 1536


def _extract_vector_size(collection_info: Any) -> Optional[int]:
    vectors = collection_info.config.params.vectors
    if hasattr(vectors, "size"):
        return vectors.size
    if isinstance(vectors, dict) and vectors:
        first_vector = next(iter(vectors.values()))
        return getattr(first_vector, "size", None)
    return None


def qdrant_health() -> dict[str, Any]:
    status: dict[str, Any] = {
        "configured": bool(QDRANT_URL),
        "collection": QDRANT_COLLECTION,
    }

    if not QDRANT_URL:
        status.update({"ok": False, "error": "QDRANT_URL is not configured"})
        return status

    try:
        info = get_qdrant_collection_info()
        vector_size = _extract_vector_size(info)
        status.update(
            {
                "ok": True,
                "vector_size": vector_size,
                "expected_vector_size": expected_embedding_dim(),
            }
        )
        if vector_size is not None and vector_size != expected_embedding_dim():
            status["ok"] = False
            status["error"] = (
                f"Embedding model dim {expected_embedding_dim()} does not match collection dim {vector_size}"
            )
        return status
    except Exception as exc:  # pragma: no cover - exercised via higher-level tests
        status.update({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
        return status
