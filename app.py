"""
English learning API.

The app uses lazy service initialization so a bad optional dependency (for example,
a broken Qdrant URL) does not prevent the API process from starting.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import time
import traceback
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, List, Optional

import azure.cognitiveservices.speech as speechsdk
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from openai import AuthenticationError, BadRequestError, NotFoundError, PermissionDeniedError, RateLimitError
from pydantic import BaseModel, field_validator
from qdrant_client.models import SearchParams
from sqlalchemy import text
from sqlalchemy.orm import Session

from bootstrap import init_db
from db import get_db
from deps import get_optional_user, require_admin, require_student
from roleplay_api import router as roleplay_router
from routers import admin, admin_monitor, auth, legal, me, tracking
from routers.tracking import create_attempt_internal, finish_attempt_internal
from retrieval import (
    is_material_related_query,
    local_retrieval_health,
    retrieve_grounding,
)
from services import (
    get_audio_client,
    get_chat_client,
    get_chat_model_name,
    get_embed_client,
    get_embed_model_name,
    get_qdrant_client,
    get_speech_config,
    qdrant_health,
)
from settings import (
    AI_OPENAI_AUDIO_ENDPOINTS_ENABLED,
    AZURE_SPEECH_REGION,
    QDRANT_COLLECTION,
    is_production_environment,
    validate_runtime_settings,
)
from tracking import track
from usage_limits import consume_ai_units, get_user_daily_usage_summary

@asynccontextmanager
async def lifespan(_app: FastAPI):
    started = time.perf_counter()
    validate_runtime_settings()
    print("[startup] initializing database", flush=True)
    init_db()
    print(f"[startup] database ready in {(time.perf_counter() - started) * 1000:.1f}ms", flush=True)
    yield


app = FastAPI(
    title="English Learning API",
    version="1.2.0",
    lifespan=lifespan,
    docs_url=None if is_production_environment() else "/docs",
    redoc_url=None if is_production_environment() else "/redoc",
    openapi_url=None if is_production_environment() else "/openapi.json",
)
ENABLE_TOPIC_RETRIEVAL = os.getenv("ENABLE_TOPIC_RETRIEVAL", "true").lower() in {"1", "true", "yes", "on"}
WEB_CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "WEB_CORS_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:4173,http://localhost:4173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=WEB_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_timing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    started = time.perf_counter()
    print(f"[http] -> {request.method} {request.url.path} rid={request_id}", flush=True)
    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = (time.perf_counter() - started) * 1000
        print(
            f"[http] !! {request.method} {request.url.path} rid={request_id} error={type(exc).__name__} duration_ms={duration_ms:.1f}",
            flush=True,
        )
        raise

    duration_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-ms"] = f"{duration_ms:.1f}"
    print(
        f"[http] <- {request.method} {request.url.path} rid={request_id} status={response.status_code} duration_ms={duration_ms:.1f}",
        flush=True,
    )
    return response


app.include_router(auth.router)
app.include_router(legal.router)
app.include_router(me.router)
app.include_router(admin.router)
app.include_router(tracking.router)
app.include_router(admin_monitor.router)
app.include_router(roleplay_router)

MAX_AUDIO_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_AUDIO_SUFFIXES = {
    ".wav",
    ".mp3",
    ".m4a",
    ".mp4",
    ".mpeg",
    ".mpga",
    ".ogg",
    ".webm",
}


class AskReq(BaseModel):
    query: str
    k: int = 5
    max_context_chars: int = 6000
    unit: Optional[str] = None


class AskResp(BaseModel):
    answer: str
    sources: List[str]


class EmbReq(BaseModel):
    text: str


class ChatMessage(BaseModel):
    role: str
    content: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        valid_roles = ["user", "assistant", "system"]
        if value not in valid_roles:
            raise ValueError(f"Invalid role: '{value}'. Must be one of: {valid_roles}")
        return value


class ChatReqDto(BaseModel):
    messages: list[ChatMessage]
    k: int = 5
    maxContextChars: int = 6000
    unit: Optional[str] = None
    use_rag: bool = True


class ChatRespDto(BaseModel):
    answer: str
    sources: list[str] = []


class PeekResp(BaseModel):
    items: List[dict]


class STTResponse(BaseModel):
    text: str


@app.get("/usage/me")
def my_usage_summary(user=Depends(require_student), db: Session = Depends(get_db)):
    return get_user_daily_usage_summary(db, user_id=user.id)


def _validate_audio_upload(file: UploadFile, content: bytes) -> str:
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty")

    if len(content) > MAX_AUDIO_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file exceeds the {MAX_AUDIO_UPLOAD_BYTES // (1024 * 1024)}MB upload limit",
        )

    content_type = (file.content_type or "").lower()
    if content_type and not (
        content_type.startswith("audio/") or content_type in {"application/octet-stream", "application/ogg"}
    ):
        raise HTTPException(status_code=415, detail=f"Unsupported content type '{content_type}'")

    suffix = (Path(file.filename or "audio.wav").suffix or ".wav").lower()
    if suffix not in ALLOWED_AUDIO_SUFFIXES:
        allowed = ", ".join(sorted(ALLOWED_AUDIO_SUFFIXES))
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported audio format '{suffix}'. Allowed formats: {allowed}",
        )

    return suffix


def _estimate_audio_seconds(file: UploadFile, content: bytes) -> float:
    suffix = (Path(file.filename or "").suffix or "").lower()
    content_type = (file.content_type or "").lower()
    if (suffix == ".wav" or content_type in {"audio/wav", "audio/x-wav"}) and len(content) >= 44:
        try:
            channels = int.from_bytes(content[22:24], "little")
            sample_rate = int.from_bytes(content[24:28], "little")
            bits_per_sample = int.from_bytes(content[34:36], "little")
            data_index = content.find(b"data")
            if channels > 0 and sample_rate > 0 and bits_per_sample > 0 and data_index != -1 and data_index + 8 <= len(content):
                data_size = int.from_bytes(content[data_index + 4:data_index + 8], "little")
                bytes_per_second = sample_rate * channels * (bits_per_sample / 8)
                if bytes_per_second > 0:
                    return max(0.1, data_size / bytes_per_second)
        except Exception:
            pass
    # Conservative fallback for compressed browser audio: charge at least a short practice turn.
    return 15.0



def ascii_safe(value: str) -> str:
    try:
        return value.encode("ascii", "ignore").decode("ascii")
    except Exception:
        return "<non-ascii>"



def sanitize_query(query: str) -> str:
    informal_to_formal = {
        "yo": "hello",
        "sup": "how are you",
        "hey": "hello",
        "wassup": "what is happening",
        "u": "you",
        "ur": "your",
        "r": "are",
        "pls": "please",
        "thx": "thank you",
        "thnx": "thank you",
    }

    sanitized = query.lower()
    for informal, formal in informal_to_formal.items():
        sanitized = sanitized.replace(f" {informal} ", f" {formal} ")
        if sanitized.startswith(f"{informal} "):
            sanitized = f"{formal}{sanitized[len(informal):]}"
        if sanitized.endswith(f" {informal}"):
            sanitized = f"{sanitized[:-len(informal)]}{formal}"
    return sanitized if sanitized != query.lower() else query



def _is_query_retrieval_relevant(query: str) -> bool:
    return is_material_related_query(query)


def _count_words(text: str) -> int:
    return len([part for part in (text or "").strip().split() if part])



def _retrieve_grounding(query: str, k: int, max_context_chars: int) -> tuple[str, list[str]]:
    result = retrieve_grounding(query=query, k=k, max_context_chars=max_context_chars)
    if result.degraded_reason:
        print(f"[ask] retrieval degraded backend={result.backend} reason={result.degraded_reason}", flush=True)
    else:
        print(f"[ask] retrieval backend={result.backend}", flush=True)
    return result.context, result.sources



def _openai_error_hint(exc: Exception, endpoint: str) -> HTTPException:
    if isinstance(exc, BadRequestError):
        message = ""
        try:
            message = exc.response.json().get("error", {}).get("message", "") or exc.response.json().get("message", "")
        except Exception:
            message = str(exc)
        return HTTPException(status_code=500, detail=f"{endpoint} failed: BadRequestError: {ascii_safe(message)}")
    if isinstance(exc, AuthenticationError):
        return HTTPException(status_code=500, detail=f"{endpoint} failed: AuthenticationError")
    if isinstance(exc, PermissionDeniedError):
        return HTTPException(status_code=500, detail=f"{endpoint} failed: PermissionDeniedError")
    if isinstance(exc, RateLimitError):
        return HTTPException(status_code=500, detail=f"{endpoint} failed: RateLimitError")
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=500, detail=f"{endpoint} failed: NotFoundError")
    return HTTPException(status_code=500, detail=f"{endpoint} failed: {type(exc).__name__}: {exc}")


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    checks = {"database": "ok", "vector_store": "not_probed"}
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        checks["database"] = f"error: {type(exc).__name__}: {exc}"
    status = "ok" if checks["database"] == "ok" else "degraded"
    return {"status": status, "service": "bizeng-chatbot-server", "checks": checks}


@app.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    database_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        database_status = f"error: {type(exc).__name__}: {exc}"
    vector_store = qdrant_health()
    local_store = local_retrieval_health()
    retrieval_ok = bool(vector_store.get("ok") or local_store.get("ok"))
    status = "ok" if database_status == "ok" and retrieval_ok else "degraded"
    preferred_backend = "qdrant" if vector_store.get("ok") else ("local_lexical" if local_store.get("ok") else "none")
    return {
        "status": status,
        "service": "bizeng-chatbot-server",
        "checks": {
            "database": database_status,
            "vector_store": vector_store,
            "local_store": local_store,
            "preferred_retrieval_backend": preferred_backend,
        },
    }


@app.get("/version")
def version():
    return {
        "version": "1.1.0",
        "startup_mode": "lazy-services",
        "features": ["auth", "roleplay", "chat", "pronunciation", "admin_analytics"],
    }


@app.post("/debug/embed")
def debug_embed(payload: EmbReq, _user=Depends(require_admin)):
    try:
        vector = get_embed_client().embeddings.create(model=get_embed_model_name(), input=payload.text).data[0].embedding
        return {"dim": len(vector)}
    except Exception as exc:
        traceback.print_exc()
        raise _openai_error_hint(exc, "/debug/embed")


@app.post("/ask", response_model=AskResp)
def ask(payload: AskReq, user=Depends(require_student), db: Session = Depends(get_db)) -> AskResp:
    sanitized_query = sanitize_query(payload.query)
    context, sources = (_retrieve_grounding(sanitized_query, payload.k, payload.max_context_chars) if ENABLE_TOPIC_RETRIEVAL else ("", []))
    print(f"[ask] query_length={len(sanitized_query)} context_chars={len(context)} sources={len(sources)}", flush=True)
    consume_ai_units(
        db,
        user_id=user.id,
        route="ask",
        extra_metadata={"query_length": len(sanitized_query), "sources": len(sources)},
    )

    system_prompt = (
        "You are a friendly English coach for A2-B1 learners. B2 is the highest level allowed. "
        "Use short sentences and common words first. Avoid idioms, slang, long academic words, and formal business jargon. "
        "If a hard business word is useful, explain it in simple English. "
        "Use grounded course materials when they are available. "
        "If grounded materials are unavailable, still help with grammar, vocabulary, speaking, reading, listening, writing, and topic review in clear English. "
        "Keep answers short. Use 2-4 bullets when a list helps."
    )
    if context:
        user_prompt = f"Student question: {sanitized_query}\n\nReference materials:\n{context}"
    else:
        user_prompt = f"Student question: {sanitized_query}\n\nGrounded reference materials are not currently available, so answer helpfully without inventing citations."

    try:
        response = get_chat_client().chat.completions.create(
            model=get_chat_model_name(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=300,
            temperature=0.2,
            timeout=45,
        )
        return AskResp(answer=response.choices[0].message.content, sources=sources)
    except BadRequestError as exc:
        message = ""
        try:
            message = str(exc.response.json())
        except Exception:
            message = str(exc)
        if "content management policy" in message.lower() or "content_filter" in message.lower():
            fallback = get_chat_client().chat.completions.create(
                model=get_chat_model_name(),
                messages=[
                    {"role": "system", "content": "You are a concise English tutor. Give short, practical educational responses."},
                    {"role": "user", "content": f"Please help me with this English-learning question: {sanitized_query}"},
                ],
                max_tokens=300,
                temperature=0.7,
                timeout=45,
            )
            return AskResp(answer=fallback.choices[0].message.content, sources=[])
        raise _openai_error_hint(exc, "/ask")
    except Exception as exc:
        traceback.print_exc()
        raise _openai_error_hint(exc, "/ask")


@app.post("/chat", response_model=ChatRespDto)
async def chat(payload: ChatReqDto, user=Depends(require_student), db: Session = Depends(get_db)) -> ChatRespDto:
    started = time.perf_counter()
    attempt = None
    try:
        consume_ai_units(
            db,
            user_id=user.id,
            route="chat",
            extra_metadata={"message_count": len(payload.messages)},
        )
        attempt = create_attempt_internal(
            db=db,
            user_id=user.id,
            exercise_type="chat",
            exercise_id=f"chat_{int(time.time())}",
            extra_metadata={"message_count": len(payload.messages)},
        )

        messages = [{"role": item.role, "content": item.content} for item in payload.messages]
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {
                "role": "system",
                "content": (
                    "You are a friendly English coach for A2-B1 learners. B2 is the highest level allowed. "
                    "Use short sentences and common words first. Avoid idioms, slang, long academic words, and formal business jargon. "
                    "If a hard business word is useful, explain it in simple English. "
                    "Help with grammar, vocabulary, reading, listening, writing, speaking, and short topic explanations using clear examples. "
                    "Keep the focus on work, study, travel, trade, meetings, email, and daily tasks when relevant."
                ),
            })

        latest_user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                latest_user_message = (msg.get("content") or "").strip()
                break

        sources: list[str] = []
        if ENABLE_TOPIC_RETRIEVAL and payload.use_rag and _is_query_retrieval_relevant(latest_user_message):
            context, sources = _retrieve_grounding(
                query=sanitize_query(latest_user_message),
                k=payload.k,
                max_context_chars=payload.maxContextChars,
            )
            if context:
                messages.insert(1, {
                    "role": "system",
                    "content": (
                        "Use these reference materials when relevant. "
                        "If the prompt is general, answer naturally without forced citations.\n\n"
                        f"{context}"
                    ),
                })

        if len(messages) > 20:
            messages = [messages[0]] + messages[-19:]

        track(user.id, "chat_opened", feature="chat", message_count=len(messages))

        response = get_chat_client().chat.completions.create(
            model=get_chat_model_name(),
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            timeout=45,
        )
        answer = response.choices[0].message.content
        if not answer:
            raise ValueError("Empty response from model")

        if attempt:
            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            latest_user_words = _count_words(latest_user_message)
            finish_attempt_internal(
                db=db,
                attempt_id=attempt.id,
                duration_seconds=max(1, int(time.perf_counter() - started)),
                score=None,
                extra_metadata={
                    "response_length": len(answer),
                    "total_messages": len(messages),
                    "message_count": len(user_messages),
                    "word_count": latest_user_words,
                    "user_message_words": latest_user_words,
                    "input_char_count": len(latest_user_message),
                    "assistant_words": _count_words(answer),
                },
            )
        track(user.id, "chat_message", feature="chat", message_length=len(answer))
        return ChatRespDto(answer=answer, sources=sources)
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise _openai_error_hint(exc, "/chat")


@app.get("/debug/search", response_model=PeekResp)
def debug_search(q: str, k: int = 5, _user=Depends(require_admin)):
    try:
        vector = get_embed_client().embeddings.create(model=get_embed_model_name(), input=q).data[0].embedding
        hits = get_qdrant_client().search(
            collection_name=QDRANT_COLLECTION,
            query_vector=vector,
            limit=k,
            with_payload=True,
            search_params=SearchParams(hnsw_ef=128, exact=False),
        )
        items = []
        for hit in hits:
            payload = hit.payload or {}
            items.append({
                "score": hit.score,
                "src": payload.get("source_id"),
                "unit": payload.get("unit"),
                "snippet": (payload.get("text", "")[:300]).replace("\n", " "),
            })
        return PeekResp(items=items)
    except Exception as exc:
        raise _openai_error_hint(exc, "/debug/search")


@app.post("/stt", response_model=STTResponse)
async def speech_to_text(
    file: UploadFile = File(...),
    user=Depends(require_student),
    db: Session = Depends(get_db),
):
    temp_path = None
    try:
        content = await file.read()
        suffix = _validate_audio_upload(file, content)
        if not AI_OPENAI_AUDIO_ENDPOINTS_ENABLED:
            raise HTTPException(status_code=403, detail="Speech-to-text is disabled to control AI spending.")
        audio_seconds = _estimate_audio_seconds(file, content)
        consume_ai_units(
            db,
            user_id=user.id,
            route="stt",
            extra_metadata={"bytes": len(content), "content_type": file.content_type, "audio_seconds": audio_seconds},
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        with open(temp_path, "rb") as audio_file:
            transcript = get_audio_client().audio.transcriptions.create(model="whisper-1", file=audio_file, language="en")
        return STTResponse(text=transcript.text)
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise _openai_error_hint(exc, "/stt")
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as exc:
                print(f"[stt] failed to remove temp file: {exc}", flush=True)


@app.post("/tts")
async def text_to_speech(
    text: str = Form(...),
    user=Depends(require_student),
    db: Session = Depends(get_db),
):
    if not AI_OPENAI_AUDIO_ENDPOINTS_ENABLED:
        raise HTTPException(status_code=403, detail="Text-to-speech is disabled to control AI spending.")

    try:
        consume_ai_units(
            db,
            user_id=user.id,
            route="tts",
            extra_metadata={"text_length": len(text)},
        )
        response = get_audio_client().audio.speech.create(model="tts-1", voice="alloy", input=text, response_format="mp3")
        return Response(content=response.content, media_type="audio/mpeg", headers={"Content-Disposition": "attachment; filename=speech.mp3"})
    except Exception as exc:
        traceback.print_exc()
        raise _openai_error_hint(exc, "/tts")

class PronunciationPhoneme(BaseModel):
    phoneme: str
    score: float


class PronunciationWord(BaseModel):
    word: str
    accuracy_score: float
    error_type: Optional[str] = None
    phonemes: Optional[List[PronunciationPhoneme]] = None
    ipa_expected: Optional[str] = None
    ipa_actual: Optional[str] = None
    feedback: Optional[str] = None


class PronunciationResult(BaseModel):
    transcript: str
    accuracy_score: float
    fluency_score: float
    completeness_score: float
    pronunciation_score: float
    words: List[PronunciationWord]
    feedback: str
    detailed_feedback: Optional[List[str]] = None


PHONETIC_TIPS = {
    "ɪ": "Short 'i' sound as in 'sit'. Relax your tongue slightly.",
    "æ": "'a' sound as in 'cat'. Open your mouth wider and keep your tongue low.",
    "ə": "Schwa, the unstressed 'uh' sound. It is very common in English.",
    "θ": "'th' as in 'think'. Put your tongue between your teeth and blow air.",
    "ð": "'th' as in 'this'. Use the same position as 'think' but add voice.",
    "ʃ": "'sh' as in 'ship'. Round your lips slightly forward.",
    "dʒ": "'j' as in 'judge'. Start with a brief 'd' and release into 'zh'.",
    "ŋ": "'ng' as in 'sing'. Block the air with the back of your tongue.",
}

WORD_IPA_DICT = {
    "hello": "həˈləʊ",
    "education": "ˌedʒuˈkeɪʃən",
    "university": "ˌjuːnɪˈvɜːsəti",
    "festival": "ˈfestɪvəl",
    "tradition": "trəˈdɪʃən",
    "market": "ˈmɑːkɪt",
    "budget": "ˈbʌdʒɪt",
    "supply": "səˈplaɪ",
    "demand": "dɪˈmɑːnd",
    "economics": "ˌiːkəˈnɒmɪks",
}



def get_word_ipa(word: str, phonemes: Optional[List[PronunciationPhoneme]] = None) -> str:
    clean_word = re.sub(r"[^a-z']", "", (word or "").lower())
    if not clean_word:
        return ""

    if phonemes:
        phoneme_joined = "".join(item.phoneme for item in phonemes if item.phoneme)
        if phoneme_joined.strip():
            return phoneme_joined

    dictionary_ipa = WORD_IPA_DICT.get(clean_word)
    if dictionary_ipa:
        return dictionary_ipa

    transformed = clean_word
    for source, target in [
        ("tion", "ʃən"),
        ("sion", "ʒən"),
        ("ough", "oʊ"),
        ("eigh", "eɪ"),
        ("igh", "aɪ"),
        ("ph", "f"),
        ("th", "θ"),
        ("ch", "tʃ"),
        ("sh", "ʃ"),
        ("ng", "ŋ"),
        ("ee", "iː"),
        ("oo", "uː"),
        ("ea", "iː"),
        ("ou", "aʊ"),
        ("ow", "aʊ"),
        ("ai", "eɪ"),
        ("ay", "eɪ"),
        ("oa", "oʊ"),
        ("qu", "kw"),
        ("x", "ks"),
    ]:
        transformed = transformed.replace(source, target)

    single_map = {
        "a": "æ",
        "b": "b",
        "c": "k",
        "d": "d",
        "e": "e",
        "f": "f",
        "g": "g",
        "h": "h",
        "i": "ɪ",
        "j": "dʒ",
        "k": "k",
        "l": "l",
        "m": "m",
        "n": "n",
        "o": "ɒ",
        "p": "p",
        "q": "k",
        "r": "r",
        "s": "s",
        "t": "t",
        "u": "ʌ",
        "v": "v",
        "w": "w",
        "y": "j",
        "z": "z",
        "'": "",
    }

    return "".join(single_map.get(char, char) for char in transformed)



def get_phonetic_tip(phoneme: str) -> Optional[str]:
    clean = phoneme.replace("ˈ", "").replace("ˌ", "").replace("ː", "")
    return PHONETIC_TIPS.get(clean)



def generate_word_feedback(
    word: str,
    accuracy: float,
    error_type: Optional[str],
    phonemes: Optional[List[PronunciationPhoneme]],
) -> Optional[str]:
    if error_type == "Omission":
        return f"You skipped the word '{word}'. Make sure to pronounce every word clearly."
    if error_type == "Insertion":
        return f"You added the word '{word}' even though it was not in the text."
    if error_type == "Mispronunciation" or accuracy < 60:
        feedback_parts = [f"Work on '{word}'."]
        problem_phonemes = [item for item in (phonemes or []) if item.score < 60]
        for item in problem_phonemes[:2]:
            tip = get_phonetic_tip(item.phoneme)
            if tip:
                feedback_parts.append(f"Focus on /{item.phoneme}/: {tip}")
        if not problem_phonemes:
            feedback_parts.append("Listen to the correct pronunciation and repeat slowly.")
            feedback_parts.append("Break the word into syllables and practice each part.")
        return " ".join(feedback_parts)
    return None



def generate_pronunciation_feedback(
    overall_score: float,
    accuracy_score: float,
    fluency_score: float,
    words: List[PronunciationWord],
) -> tuple[str, List[str]]:
    feedback_parts: list[str] = []
    detailed_tips: list[str] = []

    if overall_score >= 95:
        feedback_parts.append("Outstanding pronunciation. Nearly native-like.")
    elif overall_score >= 85:
        feedback_parts.append("Excellent pronunciation. Very clear and natural.")
    elif overall_score >= 75:
        feedback_parts.append("Good pronunciation. A few minor areas can improve.")
    elif overall_score >= 60:
        feedback_parts.append("Fair pronunciation. Focus on a few specific sounds.")
    elif overall_score >= 40:
        feedback_parts.append("Needs practice. Focus on the highlighted words.")
    else:
        feedback_parts.append("Let's practice together. Slow down and focus on clarity.")

    mispronounced = [word for word in words if word.accuracy_score < 70 or word.error_type in ["Mispronunciation", "Omission"]]
    if mispronounced:
        if len(mispronounced) == 1:
            feedback_parts.append(f"Focus on '{mispronounced[0].word}'.")
        else:
            feedback_parts.append("Words to practice: " + ", ".join(f"'{word.word}'" for word in mispronounced[:5]) + ".")
        for word in mispronounced[:3]:
            tip = generate_word_feedback(word.word, word.accuracy_score, word.error_type, word.phonemes)
            if tip:
                detailed_tips.append(tip)

    if fluency_score < 60:
        feedback_parts.append("Fluency tip: speak more smoothly with fewer pauses.")
        detailed_tips.append("Practice reading the sentence several times to build rhythm.")
    elif fluency_score < 80:
        feedback_parts.append("Fluency tip: good pace, but try to sound more natural and steady.")

    if accuracy_score < 60:
        feedback_parts.append("Accuracy tip: focus on each sound clearly and do not rush.")
        detailed_tips.append("Record yourself and compare with a native speaker.")
    elif accuracy_score < 80:
        feedback_parts.append("Accuracy tip: pay attention to stress and intonation.")

    omitted = [word for word in words if word.error_type == "Omission"]
    if omitted:
        feedback_parts.append("You missed: " + ", ".join(f"'{word.word}'" for word in omitted) + ".")
        detailed_tips.append("Make sure to pronounce every word in the sentence.")

    return " ".join(feedback_parts), detailed_tips


async def _run_pronunciation_assessment(
    audio: UploadFile,
    reference_text: str,
    user,
    db: Session,
) -> PronunciationResult:
    speech_config = get_speech_config()
    if speech_config is None:
        raise HTTPException(status_code=503, detail="Azure Speech Service is not configured")

    started = time.perf_counter()
    attempt = None
    temp_audio_path = None

    try:
        if user:
            attempt = create_attempt_internal(
                db=db,
                user_id=user.id,
                exercise_type="pronunciation",
                exercise_id=f"pron_{int(time.time())}",
                extra_metadata={"reference_text": reference_text[:100]},
            )

        audio_content = await audio.read()
        audio_suffix = _validate_audio_upload(audio, audio_content)

        with tempfile.NamedTemporaryFile(delete=False, suffix=audio_suffix) as temp_audio:
            temp_audio.write(audio_content)
            temp_audio_path = temp_audio.name

        try:
            audio_config = speechsdk.AudioConfig(filename=temp_audio_path)
            assessment_config = speechsdk.PronunciationAssessmentConfig(
                reference_text=reference_text,
                grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
                granularity=speechsdk.PronunciationAssessmentGranularity.Word,
                enable_miscue=True,
            )
            recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
            assessment_config.apply_to(recognizer)
            result = recognizer.recognize_once()
        except RuntimeError as exc:
            message = str(exc)
            if "SPXERR_INVALID_HEADER" in message:
                raise HTTPException(
                    status_code=415,
                    detail="The audio format could not be read. Record again in the browser and submit WAV audio.",
                ) from exc
            print(f"[pronunciation] Azure Speech SDK failed: {exc}", flush=True)
            raise HTTPException(
                status_code=502,
                detail="Speech service could not process the audio. Please try again.",
            ) from exc

        if result.reason == speechsdk.ResultReason.NoMatch:
            raise HTTPException(status_code=400, detail="Could not recognize speech. Please speak clearly and try again.")
        if result.reason == speechsdk.ResultReason.Canceled:
            details = speechsdk.CancellationDetails(result)
            raise HTTPException(status_code=502, detail=f"Speech recognition was canceled: {details.reason}")
        if result.reason != speechsdk.ResultReason.RecognizedSpeech:
            raise HTTPException(status_code=500, detail=f"Speech recognition failed: {result.reason}")

        pronunciation_result = speechsdk.PronunciationAssessmentResult(result)
        words: list[PronunciationWord] = []
        raw_details = result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult)
        if raw_details:
            parsed = json.loads(raw_details)
            for word_info in parsed.get("NBest", [{}])[0].get("Words", []):
                assessment = word_info.get("PronunciationAssessment", {})
                word_text = word_info.get("Word", "")
                error_type = assessment.get("ErrorType")
                phonemes: list[PronunciationPhoneme] = []
                for phoneme_info in word_info.get("Phonemes", []):
                    phonemes.append(
                        PronunciationPhoneme(
                            phoneme=phoneme_info.get("Phoneme", ""),
                            score=phoneme_info.get("PronunciationAssessment", {}).get("AccuracyScore", 0),
                        )
                    )
                words.append(
                    PronunciationWord(
                        word=word_text,
                        accuracy_score=assessment.get("AccuracyScore", 0),
                        error_type=error_type,
                        phonemes=phonemes or None,
                        ipa_expected=get_word_ipa(word_text, phonemes or None) or None,
                        ipa_actual=None,
                        feedback=generate_word_feedback(
                            word_text,
                            assessment.get("AccuracyScore", 0),
                            error_type,
                            phonemes or None,
                        ),
                    )
                )

        feedback, detailed_tips = generate_pronunciation_feedback(
            pronunciation_result.pronunciation_score,
            pronunciation_result.accuracy_score,
            pronunciation_result.fluency_score,
            words,
        )

        if attempt:
            finish_attempt_internal(
                db=db,
                attempt_id=attempt.id,
                duration_seconds=int(time.perf_counter() - started),
                score=pronunciation_result.pronunciation_score,
                passed=pronunciation_result.pronunciation_score >= 70.0,
                extra_metadata={
                    "accuracy": pronunciation_result.accuracy_score,
                    "fluency": pronunciation_result.fluency_score,
                    "completeness": pronunciation_result.completeness_score,
                },
            )

        return PronunciationResult(
            transcript=result.text,
            accuracy_score=pronunciation_result.accuracy_score,
            fluency_score=pronunciation_result.fluency_score,
            completeness_score=pronunciation_result.completeness_score,
            pronunciation_score=pronunciation_result.pronunciation_score,
            words=words,
            feedback=feedback,
            detailed_feedback=detailed_tips or None,
        )
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
            except Exception as exc:
                print(f"[pronunciation] failed to remove temp file: {exc}", flush=True)

@app.post("/pronunciation/assess", response_model=PronunciationResult)
async def assess_pronunciation(
    audio: UploadFile = File(...),
    reference_text: str = Form(...),
    user=Depends(require_student),
    db: Session = Depends(get_db),
):
    audio_content = await audio.read()
    audio_suffix = _validate_audio_upload(audio, audio_content)
    audio_seconds = _estimate_audio_seconds(audio, audio_content)
    await audio.seek(0)
    consume_ai_units(
        db,
        user_id=user.id,
        route="pronunciation_assess",
        extra_metadata={
            "reference_length": len(reference_text),
            "audio_seconds": audio_seconds,
            "audio_suffix": audio_suffix,
        },
    )
    return await _run_pronunciation_assessment(audio, reference_text, user, db)


@app.post("/pronunciation/quick-check")
async def quick_pronunciation_check(
    audio: UploadFile = File(...),
    reference_text: str = Form(...),
    user=Depends(require_student),
    db: Session = Depends(get_db),
):
    audio_content = await audio.read()
    audio_suffix = _validate_audio_upload(audio, audio_content)
    audio_seconds = _estimate_audio_seconds(audio, audio_content)
    await audio.seek(0)
    consume_ai_units(
        db,
        user_id=user.id,
        route="pronunciation_quick_check",
        extra_metadata={
            "reference_length": len(reference_text),
            "audio_seconds": audio_seconds,
            "audio_suffix": audio_suffix,
        },
    )
    result = await _run_pronunciation_assessment(audio, reference_text, user, db)
    return {
        "score": round(result.pronunciation_score, 1),
        "feedback": result.feedback,
        "transcript": result.transcript,
        "needs_practice": result.pronunciation_score < 70,
        "mispronounced_words": [
            word.word
            for word in result.words
            if word.accuracy_score < 60 or word.error_type == "Mispronunciation"
        ],
    }


@app.get("/pronunciation/test")
async def test_pronunciation_service():
    if get_speech_config() is None:
        raise HTTPException(status_code=503, detail="Azure Speech Service is not configured")
    return {
        "status": "ok",
        "region": AZURE_SPEECH_REGION,
        "service": "Azure Speech Service",
        "features": [
            "Pronunciation Assessment",
            "Word-level scoring",
            "Fluency analysis",
            "Accuracy measurement",
        ],
    }





