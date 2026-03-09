"""
Biz-English API.

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
from fastapi.responses import Response
from openai import AuthenticationError, BadRequestError, NotFoundError, PermissionDeniedError, RateLimitError
from pydantic import BaseModel, field_validator
from qdrant_client.models import SearchParams
from sqlalchemy import text
from sqlalchemy.orm import Session
from tiktoken import get_encoding

from bootstrap import init_db
from db import get_db
from deps import get_optional_user
from roleplay_api import router as roleplay_router
from routers import admin, admin_monitor, auth, me, tracking
from routers.tracking import create_attempt_internal, finish_attempt_internal
from services import (
    expected_embedding_dim,
    get_audio_client,
    get_chat_client,
    get_chat_model_name,
    get_embed_client,
    get_embed_model_name,
    get_qdrant_client,
    get_qdrant_collection_info,
    get_speech_config,
    qdrant_health,
)
from settings import AZURE_SPEECH_REGION, QDRANT_COLLECTION
from tracking import track

@asynccontextmanager
async def lifespan(_app: FastAPI):
    started = time.perf_counter()
    print("[startup] initializing database", flush=True)
    init_db()
    print(f"[startup] database ready in {(time.perf_counter() - started) * 1000:.1f}ms", flush=True)
    yield


app = FastAPI(title="Biz-English API", version="1.1.0", lifespan=lifespan)
_enc = get_encoding("cl100k_base")


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
app.include_router(me.router)
app.include_router(admin.router)
app.include_router(tracking.router)
app.include_router(admin_monitor.router)
app.include_router(roleplay_router)


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


class ChatRespDto(BaseModel):
    answer: str
    sources: list[str] = []


class PeekResp(BaseModel):
    items: List[dict]


class STTResponse(BaseModel):
    text: str



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



def pack_context(hits: list[Any], token_budget: int = 1200) -> str:
    chunks: list[str] = []
    used = 0
    for hit in hits:
        text_value = (hit.payload.get("text") or "").strip()
        if not text_value:
            continue
        token_count = len(_enc.encode(text_value))
        if used + token_count > token_budget:
            continue
        chunks.append(text_value)
        used += token_count
    return "\n\n---\n\n".join(chunks)



def bm25ish_score(text_value: str, query: str) -> int:
    query_words = re.findall(r"\w+", (query or "").lower())
    text_words = set(re.findall(r"\w+", (text_value or "").lower()))
    return sum(1 for word in query_words if word in text_words)



def _vector_collection_size() -> int:
    info = get_qdrant_collection_info()
    vectors = info.config.params.vectors
    if hasattr(vectors, "size"):
        return int(vectors.size)
    if isinstance(vectors, dict) and vectors:
        return int(next(iter(vectors.values())).size)
    raise RuntimeError("Unable to determine Qdrant vector size")



def _retrieve_grounding(query: str, k: int, max_context_chars: int) -> tuple[str, list[str]]:
    try:
        vector_size = _vector_collection_size()
        expected_size = expected_embedding_dim()
        if vector_size != expected_size:
            raise RuntimeError(
                f"Embedding model dimension {expected_size} does not match collection dimension {vector_size}"
            )

        q_emb = get_embed_client().embeddings.create(
            model=get_embed_model_name(),
            input=query,
        ).data[0].embedding

        raw_hits = get_qdrant_client().search(
            collection_name=QDRANT_COLLECTION,
            query_vector=q_emb,
            limit=max(k, 50),
            with_payload=True,
            search_params=SearchParams(hnsw_ef=128, exact=False),
        )
        if not raw_hits:
            return "", []

        raw_hits.sort(
            key=lambda hit: (hit.score or 0.0) + 0.001 * bm25ish_score((hit.payload or {}).get("text", ""), query),
            reverse=True,
        )
        hits = raw_hits[:k]
        context = pack_context(hits, token_budget=1200)
        if len(context) > max_context_chars:
            context = context[:max_context_chars]
        sources = [str((hit.payload or {}).get("source_id") or "") for hit in hits if (hit.payload or {}).get("source_id")]
        return context, sources
    except Exception as exc:
        print(f"[ask] retrieval unavailable: {type(exc).__name__}: {exc}", flush=True)
        return "", []



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
    return {"status": status, "service": "bizeng-server", "checks": checks}


@app.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    database_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        database_status = f"error: {type(exc).__name__}: {exc}"
    vector_store = qdrant_health()
    status = "ok" if database_status == "ok" and vector_store.get("ok") else "degraded"
    return {"status": status, "service": "bizeng-server", "checks": {"database": database_status, "vector_store": vector_store}}


@app.get("/version")
def version():
    return {
        "version": "1.1.0",
        "startup_mode": "lazy-services",
        "features": ["auth", "roleplay", "chat", "pronunciation", "admin_analytics"],
    }


@app.post("/debug/embed")
def debug_embed(payload: EmbReq):
    try:
        vector = get_embed_client().embeddings.create(model=get_embed_model_name(), input=payload.text).data[0].embedding
        return {"dim": len(vector)}
    except Exception as exc:
        traceback.print_exc()
        raise _openai_error_hint(exc, "/debug/embed")


@app.post("/ask", response_model=AskResp)
def ask(payload: AskReq) -> AskResp:
    sanitized_query = sanitize_query(payload.query)
    context, sources = _retrieve_grounding(sanitized_query, payload.k, payload.max_context_chars)
    print(f"[ask] query={ascii_safe(sanitized_query)} context_chars={len(context)} sources={len(sources)}", flush=True)

    system_prompt = (
        "You are a professional Business English teaching assistant. "
        "Use the course materials when they are available. "
        "If the answer is not in the materials, provide helpful business English guidance."
    )
    if context:
        user_prompt = f"Student question: {sanitized_query}\n\nCourse materials:\n{context}"
    else:
        user_prompt = f"Student question: {sanitized_query}\n\nNo grounded materials are currently available, so answer helpfully without inventing citations."

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
                    {"role": "system", "content": "You are a professional Business English teacher. Give concise educational responses."},
                    {"role": "user", "content": f"Please help me with this Business English question: {sanitized_query}"},
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
async def chat(payload: ChatReqDto, user=Depends(get_optional_user), db: Session = Depends(get_db)) -> ChatRespDto:
    started = time.perf_counter()
    attempt = None
    try:
        if user:
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
                    "You are a helpful Business English learning assistant. "
                    "Help students improve professional communication, explain business vocabulary, and provide clear examples."
                ),
            })
        if len(messages) > 20:
            messages = [messages[0]] + messages[-19:]

        if user:
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
            finish_attempt_internal(
                db=db,
                attempt_id=attempt.id,
                duration_seconds=int(time.perf_counter() - started),
                score=None,
                extra_metadata={"response_length": len(answer), "total_messages": len(messages)},
            )
        if user:
            track(user.id, "chat_message", feature="chat", message_length=len(answer))
        return ChatRespDto(answer=answer, sources=[])
    except Exception as exc:
        traceback.print_exc()
        raise _openai_error_hint(exc, "/chat")


@app.get("/debug/search", response_model=PeekResp)
def debug_search(q: str, k: int = 5):
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
async def speech_to_text(file: UploadFile = File(...)):
    temp_path = None
    try:
        content = await file.read()
        suffix = Path(file.filename).suffix if file.filename else ".wav"
        suffix = suffix or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        with open(temp_path, "rb") as audio_file:
            transcript = get_audio_client().audio.transcriptions.create(model="whisper-1", file=audio_file, language="en")
        return STTResponse(text=transcript.text)
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
async def text_to_speech(text: str = Form(...)):
    try:
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
    "meeting": "ˈmiːtɪŋ",
    "business": "ˈbɪznəs",
    "client": "ˈklaɪənt",
    "manager": "ˈmænɪdʒə",
    "project": "ˈprɒdʒekt",
    "deadline": "ˈdedlaɪn",
    "report": "rɪˈpɔːt",
    "agreement": "əˈɡriːmənt",
    "professional": "prəˈfeʃənəl",
}



def get_word_ipa(word: str, phonemes: Optional[List[PronunciationPhoneme]] = None) -> str:
    if phonemes:
        return "".join(item.phoneme for item in phonemes)
    return WORD_IPA_DICT.get(word.lower().strip(".,!?;:"), "")



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

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(await audio.read())
            temp_audio_path = temp_audio.name

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

        if result.reason == speechsdk.ResultReason.NoMatch:
            raise HTTPException(status_code=400, detail="Could not recognize speech. Please speak clearly and try again.")
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
    user=Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    return await _run_pronunciation_assessment(audio, reference_text, user, db)


@app.post("/pronunciation/quick-check")
async def quick_pronunciation_check(
    audio: UploadFile = File(...),
    reference_text: str = Form(...),
    user=Depends(get_optional_user),
    db: Session = Depends(get_db),
):
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



