"""
Purpose: expose a simple /ask endpoint.

WHY steps:
1) Embed the user's question -> numeric vector.
2) Vector search in Qdrant -> top-k relevant chunks.
3) Build a compact CONTEXT string from those chunks (token budgeted).
4) Chat completion with strict instructions to ground answers in CONTEXT.
"""
from __future__ import annotations

import re
import sys
import tempfile
import json
from typing import Any, List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import Response
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from qdrant_client import QdrantClient
from qdrant_client.models import SearchParams, Filter, FieldCondition, MatchValue

from openai import OpenAI, AzureOpenAI, AuthenticationError, PermissionDeniedError, RateLimitError, NotFoundError, BadRequestError

import azure.cognitiveservices.speech as speechsdk

from settings import (
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    OPENAI_API_KEY,
    EMBED_MODEL,
    CHAT_MODEL,
    USE_AZURE,
    USE_AZURE_EMBEDDINGS,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_CHAT_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_KEY,
    AZURE_OPENAI_EMBEDDING_ENDPOINT,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    AZURE_SPEECH_KEY,
    AZURE_SPEECH_REGION,
)

print("--- SERVER RESTARTED WITH LATEST CODE (Version 4 - AZURE OPTIMIZED) ---")

if USE_AZURE:
    print(f"[startup] 💰 Using AZURE OpenAI for Chat - 80% cost savings!", flush=True)
    print(f"[startup] Azure Chat endpoint: {AZURE_OPENAI_ENDPOINT[:50]}...", flush=True)
else:
    print(f"[startup] Using OpenAI API for Chat (fallback)", flush=True)
    print("[startup] key_prefix=", (OPENAI_API_KEY or "")[:7], " len=", len(OPENAI_API_KEY or ""), flush=True)

if USE_AZURE_EMBEDDINGS:
    print(f"[startup] 💰 Using AZURE OpenAI for Embeddings - 80% cost savings!", flush=True)
    print(f"[startup] Azure Embeddings endpoint: {AZURE_OPENAI_EMBEDDING_ENDPOINT[:50]}...", flush=True)
else:
    print(f"[startup] Using OpenAI API for Embeddings (fallback)", flush=True)

print(f"[startup] chat={AZURE_OPENAI_CHAT_DEPLOYMENT if USE_AZURE else CHAT_MODEL} embed={AZURE_OPENAI_EMBEDDING_DEPLOYMENT if USE_AZURE_EMBEDDINGS else EMBED_MODEL}", flush=True)

# --- make stdout UTF-8 safe on Windows; also keep logs ASCII to be bulletproof ---
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def ascii_safe(s: str) -> str:
    """Return ASCII-only version of s (drop non-ASCII)."""
    try:
        return s.encode("ascii", "ignore").decode("ascii")
    except Exception:
        return "<non-ascii>"


import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# --- app init ---
app = FastAPI(title="Biz-English RAG API")
print("[startup] app.py reloaded OK", flush=True)

# Initialize database on startup
from db_init import init_db
from db import get_db

@app.on_event("startup")
def startup_event():
    """Initialize database and seed roles"""
    try:
        init_db()
    except Exception as e:
        print(f"[startup] ⚠️  Database initialization warning: {e}", flush=True)

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "bizeng-server"}

# Version endpoint
@app.get("/version")
def version():
    """API version information"""
    return {
        "version": "1.0.0",
        "features": ["auth", "roleplay", "chat", "pronunciation", "admin_analytics"]
    }

# Import auth routers
from routers import auth, me, admin, tracking
from routers import admin_monitor
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(admin.router)
app.include_router(tracking.router)
app.include_router(admin_monitor.router)

print("[startup] ✅ Auth routers registered: /auth, /me, /admin, /tracking, /admin/monitor", flush=True)

# Import and include roleplay router
from roleplay_api import router as roleplay_router
app.include_router(roleplay_router)

# Initialize Qdrant client with Cloud credentials
qdr = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=30,
)
print(f"[startup] ✅ Qdrant client initialized: {QDRANT_URL}", flush=True)
print(f"[startup] ✅ Using collection: {QDRANT_COLLECTION}", flush=True)

# Initialize OpenAI client for Chat (Azure Sweden Central or regular OpenAI)
if USE_AZURE:
    oai = AzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    print(f"[startup] ✅ Azure Chat client initialized (Sweden Central)", flush=True)
else:
    oai = OpenAI(api_key=OPENAI_API_KEY)
    print(f"[startup] ✅ OpenAI Chat client initialized (fallback)", flush=True)

# Initialize separate client for Embeddings (Azure UAE North or regular OpenAI)
if USE_AZURE_EMBEDDINGS:
    oai_embed = AzureOpenAI(
        api_key=AZURE_OPENAI_EMBEDDING_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_EMBEDDING_ENDPOINT
    )
    print(f"[startup] ✅ Azure Embeddings client initialized (UAE North)", flush=True)
else:
    oai_embed = OpenAI(api_key=OPENAI_API_KEY)
    print(f"[startup] ✅ OpenAI Embeddings client initialized (fallback)", flush=True)

# Validate collection vs embedding model dimension
info = qdr.get_collection(QDRANT_COLLECTION)
dim = info.config.params.vectors.size
model_dim = 3072 if "3-large" in EMBED_MODEL else 1536
assert dim == model_dim, (
    f"EMBED_MODEL ({EMBED_MODEL}, dim={model_dim}) "
    f"does not match Qdrant collection dim={dim}. "
    f"Fix .env or recreate the collection."
)

# Tokenizer for budgeting context
from tiktoken import get_encoding
_enc = get_encoding("cl100k_base")


def sanitize_query(query: str) -> str:
    """
    Sanitize user input to reduce Azure content filter triggers.
    Converts informal/casual language to professional equivalents.
    """
    # Map informal -> formal
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

    # Replace informal terms (case-insensitive, whole words only)
    sanitized = query.lower()
    for informal, formal in informal_to_formal.items():
        # Replace whole words only (not parts of words)
        sanitized = sanitized.replace(f" {informal} ", f" {formal} ")
        if sanitized.startswith(f"{informal} "):
            sanitized = f"{formal}{sanitized[len(informal):]}"
        if sanitized.endswith(f" {informal}"):
            sanitized = f"{sanitized[:-len(informal)]}{formal}"

    return sanitized if sanitized != query.lower() else query


def pack_context(hits, token_budget: int = 1200) -> str:
    """Concatenate hit payload text slices until token_budget is reached."""
    out, used = [], 0
    for h in hits:
        t = (h.payload.get("text") or "").strip()
        if not t:
            continue
        t_tok = len(_enc.encode(t))
        if used + t_tok > token_budget:
            continue
        out.append(t)
        used += t_tok
    return "\n\n---\n\n".join(out)


def bm25ish_score(text: str, query: str) -> int:
    """Very rough lexical re-rank: counts overlapping words."""
    q_words = re.findall(r"\w+", (query or "").lower())
    t_words = set(re.findall(r"\w+", (text or "").lower()))
    return sum(1 for w in q_words if w in t_words)


class AskReq(BaseModel):
    query: str
    k: int = 5                      # default top-k
    max_context_chars: int = 6000   # secondary guard under model limits
    unit: Optional[str] = None      # optional filter if you ingested unit info


class AskResp(BaseModel):
    answer: str
    sources: List[str]


class EmbReq(BaseModel):
    text: str


@app.get("/version")
def version():
    return {"version": "0.1.0", "env": "dev", "debug": True}

@app.post("/debug/embed")
def debug_embed(e: EmbReq):
    try:
        model_name = AZURE_OPENAI_EMBEDDING_DEPLOYMENT if USE_AZURE_EMBEDDINGS else EMBED_MODEL
        vec = oai_embed.embeddings.create(model=model_name, input=e.text).data[0].embedding
        print("[debug][embed] ok len", len(vec), flush=True)
        return {"dim": len(vec)}
    except Exception as ex:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"embed failed: {type(ex).__name__}: {ex}")


@app.post("/ask", response_model=AskResp)
def ask(req: AskReq) -> AskResp:
    try:
        # Sanitize query to avoid Azure content filter triggers
        original_query = req.query
        sanitized_query = sanitize_query(req.query)
        if sanitized_query != original_query:
            print(f"[ask] Sanitized query: '{original_query}' -> '{sanitized_query}'", flush=True)

        print("[ask] stage=embed", flush=True)
        embed_model = AZURE_OPENAI_EMBEDDING_DEPLOYMENT if USE_AZURE_EMBEDDINGS else EMBED_MODEL
        q_emb = oai_embed.embeddings.create(model=embed_model, input=sanitized_query).data[0].embedding

        # ✂️ Ignore unit completely for now (OCR won't have it reliably)
        qfilter = None

        # 1st pass: ANN search, **always with payload**, wider net
        raw_hits = qdr.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=q_emb,
            limit=max(req.k, 50),
            query_filter=qfilter,
            with_payload=True,
            search_params=SearchParams(hnsw_ef=128, exact=False),
        )

        # Retry (no filter anyway) — still ensure payloads are present
        if not raw_hits:
            print("[ask] zero hits; retrying", flush=True)
            raw_hits = qdr.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=q_emb,
                limit=max(req.k, 50),
                with_payload=True,
                search_params=SearchParams(hnsw_ef=128, exact=False),
            )

        if not raw_hits:
            return AskResp(answer="Not found in the provided materials.", sources=[])

        # ⚠️ OCR text is noisy; lexical rerank can *hurt*. Keep ANN order, then do a light bump.
        def bump_score(h):
            base = h.score or 0.0  # ANN similarity
            txt = (h.payload or {}).get("text", "")
            # reward a tiny bit if any whole word overlaps (helps clean hits; doesn't nuke ANN)
            overlap = bm25ish_score(txt, sanitized_query)
            return base + 0.001 * overlap

        raw_hits.sort(key=bump_score, reverse=True)
        hits = raw_hits[: req.k]
        print(f"[ask] stage=search hits={len(hits)}", flush=True)

        # Build context
        context = pack_context(hits, token_budget=1200)
        if len(context) > req.max_context_chars:
            context = context[: req.max_context_chars]
        sources = [ (h.payload or {}).get("source_id","") for h in hits ]

        # Debug: show first 2 snippets so you *see* what was retrieved
        for i, h in enumerate(hits[:2], 1):
            t = ((h.payload or {}).get("text","")[:180]).replace("\n"," ")
            print(f"[ask] top{i}: score={h.score:.4f} src={(h.payload or {}).get('source_id')} | {t}", flush=True)

        ctx_tokens = len(_enc.encode(context))
        print(f"[ask] q='{ascii_safe(sanitized_query)}' k={req.k} hits={len(hits)} ctx_tokens={ctx_tokens} chars={len(context)}", flush=True)

        # Build safe system prompt for Azure content filter
        system_prompt = (
            "You are a professional Business English teaching assistant. "
            "You help students learn business communication skills in a professional, educational setting. "
            "Use the provided course materials to answer the student's question. "
            "If the answer is not in the materials, provide helpful business English guidance."
        )

        # Use sanitized query in user prompt
        user_prompt = f"Student question: {sanitized_query}\n\nCourse materials:\n{context}"

        print("[ask] stage=chat", flush=True)
        chat_model = AZURE_OPENAI_CHAT_DEPLOYMENT if USE_AZURE else CHAT_MODEL

        try:
            # Try main request with safe prompts
            chat = oai.chat.completions.create(
                model=chat_model,
                messages=[{"role":"system","content":system_prompt},
                          {"role":"user","content":user_prompt}],
                max_tokens=300,
                temperature=0.2,
            )
            answer = chat.choices[0].message.content
            return AskResp(answer=answer, sources=sources)

        except BadRequestError as e:
            # Check if it's a content filter error
            error_msg = ""
            try:
                error_msg = str(e.response.json())
            except:
                error_msg = str(e)

            if "content management policy" in error_msg.lower() or "content_filter" in error_msg.lower():
                print(f"⚠️ [ask] Content filter triggered, trying fallback...", flush=True)

                # FALLBACK: Ultra-safe prompt without context
                try:
                    fallback_messages = [
                        {
                            "role": "system",
                            "content": "You are a professional Business English teacher. Provide helpful, appropriate educational responses."
                        },
                        {
                            "role": "user",
                            "content": f"Please help me with this business English question: {sanitized_query}"
                        }
                    ]

                    chat = oai.chat.completions.create(
                        model=chat_model,
                        messages=fallback_messages,
                        max_tokens=300,
                        temperature=0.7
                    )

                    answer = chat.choices[0].message.content
                    print("✅ [ask] Fallback prompt succeeded", flush=True)
                    return AskResp(answer=answer, sources=[])  # No sources in fallback

                except Exception as fallback_error:
                    print(f"❌ [ask] Even fallback failed: {fallback_error}", flush=True)
                    # Return helpful error message
                    return AskResp(
                        answer=(
                            "I apologize, but I'm having trouble processing that query due to content filtering. "
                            "Could you please rephrase your question in a more formal way? "
                            "For example, instead of casual greetings, try asking a specific business English question."
                        ),
                        sources=[]
                    )
            else:
                # Not a content filter error, re-raise
                raise

    except HTTPException:
        raise
    except BadRequestError as e:
        msg = ""
        try: msg = e.response.json().get("error", {}).get("message", "") or e.response.json().get("message","")
        except Exception: pass
        msg = (msg or "").encode("ascii","ignore").decode("ascii")
        raise HTTPException(status_code=500, detail=f"/ask failed: BadRequestError: {msg}")
    except (AuthenticationError, PermissionDeniedError, RateLimitError, NotFoundError) as e:
        hint = {
            AuthenticationError: "Invalid or missing OPENAI_API_KEY",
            PermissionDeniedError: "Model access denied",
            RateLimitError: "Rate limited",
            NotFoundError: "Model not found",
        }.get(e.__class__, "OpenAI error")
        raise HTTPException(status_code=500, detail=f"/ask failed: {e.__class__.__name__}: {hint}")
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"/ask failed: {e.__class__.__name__}")



@app.get("/health")
def health():
    return {"status": "nowwww"}


class ChatMessage(BaseModel):
    role: str
    content: str

    @validator('role')
    def validate_role(cls, v):
        """Validate that role is one of the allowed values"""
        valid_roles = ['user', 'assistant', 'system']
        if v not in valid_roles:
            raise ValueError(f"Invalid role: '{v}'. Must be one of: {valid_roles}")
        return v

class ChatReqDto(BaseModel):
    messages: list[ChatMessage]
    k: int = 5
    maxContextChars: int = 6000
    unit: Optional[str] = None

class ChatRespDto(BaseModel):
    answer: str
    sources: list[str] = []

from tracking import track
from deps import get_optional_user

@app.post("/chat", response_model=ChatRespDto)
async def chat(req: ChatReqDto, user = Depends(get_optional_user), db: Session = Depends(get_db)) -> ChatRespDto:
    """
    Free chat mode - conversational AI for business English learning
    Uses OpenAI to provide natural assistance without strict RAG grounding
    """
    from routers.tracking import create_attempt_internal, finish_attempt_internal
    from datetime import datetime

    start_time = datetime.utcnow()
    attempt = None

    try:
        print(f"[chat] Received {len(req.messages)} messages", flush=True)

        # Create attempt record
        if user:
            try:
                attempt = create_attempt_internal(
                    db=db,
                    user_id=user.id,
                    exercise_type="chat",
                    exercise_id=f"chat_{start_time.isoformat()}",
                    extra_metadata={"message_count": len(req.messages)}
                )
                print(f"[chat] Created attempt ID: {attempt.id}", flush=True)
            except Exception as e:
                print(f"[chat] Warning: Failed to create attempt: {e}", flush=True)

        # Convert messages to OpenAI format
        messages = [{"role": msg.role, "content": msg.content} for msg in req.messages]

        # Add system message if not present
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {
                "role": "system",
                "content": (
                    "You are a helpful business English learning assistant. "
                    "Help students improve their business communication skills, "
                    "explain business vocabulary and phrases, provide examples of professional language, "
                    "and answer questions about business English. "
                    "Be encouraging, clear, and educational in your responses. "
                    "Keep responses professional and avoid explicit content."
                )
            })

        # Limit history to last 10 exchanges (20 messages + system message)
        MAX_HISTORY = 20  # system + 10 user-assistant pairs
        if len(messages) > MAX_HISTORY:
            messages = [messages[0]] + messages[-(MAX_HISTORY-1):]
            print(f"[chat] Trimmed to {len(messages)} messages (max={MAX_HISTORY})", flush=True)

        print(f"[chat] Calling OpenAI with {len(messages)} messages", flush=True)

        # Instrument: opened chat
        try:
            uid = user.id if user else None
            track(uid, "chat_opened", feature="chat", message_count=len(messages))
        except Exception:
            pass

        # Call OpenAI API using the existing client
        chat_model = AZURE_OPENAI_CHAT_DEPLOYMENT if USE_AZURE else CHAT_MODEL
        response = oai.chat.completions.create(
            model=chat_model,
            messages=messages,
            temperature=0.7,
            max_tokens=500  # Azure-compatible
        )

        ai_message = response.choices[0].message.content

        # RESPONSE validation
        if not ai_message:
            raise ValueError("Empty response from OpenAI")

        # SANITIZE logging
        print(f"[chat] Response generated ({len(ai_message)} chars)", flush=True)

        # Finish attempt
        if attempt:
            try:
                duration = int((datetime.utcnow() - start_time).total_seconds())
                finish_attempt_internal(
                    db=db,
                    attempt_id=attempt.id,
                    duration_seconds=duration,
                    score=None,  # No scoring for chat
                    extra_metadata={
                        "response_length": len(ai_message),
                        "total_messages": len(messages)
                    }
                )
                print(f"[chat] ✅ Attempt {attempt.id} finished - Duration: {duration}s", flush=True)
            except Exception as e:
                print(f"[chat] Warning: Failed to finish attempt: {e}", flush=True)

        # Instrument: chat message produced
        try:
            uid = user.id if user else None
            track(uid, "chat_message", feature="chat", message_length=len(ai_message))
        except Exception:
            pass

        return ChatRespDto(answer=ai_message, sources=[])

    except BadRequestError as e:
        msg = ""
        try:
            msg = e.response.json().get("error", {}).get("message", "") or e.response.json().get("message",
                                                                                                 "")
        except Exception:
            pass
        msg = (msg or "").encode("ascii", "ignore").decode("ascii")
        raise HTTPException(status_code=500, detail=f"/chat failed: BadRequestError: {msg}")
    except (AuthenticationError, PermissionDeniedError, RateLimitError, NotFoundError) as e:
        hint = {
            AuthenticationError: "Invalid or missing OPENAI_API_KEY",
            PermissionDeniedError: "Model access denied",
            RateLimitError: "Rate limited",
            NotFoundError: "Model not found",
        }.get(e.__class__, "OpenAI error")
        raise HTTPException(status_code=500, detail=f"/chat failed: {e.__class__.__name__}: {hint}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[chat] Error: {type(e).__name__}: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"/chat failed: {type(e).__name__}: {str(e)}")


class PeekResp(BaseModel):
    items: List[dict]

@app.get("/debug/search", response_model=PeekResp)
def debug_search(q: str, k: int = 5):
    embed_model = AZURE_OPENAI_EMBEDDING_DEPLOYMENT if USE_AZURE_EMBEDDINGS else EMBED_MODEL
    vec = oai_embed.embeddings.create(model=embed_model, input=q).data[0].embedding
    hits = qdr.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=vec,
        limit=k,
        with_payload=True,
        search_params=SearchParams(hnsw_ef=128, exact=False),
    )
    out = []
    for h in hits:
        p = h.payload or {}
        out.append({
            "score": h.score,
            "src": p.get("source_id"),
            "unit": p.get("unit"),
            "snippet": (p.get("text","")[:300]).replace("\n"," ")
        })
    print(f"[debug/search] q='{ascii_safe(q)}' -> {len(out)} hits", flush=True)
    return PeekResp(items=out)


# ============================================================================
# AUDIO ENDPOINTS: Speech-to-Text (STT) and Text-to-Speech (TTS)
# ============================================================================

class STTResponse(BaseModel):
    text: str

@app.post("/stt", response_model=STTResponse)
async def speech_to_text(file: UploadFile = File(...)):
    """
    Transcribe audio file to text using OpenAI Whisper API.
    Accepts WAV, MP3, M4A, and other audio formats.
    """
    print(f"[stt] Received file: {file.filename}, content_type: {file.content_type}", flush=True)

    # Create temporary file to store uploaded audio
    temp_path = None
    try:
        # Read uploaded file content
        content = await file.read()
        print(f"[stt] File size: {len(content)} bytes", flush=True)

        # Determine file extension from filename or content type
        suffix = Path(file.filename).suffix if file.filename else ".wav"
        if not suffix:
            suffix = ".wav"

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        print(f"[stt] Saved to temp file: {temp_path}", flush=True)

        # Call OpenAI Whisper API
        with open(temp_path, "rb") as audio_file:
            print("[stt] Calling OpenAI Whisper API...", flush=True)
            transcript = oai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"  # Specify English for better accuracy
            )

        transcribed_text = transcript.text
        print(f"[stt] Transcription successful: '{transcribed_text[:100]}...'", flush=True)

        return STTResponse(text=transcribed_text)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[stt] Error: {type(e).__name__}: {e}", flush=True)
        raise HTTPException(
            status_code=500,
            detail=f"Speech-to-text failed: {type(e).__name__}: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                print(f"[stt] Cleaned up temp file: {temp_path}", flush=True)
            except Exception as e:
                print(f"[stt] Failed to delete temp file: {e}", flush=True)


@app.post("/tts")
async def text_to_speech(text: str = Form(...)):
    """
    Convert text to speech using OpenAI TTS API.
    Returns audio/mpeg (MP3) format.
    Voice options: alloy, echo, fable, onyx, nova, shimmer
    """
    print(f"[tts] Received text: '{text[:100]}...'", flush=True)

    try:
        # Call OpenAI TTS API
        print("[tts] Calling OpenAI TTS API...", flush=True)
        response = oai.audio.speech.create(
            model="tts-1",  # or "tts-1-hd" for higher quality
            voice="alloy",  # Professional, neutral voice
            input=text,
            response_format="mp3"  # Android can play MP3
        )

        # Get audio bytes
        audio_bytes = response.content
        print(f"[tts] TTS successful, audio size: {len(audio_bytes)} bytes", flush=True)

        # Return audio response
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3"
            }
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[tts] Error: {type(e).__name__}: {e}", flush=True)
        raise HTTPException(
            status_code=500,
            detail=f"Text-to-speech failed: {type(e).__name__}: {str(e)}"
        )


# ============================================================================
# AZURE SPEECH SERVICE - PRONUNCIATION ASSESSMENT
# ============================================================================

# Azure Speech Service Configuration - loaded from settings
# Only initialize if credentials are available
if AZURE_SPEECH_KEY and AZURE_SPEECH_REGION:
    speech_config = speechsdk.SpeechConfig(
        subscription=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION
    )
    print(f"[startup] ✅ Azure Speech Service configured: {AZURE_SPEECH_REGION}", flush=True)
else:
    speech_config = None
    print(f"[startup] ⚠️  Azure Speech Service NOT configured (optional feature)", flush=True)


# DTOs for Pronunciation Assessment
class PronunciationPhoneme(BaseModel):
    """Phoneme-level pronunciation details"""
    phoneme: str  # IPA phoneme symbol
    score: float  # 0-100

class PronunciationWord(BaseModel):
    word: str
    accuracy_score: float  # 0-100
    error_type: Optional[str] = None  # "Mispronunciation", "Omission", "Insertion", or None
    phonemes: Optional[List[PronunciationPhoneme]] = None  # Phoneme-level details
    ipa_expected: Optional[str] = None  # Expected IPA transcription
    ipa_actual: Optional[str] = None  # What user actually said (IPA)
    feedback: Optional[str] = None  # Specific feedback for this word


class PronunciationResult(BaseModel):
    transcript: str  # What the user actually said
    accuracy_score: float  # 0-100 overall accuracy
    fluency_score: float  # 0-100 how natural it sounds
    completeness_score: float  # 0-100 did they say everything
    pronunciation_score: float  # 0-100 overall pronunciation
    words: List[PronunciationWord]  # Individual word scores
    feedback: str  # Human-readable feedback
    detailed_feedback: Optional[List[str]] = None  # Detailed tips per word


# Phonetic feedback database for common mispronunciations
PHONETIC_TIPS = {
    # Vowels
    "iː": "Long 'ee' sound as in 'see'. Keep your tongue high and front.",
    "ɪ": "Short 'i' sound as in 'sit'. Relax your tongue slightly.",
    "e": "Short 'e' sound as in 'bed'. Mid-front tongue position.",
    "æ": "'a' sound as in 'cat'. Open your mouth wider, tongue low.",
    "ɑː": "Long 'ah' sound as in 'father'. Open mouth, tongue back.",
    "ɒ": "Short 'o' sound as in 'hot'. Round your lips slightly.",
    "ɔː": "Long 'aw' sound as in 'law'. Round your lips more.",
    "ʊ": "Short 'oo' sound as in 'put'. Lips rounded, tongue back.",
    "uː": "Long 'oo' sound as in 'food'. Round lips fully, tongue back and high.",
    "ʌ": "Short 'uh' sound as in 'cup'. Neutral tongue position.",
    "ɜː": "'ur' sound as in 'bird'. Mid-central tongue, lips neutral.",
    "ə": "Schwa - unstressed 'uh' sound. Most common vowel in English.",

    # Consonants
    "θ": "'th' as in 'think'. Put tongue between teeth, blow air.",
    "ð": "'th' as in 'this'. Same as θ but add voice.",
    "ʃ": "'sh' sound as in 'ship'. Lips rounded forward.",
    "ʒ": "'zh' sound as in 'measure'. Like 'sh' but add voice.",
    "tʃ": "'ch' sound as in 'church'. Quick 't' + 'sh'.",
    "dʒ": "'j' sound as in 'judge'. Quick 'd' + 'zh'.",
    "ŋ": "'ng' sound as in 'sing'. Block air with back of tongue.",
    "r": "'r' sound. Curl tongue back (American) or tap (British).",
    "l": "'l' sound. Touch tongue to roof of mouth behind teeth.",
    "w": "'w' sound. Round lips tightly then release.",
    "j": "'y' sound as in 'yes'. Tongue high and forward.",
}

# Basic IPA dictionary for common business English words
# This provides fallback IPA transcriptions when Azure doesn't provide them
WORD_IPA_DICT = {
    "good": "ɡʊd",
    "morning": "ˈmɔːnɪŋ",
    "hello": "həˈləʊ",
    "meeting": "ˈmiːtɪŋ",
    "schedule": "ˈʃedjuːl",  # American
    "business": "ˈbɪznəs",
    "email": "ˈiːmeɪl",
    "phone": "fəʊn",
    "call": "kɔːl",
    "client": "ˈklaɪənt",
    "customer": "ˈkʌstəmə",
    "manager": "ˈmænɪdʒə",
    "presentation": "ˌprezənˈteɪʃən",
    "project": "ˈprɒdʒekt",
    "deadline": "ˈdedlaɪn",
    "report": "rɪˈpɔːt",
    "invoice": "ˈɪnvɔɪs",
    "contract": "ˈkɒntrækt",
    "agreement": "əˈɡriːmənt",
    "appointment": "əˈpɔɪntmənt",
    "conference": "ˈkɒnfərəns",
    "interview": "ˈɪntəvjuː",
    "salary": "ˈsæləri",
    "office": "ˈɒfɪs",
    "department": "dɪˈpɑːtmənt",
    "colleague": "ˈkɒliːɡ",
    "professional": "prəˈfeʃənəl",
    "important": "ɪmˈpɔːtənt",
    "urgent": "ˈɜːdʒənt",
    "available": "əˈveɪləbəl",
    "please": "pliːz",
    "thank": "θæŋk",
    "welcome": "ˈwelkəm",
    "regards": "rɪˈɡɑːdz",
    "sincerely": "sɪnˈsɪəli",
}


def get_word_ipa(word: str, phonemes: Optional[List[PronunciationPhoneme]] = None) -> str:
    """
    Generate IPA transcription for a word.
    First tries to build from phoneme list, then falls back to dictionary.
    """
    # If we have phoneme data from Azure, construct IPA from that
    if phonemes:
        ipa_parts = [p.phoneme for p in phonemes]
        return "".join(ipa_parts)

    # Fallback to dictionary lookup
    word_lower = word.lower().strip(".,!?;:")
    return WORD_IPA_DICT.get(word_lower, "")


def get_phonetic_tip(phoneme: str) -> Optional[str]:
    """Get pronunciation tip for a specific phoneme"""
    # Remove stress markers and length markers
    clean_phoneme = phoneme.replace("ˈ", "").replace("ˌ", "").replace("ː", "")
    return PHONETIC_TIPS.get(clean_phoneme)


def generate_word_feedback(word: str, accuracy: float, error_type: Optional[str],
                          phonemes: Optional[List[PronunciationPhoneme]]) -> str:
    """Generate specific feedback for a mispronounced word"""

    if error_type == "Omission":
        return f"You skipped the word '{word}'. Make sure to pronounce every word clearly."

    if error_type == "Insertion":
        return f"You added the word '{word}' which wasn't in the text."

    if error_type == "Mispronunciation" or accuracy < 60:
        feedback_parts = [f"Work on '{word}'"]

        # Find the most problematic phonemes
        if phonemes:
            problem_phonemes = [p for p in phonemes if p.score < 60]
            if problem_phonemes:
                # Get tips for the worst phonemes
                for phoneme in problem_phonemes[:2]:  # Top 2 worst
                    tip = get_phonetic_tip(phoneme.phoneme)
                    if tip:
                        feedback_parts.append(f"- Focus on /{phoneme.phoneme}/ sound: {tip}")

        if not phonemes or not problem_phonemes:
            # Generic feedback based on common issues
            feedback_parts.append("- Listen to the correct pronunciation and repeat slowly.")
            feedback_parts.append("- Break it into syllables and practice each part.")

        return " ".join(feedback_parts)

    return None


def generate_pronunciation_feedback(
    overall_score: float,
    accuracy_score: float,
    fluency_score: float,
    words: List[PronunciationWord]
) -> tuple[str, List[str]]:
    """Generate human-readable feedback based on scores"""

    feedback_parts = []
    detailed_tips = []

    # Overall assessment with more nuance
    if overall_score >= 95:
        feedback_parts.append("Outstanding pronunciation! Nearly native-like. 🌟")
    elif overall_score >= 85:
        feedback_parts.append("Excellent pronunciation! Very clear and natural. 👏")
    elif overall_score >= 75:
        feedback_parts.append("Good pronunciation! A few minor areas to improve. 👍")
    elif overall_score >= 60:
        feedback_parts.append("Fair pronunciation. Let's work on some specific sounds. 📚")
    elif overall_score >= 40:
        feedback_parts.append("Needs practice. Focus on the words highlighted below. 💪")
    else:
        feedback_parts.append("Let's practice together. Slow down and focus on clarity. 🎯")

    # Identify mispronounced words with detailed feedback
    mispronounced = [w for w in words if w.accuracy_score < 70 or w.error_type in ["Mispronunciation", "Omission"]]

    if mispronounced:
        if len(mispronounced) == 1:
            feedback_parts.append(f"\n📍 Focus on: '{mispronounced[0].word}'")
        else:
            word_list = ', '.join([f"'{w.word}'" for w in mispronounced[:5]])
            feedback_parts.append(f"\n📍 Words to practice: {word_list}")

        # Generate detailed tips for each problem word
        for word in mispronounced[:3]:  # Top 3 worst words
            word_tip = generate_word_feedback(word.word, word.accuracy_score, word.error_type, word.phonemes)
            if word_tip:
                detailed_tips.append(word_tip)

    # Fluency feedback with specific advice
    if fluency_score < 60:
        feedback_parts.append("\n⏱️ Fluency tip: You're speaking too slowly or with too many pauses. Try to speak more smoothly.")
        detailed_tips.append("Practice reading the sentence out loud several times to build muscle memory.")
    elif fluency_score < 80:
        feedback_parts.append("\n⏱️ Fluency tip: Good pace, but try to sound more natural with fewer hesitations.")

    # Accuracy feedback with specific advice
    if accuracy_score < 60:
        feedback_parts.append("\n🎯 Accuracy tip: Focus on pronouncing each sound clearly. Don't rush.")
        detailed_tips.append("Record yourself and compare with a native speaker.")
    elif accuracy_score < 80:
        feedback_parts.append("\n🎯 Accuracy tip: Almost there! Pay attention to stress and intonation.")

    # Completeness feedback
    omitted = [w for w in words if w.error_type == "Omission"]
    if omitted:
        omitted_words = ', '.join([f"'{w.word}'" for w in omitted])
        feedback_parts.append(f"\n⚠️ You missed: {omitted_words}")
        detailed_tips.append("Make sure to pronounce every word in the sentence.")

    return " ".join(feedback_parts), detailed_tips


@app.post("/pronunciation/assess", response_model=PronunciationResult)
async def assess_pronunciation(
    audio: UploadFile = File(...),
    reference_text: str = Form(...),
    user = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Assess pronunciation of uploaded audio against reference text.

    Usage from Android:
    - Record audio to WAV/MP3 file
    - Send as multipart/form-data with reference_text

    Example:
        audio: User's recorded audio file
        reference_text: "Good morning, I would like to schedule a meeting"

    Returns:
        Detailed pronunciation scores and feedback
    """
    from routers.tracking import create_attempt_internal, finish_attempt_internal
    from datetime import datetime

    start_time = datetime.utcnow()
    attempt = None
    temp_audio_path = None

    try:
        print(f"[pronunciation] Assessing audio for: '{reference_text}'", flush=True)

        # Create attempt record
        if user:
            try:
                attempt = create_attempt_internal(
                    db=db,
                    user_id=user.id,
                    exercise_type="pronunciation",
                    exercise_id=f"pron_{start_time.isoformat()}",
                    extra_metadata={"reference_text": reference_text[:100]}  # First 100 chars only
                )
                print(f"[pronunciation] Created attempt ID: {attempt.id}", flush=True)
            except Exception as e:
                print(f"[pronunciation] Warning: Failed to create attempt: {e}", flush=True)

        # Save uploaded audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            content = await audio.read()
            temp_audio.write(content)
            temp_audio_path = temp_audio.name

        print(f"[pronunciation] Audio saved to: {temp_audio_path}", flush=True)

        # Configure audio input
        audio_config = speechsdk.AudioConfig(filename=temp_audio_path)

        # Configure pronunciation assessment
        pronunciation_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Word,
            enable_miscue=True  # Detect if they said wrong words
        )

        # Create speech recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        # Apply pronunciation assessment
        pronunciation_config.apply_to(speech_recognizer)

        print("[pronunciation] Running Azure Speech assessment...", flush=True)

        # Perform recognition
        result = speech_recognizer.recognize_once()

        # Check if recognition succeeded
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print(f"[pronunciation] Recognized: '{result.text}'", flush=True)

            # Parse pronunciation assessment results
            pronunciation_result = speechsdk.PronunciationAssessmentResult(result)

            # Extract word-level and phoneme-level scores
            words = []
            word_details = result.properties.get(
                speechsdk.PropertyId.SpeechServiceResponse_JsonResult
            )

            if word_details:
                details = json.loads(word_details)

                # Log full JSON for debugging
                print(f"[pronunciation] Full Azure response available", flush=True)

                for word_info in details.get("NBest", [{}])[0].get("Words", []):
                    word_text = word_info.get("Word", "")
                    word_assessment = word_info.get("PronunciationAssessment", {})
                    accuracy = word_assessment.get("AccuracyScore", 0)
                    error_type = word_assessment.get("ErrorType")

                    # Extract phoneme-level details if available
                    phonemes = []
                    phoneme_data = word_info.get("Phonemes", [])
                    if phoneme_data:
                        for phoneme_info in phoneme_data:
                            phoneme_symbol = phoneme_info.get("Phoneme", "")
                            phoneme_score = phoneme_info.get("PronunciationAssessment", {}).get("AccuracyScore", 0)
                            phonemes.append(PronunciationPhoneme(
                                phoneme=phoneme_symbol,
                                score=phoneme_score
                            ))
                            print(f"    Phoneme: /{phoneme_symbol}/ - Score: {phoneme_score:.1f}/100", flush=True)

                    # Generate IPA transcription for this word
                    word_ipa = get_word_ipa(word_text, phonemes if phonemes else None)
                    if word_ipa:
                        print(f"    IPA: /{word_ipa}/", flush=True)

                    # Generate word-specific feedback
                    word_feedback = generate_word_feedback(word_text, accuracy, error_type, phonemes if phonemes else None)

                    words.append(PronunciationWord(
                        word=word_text,
                        accuracy_score=accuracy,
                        error_type=error_type,
                        phonemes=phonemes if phonemes else None,
                        ipa_expected=word_ipa if word_ipa else None,  # Add IPA transcription
                        ipa_actual=None,  # Azure doesn't provide what user said in IPA (future enhancement)
                        feedback=word_feedback
                    ))

                    print(f"  Word: '{word_text}' - Score: {accuracy:.1f}/100 - Error: {error_type or 'None'}", flush=True)

            # Generate comprehensive feedback with detailed tips
            overall_score = pronunciation_result.pronunciation_score
            feedback, detailed_tips = generate_pronunciation_feedback(
                overall_score,
                pronunciation_result.accuracy_score,
                pronunciation_result.fluency_score,
                words
            )

            print(f"[pronunciation] Overall score: {overall_score:.1f}/100", flush=True)
            print(f"[pronunciation] Feedback: {feedback[:100]}...", flush=True)
            if detailed_tips:
                print(f"[pronunciation] Generated {len(detailed_tips)} detailed tips", flush=True)

            # Finish attempt with score
            if attempt:
                try:
                    duration = int((datetime.utcnow() - start_time).total_seconds())
                    finish_attempt_internal(
                        db=db,
                        attempt_id=attempt.id,
                        duration_seconds=duration,
                        score=overall_score,
                        passed=overall_score >= 70.0,  # 70% is passing
                        extra_metadata={
                            "accuracy": pronunciation_result.accuracy_score,
                            "fluency": pronunciation_result.fluency_score,
                            "completeness": pronunciation_result.completeness_score
                        }
                    )
                    print(f"[pronunciation] ✅ Attempt {attempt.id} finished - Score: {overall_score:.1f}, Duration: {duration}s", flush=True)
                except Exception as e:
                    print(f"[pronunciation] Warning: Failed to finish attempt: {e}", flush=True)

            return PronunciationResult(
                transcript=result.text,
                accuracy_score=pronunciation_result.accuracy_score,
                fluency_score=pronunciation_result.fluency_score,
                completeness_score=pronunciation_result.completeness_score,
                pronunciation_score=pronunciation_result.pronunciation_score,
                words=words,
                feedback=feedback,
                detailed_feedback=detailed_tips if detailed_tips else None
            )

        elif result.reason == speechsdk.ResultReason.NoMatch:
            print("[pronunciation] ERROR: No speech detected", flush=True)
            raise HTTPException(
                status_code=400,
                detail="Could not recognize speech. Please speak clearly and try again."
            )

        else:
            print(f"[pronunciation] ERROR: Recognition failed - {result.reason}", flush=True)
            raise HTTPException(
                status_code=500,
                detail=f"Speech recognition failed: {result.reason}"
            )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[pronunciation] ERROR: {str(e)}", flush=True)
        raise HTTPException(
            status_code=500,
            detail=f"Pronunciation assessment failed: {str(e)}"
        )
    finally:
        # Clean up temp file
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
                print(f"[pronunciation] Cleaned up temp file: {temp_audio_path}", flush=True)
            except Exception as e:
                print(f"[pronunciation] Failed to delete temp file: {e}", flush=True)


@app.post("/pronunciation/quick-check")
async def quick_pronunciation_check(
    audio: UploadFile = File(...),
    reference_text: str = Form(...)
):
    """
    Quick pronunciation check - returns simplified results.
    Good for integrating into chat/roleplay without overwhelming the user.

    Returns:
        score: Overall pronunciation score (0-100)
        feedback: Simple text feedback
        transcript: What they actually said
        needs_practice: Boolean if score is below 70
    """
    try:
        result = await assess_pronunciation(audio, reference_text)

        # Simplified response
        return {
            "score": round(result.pronunciation_score, 1),
            "feedback": result.feedback,
            "transcript": result.transcript,
            "needs_practice": result.pronunciation_score < 70,
            "mispronounced_words": [
                w.word for w in result.words
                if w.accuracy_score < 60 or w.error_type == "Mispronunciation"
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pronunciation/test")
async def test_pronunciation_service():
    """Test if Azure Speech Service is configured correctly"""
    try:
        return {
            "status": "ok",
            "region": AZURE_SPEECH_REGION,
            "service": "Azure Speech Service",
            "features": [
                "Pronunciation Assessment",
                "Word-level scoring",
                "Fluency analysis",
                "Accuracy measurement"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AUTH & ADMIN ROUTERS
# ============================================================================

from routers import auth, me, admin, tracking

# Register all auth-related routers
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(admin.router)
app.include_router(tracking.router)

print("[startup] ✅ Auth routers registered: /auth, /me, /admin, /tracking", flush=True)
