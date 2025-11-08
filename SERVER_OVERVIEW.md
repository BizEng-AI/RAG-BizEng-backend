# Server Architecture Overview

Updated: 2025-10-29
Scope: High-level map of the Biz-English RAG server so Android/ChatGPT can align without touching code or secrets.

---

## 1) Technology Stack
- Framework: FastAPI (Python)
- Runtime: Uvicorn
- Vector DB: Qdrant
- LLM Provider(s):
  - Azure OpenAI (primary) for Chat and Embeddings
  - OpenAI (fallback) for STT (Whisper) and TTS (tts-1)
- Speech: Azure Speech Service (Pronunciation Assessment)

---

## 2) Key Files
- `app.py`
  - API entrypoint, mounts routers, health/version
  - Endpoints: /ask, /chat, /debug/embed, /debug/search
  - STT/TTS, Pronunciation Assessment
- `roleplay_api.py`
  - `/roleplay` endpoints: start, turn, hint, session info, list sessions, delete
- `roleplay_engine.py`
  - Roleplay orchestration (RAG → LLM → memory)
- `roleplay_referee.py`
  - Analyzes user messages; returns one prioritized correction
- `roleplay_scenarios.py`, `roleplay_session.py`
  - Scenarios and session state management
- `settings.py`
  - Loads .env and exposes strongly-typed settings (Azure/OpenAI/Qdrant)

---

## 3) Configuration (via .env → `settings.py`)
Do not commit secrets. Provide these as environment variables.

- Qdrant
  - `QDRANT_URL` (e.g., http://localhost:6333)
  - `QDRANT_COLLECTION` (e.g., rag_biz_english)

- Azure OpenAI (Chat)
  - `AZURE_OPENAI_KEY`
  - `AZURE_OPENAI_ENDPOINT` (e.g., https://<resource>.<region>.cognitiveservices.azure.com)
  - `AZURE_OPENAI_API_VERSION` (e.g., 2024-02-15-preview)
  - `AZURE_OPENAI_CHAT_DEPLOYMENT` (e.g., gpt-35-turbo)

- Azure OpenAI (Embeddings)
  - `AZURE_OPENAI_EMBEDDING_KEY` (can reuse chat key)
  - `AZURE_OPENAI_EMBEDDING_ENDPOINT` (can reuse chat endpoint)
  - `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` (e.g., text-embedding-3-small)

- Azure Speech Service
  - `AZURE_SPEECH_KEY`
  - `AZURE_SPEECH_REGION` (e.g., eastasia)

- OpenAI (fallback, non-Azure)
  - `OPENAI_API_KEY`
  - `CHAT_MODEL` (fallback, e.g., gpt-4o-mini)
  - `EMBED_MODEL` (fallback, e.g., text-embedding-3-small)

- Feature switches
  - `USE_AZURE` is derived automatically if Azure Chat key+endpoint are set
  - `USE_AZURE_EMBEDDINGS` is derived automatically if Azure Embedding key+endpoint are set

---

## 4) Models and Deployments (current intent)
- Chat: Azure OpenAI deployment `gpt-35-turbo` (region: Sweden Central)
- Embeddings: Azure OpenAI deployment `text-embedding-3-small` (region: UAE North)
- Speech: Azure Speech (region per env, e.g., eastasia)
- STT: OpenAI Whisper (`whisper-1`)
- TTS: OpenAI TTS (`tts-1`)

Note: Actual model used at runtime depends on env vars loaded by `settings.py`.

---

## 5) Endpoints (request/response contracts)

- GET `/health`
  - Response: `{ "status": "nowwww" }`

- GET `/version`
  - Response: `{ "version": "0.1.0", "env": "dev", "debug": true }`

- POST `/debug/embed`
  - Body: `{ "text": "..." }`
  - Response: `{ "dim": 1536 | 3072 }`

- GET `/debug/search?q=...&k=5`
  - Response: `{ "items": [{ "score": float, "src": string, "unit": string, "snippet": string }] }`

- POST `/ask`
  - Body: `{ "query": string, "k"?: int, "max_context_chars"?: int, "unit"?: string|null }`
  - Response: `{ "answer": string, "sources": string[] }`
  - Uses: Embeddings → Qdrant → Chat

- POST `/chat`
  - Body: `{ "messages": [{ "role": "user|assistant|system", "content": string }], "k"?: int, "maxContextChars"?: int, "unit"?: string|null }`
  - Response: `{ "answer": string, "sources": string[] }`
  - Free chat (no RAG grounding), with safety/system prompt

- Roleplay (`/roleplay` prefix)
  - POST `/roleplay/start` → session + opening message
  - POST `/roleplay/turn` → `{ ai_message, correction, current_stage, is_completed, feedback? }`
  - POST `/roleplay/hint` → `{ hint, hints_used }`
  - GET `/roleplay/session/{id}` → session info
  - GET `/roleplay/sessions` → list
  - DELETE `/roleplay/session/{id}` → delete

- Pronunciation (Azure Speech)
  - POST `/pronunciation/assess` (multipart: `audio`, `reference_text`)
    - Response: `{ transcript, accuracy_score, fluency_score, completeness_score, pronunciation_score, words: [{ word, accuracy_score, error_type?, phonemes?, ipa_expected?, ipa_actual?, feedback? }], feedback, detailed_feedback? }`
  - POST `/pronunciation/quick-check` (multipart)
    - Response: `{ score, feedback, transcript, needs_practice, mispronounced_words }`
  - GET `/pronunciation/test` → service/region info

- Speech (OpenAI)
  - POST `/stt` (file) → `{ text }`
  - POST `/tts` (form `text`) → MP3 audio

---

## 6) Data Flows

A) RAG Ask
1. Embed query → (Azure) Embeddings
2. ANN search → Qdrant (payload with OCR text & source_id)
3. Pack context within token budget
4. Chat completion (Azure Chat) with safe system prompt
5. Return `{answer, sources}`

B) Free Chat
- Direct chat completion (Azure Chat) with a teaching assistant system prompt

C) Roleplay Turn
1. Save student turn → session memory
2. RAG context for current stage (keywords)
3. Referee analyzes message (one prioritized correction)
4. Generate AI reply (Azure Chat) with scenario/stage system prompt and memory
5. Save AI turn → return message + structured correction

D) Pronunciation
1. Upload audio + reference text
2. Azure Speech Pronunciation Assessment → word/phoneme scores
3. Derive IPA (fallback dictionary) + actionable feedback
4. Return comprehensive or quick result

---

## 7) Operational Notes
- Collection dimensionality check at startup ensures embedding model matches Qdrant collection size (1536 for `text-embedding-3-small`, 3072 for `*-3-large`).
- Content filters: prompts are framed as educational/professional. Some casual input is sanitized in `/ask`.
- Logging: concise; Windows-safe UTF-8 configured; expect a 404 for `/favicon.ico` unless a favicon route is added.

---

## 8) Troubleshooting Cheatsheet
- 500 on `/chat` or `/ask` with model errors
  - Verify Azure deployment names (chat vs embedding) match env
  - Ensure keys/endpoints are set and in the correct region
- 400 "unsupported parameter"
  - Azure API versions differ in parameter names; see your current code for the exact parameter used (`max_tokens` vs `max_completion_tokens`).
- Qdrant dim mismatch assertion at startup
  - Recreate collection or adjust embedding model to match dim
- Speech errors
  - Confirm `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION`
- Android 404/Ngrok issues
  - Confirm ngrok URL, port, and app base URL are aligned

---

## 9) Minimal Runbook (local)
- Start Qdrant and load data (outside scope of this doc)
- Run server:
  - `uvicorn app:app --host 0.0.0.0 --port 8020 --reload`
- Smoke tests:
  - GET `/health` → 200 `{status:"nowwww"}`
  - GET `/version` → 200
  - POST `/ask` and `/chat` with small inputs

---

This document is safe to share with Android/ChatGPT. It contains no secrets and reflects the current server layout and intent. Adjust the env values per deployment.

