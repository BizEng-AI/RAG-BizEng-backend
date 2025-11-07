# 📱 COMPLETE ANDROID INTEGRATION REFERENCE
**Generated:** October 25, 2025  
**Server Port:** 8020  
**Base URL:** `http://YOUR_NGROK_URL` or `http://localhost:8020`

---

## 🔐 AZURE CREDENTIALS

### 1. Azure OpenAI - Chat (Sweden Central)
```
Endpoint: https://sanja-mh654t02-swedencentral.cognitiveservices.azure.com/
API Key: DuQJzDcQmb9siNeUiiUsgaENRgewWHd9FLM4dJd0FJdQe9SAulRhJQQJ99BJACfhMk5XJ3w3AAAAACOGDSnb
API Version: 2024-12-01-preview
Deployment Name: gpt-35-turbo
Model: gpt-35-turbo
```

### 2. Azure OpenAI - Embeddings (UAE North)
```
Endpoint: https://sanja-mh6697hv-uaenorth.cognitiveservices.azure.com/
API Key: 9fyw2LxxdqRgay7cAuK84FXP7TwWMm1HC2QOMy5u5oeKKVt8lyTdJQQJ99BJACF24PCXJ3w3AAAAACOGMrGx
API Version: 2024-02-15-preview
Deployment Name: text-embedding-3-small
Model: text-embedding-3-small
```

### 3. Azure Speech Service (East Asia)
```
API Key: CbZ50wqN8vOc9BwwgUZak4sKkHqtUZSjj31bayNGIVaIn47214zRJQQJ99BJAC3pKaRXJ3w3AAAYACOGKoCE
Region: eastasia
Endpoint: https://eastasia.api.cognitive.microsoft.com/
```

---

## 🌐 SERVER ENDPOINTS

### ✅ 1. Health Check
**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "nowwww"
}
```

---

### ✅ 2. Version Check
**Endpoint:** `GET /version`

**Response:**
```json
{
  "version": "0.1.0",
  "env": "dev",
  "debug": true
}
```

---

### 💬 3. Free Chat Mode
**Endpoint:** `POST /chat`

**Purpose:** Conversational AI for business English learning (no RAG, just chat)

**Request Body:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "How do I write a professional email?"
    }
  ],
  "k": 5,
  "maxContextChars": 6000,
  "unit": null
}
```

**Response:**
```json
{
  "answer": "To write a professional email, start with...",
  "sources": []
}
```

**Models Used:**
- Chat: `gpt-35-turbo` (Azure Sweden Central)

---

### 📚 4. RAG-Based Question Answering
**Endpoint:** `POST /ask`

**Purpose:** Answer questions grounded in your business English materials (uses Qdrant + RAG)

**Request Body:**
```json
{
  "query": "What are the stages of a business meeting?",
  "k": 5,
  "max_context_chars": 6000,
  "unit": null
}
```

**Response:**
```json
{
  "answer": "Based on the materials...",
  "sources": ["unit_1_page_3", "unit_2_page_5"]
}
```

**Models Used:**
- Embeddings: `text-embedding-3-small` (Azure UAE North)
- Chat: `gpt-35-turbo` (Azure Sweden Central)

---

### 🎭 5. Roleplay - List Scenarios
**Endpoint:** `GET /roleplay/scenarios`

**Query Parameters:**
- `difficulty` (optional): `beginner`, `intermediate`, `advanced`

**Response:**
```json
{
  "scenarios": [
    {
      "id": "job_interview",
      "title": "Job Interview",
      "description": "Practice interviewing for a job position",
      "difficulty": "intermediate"
    },
    {
      "id": "client_meeting",
      "title": "Client Meeting",
      "description": "Conduct a professional client meeting",
      "difficulty": "advanced"
    }
  ]
}
```

---

### 🎭 6. Roleplay - Get Scenario Details
**Endpoint:** `GET /roleplay/scenarios/{scenario_id}`

**Example:** `GET /roleplay/scenarios/job_interview`

**Response:**
```json
{
  "id": "job_interview",
  "title": "Job Interview",
  "description": "Practice interviewing for a job position",
  "difficulty": "intermediate",
  "context": "You are interviewing for a marketing position...",
  "student_role": "Job Candidate",
  "ai_role": "HR Manager",
  "stages": [
    {
      "name": "opening",
      "objective": "Introduce yourself professionally",
      "hints_available": 3
    }
  ]
}
```

---

### 🎭 7. Roleplay - Start Session
**Endpoint:** `POST /roleplay/start`

**Purpose:** Begin a new roleplay session

**Request Body:**
```json
{
  "scenario_id": "job_interview",
  "student_name": "John Doe"
}
```

**Response:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "scenario_title": "Job Interview",
  "scenario_description": "Practice interviewing for a job position",
  "context": "You are interviewing for a marketing position...",
  "student_role": "Job Candidate",
  "ai_role": "HR Manager",
  "initial_message": "Good morning! Thank you for coming in today. Please, have a seat...",
  "stage_info": {
    "current_stage": 0,
    "total_stages": 3,
    "stage_name": "opening",
    "objective": "Introduce yourself professionally"
  }
}
```

**Models Used:**
- Chat: `gpt-35-turbo` (Azure Sweden Central)

---

### 🎭 8. Roleplay - Submit Turn
**Endpoint:** `POST /roleplay/turn`

**Purpose:** Send student's message and get AI response with corrections

**Request Body:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Hello, I'm very excited for this opportunity"
}
```

**Response:**
```json
{
  "ai_message": "That's wonderful! Tell me about your background and experience.",
  "correction": {
    "has_errors": false,
    "errors": [],
    "feedback": "Great job! Your response was appropriate."
  },
  "stage_info": {
    "current_stage": 0,
    "total_stages": 3,
    "stage_name": "opening",
    "objective": "Introduce yourself professionally"
  },
  "stage_advanced": false,
  "is_completed": false
}
```

**Response with Error:**
```json
{
  "ai_message": "I see. Could you elaborate on that?",
  "correction": {
    "has_errors": true,
    "errors": [
      {
        "type": "register",
        "incorrect": "gonna",
        "correct": "going to",
        "explanation": "Use 'going to' instead of 'gonna' in professional settings"
      }
    ],
    "feedback": "Priority: high. Keep practicing!"
  },
  "stage_info": {...},
  "stage_advanced": false,
  "is_completed": false
}
```

**Models Used:**
- Embeddings: `text-embedding-3-small` (Azure UAE North) - for RAG context retrieval
- Chat: `gpt-35-turbo` (Azure Sweden Central) - for AI response and error analysis

---

### 🎭 9. Roleplay - Get Hint
**Endpoint:** `POST /roleplay/hint`

**Purpose:** Get a hint for the current stage

**Request Body:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Response:**
```json
{
  "hint": "Try mentioning your relevant work experience",
  "hints_used": 1
}
```

---

### 🎭 10. Roleplay - Get Session Info
**Endpoint:** `GET /roleplay/session/{session_id}`

**Example:** `GET /roleplay/session/123e4567-e89b-12d3-a456-426614174000`

**Response:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "scenario_id": "job_interview",
  "scenario_title": "Job Interview",
  "student_name": "John Doe",
  "current_stage": 1,
  "total_stages": 3,
  "started_at": "2025-10-25T10:30:00",
  "updated_at": "2025-10-25T10:45:00",
  "is_completed": false,
  "dialogue_history": [
    {
      "speaker": "ai",
      "message": "Good morning!",
      "timestamp": "2025-10-25T10:30:00",
      "correction": null
    }
  ],
  "corrections_count": 2,
  "hints_used": 1
}
```

---

### 🎭 11. Roleplay - List Sessions
**Endpoint:** `GET /roleplay/sessions`

**Query Parameters:**
- `student_name` (optional): Filter by student name
- `active_only` (optional): `true` or `false`

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "123e4567-e89b-12d3-a456-426614174000",
      "scenario_id": "job_interview",
      "student_name": "John Doe",
      "is_completed": false,
      "started_at": "2025-10-25T10:30:00"
    }
  ]
}
```

---

### 🎭 12. Roleplay - Delete Session
**Endpoint:** `DELETE /roleplay/session/{session_id}`

**Response:**
```json
{
  "message": "Session deleted successfully"
}
```

---

### 🎤 13. Pronunciation Assessment
**Endpoint:** `POST /pronunciation/assess`

**Purpose:** Assess pronunciation of recorded audio against reference text

**Request:** `multipart/form-data`
- `audio`: Audio file (WAV, MP3, M4A)
- `reference_text`: Text that should be spoken (e.g., "Good morning, I would like to schedule a meeting")

**Response:**
```json
{
  "transcript": "Good morning I would like to schedule a meeting",
  "accuracy_score": 85.5,
  "fluency_score": 78.2,
  "completeness_score": 95.0,
  "pronunciation_score": 82.3,
  "words": [
    {
      "word": "Good",
      "accuracy_score": 95.0,
      "error_type": null
    },
    {
      "word": "morning",
      "accuracy_score": 55.0,
      "error_type": "Mispronunciation"
    }
  ],
  "feedback": "Good pronunciation! Keep practicing. Words to practice: 'morning'. Focus on pronouncing each word clearly."
}
```

**Azure Service Used:**
- Azure Speech Service (East Asia)

---

### 🎤 14. Quick Pronunciation Check
**Endpoint:** `POST /pronunciation/quick-check`

**Purpose:** Simplified pronunciation check for integration into chat/roleplay

**Request:** `multipart/form-data`
- `audio`: Audio file
- `reference_text`: Text that should be spoken

**Response:**
```json
{
  "score": 82.3,
  "feedback": "Good pronunciation! Keep practicing.",
  "transcript": "Good morning I would like to schedule a meeting",
  "needs_practice": false,
  "mispronounced_words": ["morning"]
}
```

---

### 🎤 15. Test Pronunciation Service
**Endpoint:** `GET /pronunciation/test`

**Response:**
```json
{
  "status": "ok",
  "region": "eastasia",
  "service": "Azure Speech Service",
  "features": [
    "Pronunciation Assessment",
    "Word-level scoring",
    "Fluency analysis",
    "Accuracy measurement"
  ]
}
```

---

### 🎙️ 16. Speech-to-Text (STT)
**Endpoint:** `POST /stt`

**Purpose:** Transcribe audio to text using OpenAI Whisper

**Request:** `multipart/form-data`
- `file`: Audio file (WAV, MP3, M4A)

**Response:**
```json
{
  "text": "Hello, this is a test of the speech to text feature"
}
```

**Models Used:**
- Whisper: `whisper-1` (OpenAI - not Azure)

---

### 🔊 17. Text-to-Speech (TTS)
**Endpoint:** `POST /tts`

**Purpose:** Convert text to speech audio

**Request:** `application/x-www-form-urlencoded`
- `text`: Text to convert to speech

**Response:** Audio file (MP3 format)
- Content-Type: `audio/mpeg`

**Models Used:**
- TTS: `tts-1` (OpenAI - not Azure)

---

### 🔍 18. Debug - Embedding Test
**Endpoint:** `POST /debug/embed`

**Purpose:** Test embedding generation

**Request Body:**
```json
{
  "text": "This is a test"
}
```

**Response:**
```json
{
  "dim": 1536
}
```

**Models Used:**
- Embeddings: `text-embedding-3-small` (Azure UAE North)

---

### 🔍 19. Debug - Search Test
**Endpoint:** `GET /debug/search`

**Query Parameters:**
- `q`: Search query (required)
- `k`: Number of results (default: 5)

**Example:** `GET /debug/search?q=business%20meeting&k=3`

**Response:**
```json
{
  "items": [
    {
      "score": 0.85,
      "src": "unit_1_page_3",
      "unit": "1",
      "snippet": "A business meeting typically has three stages: opening, discussion, and closing..."
    }
  ]
}
```

**Models Used:**
- Embeddings: `text-embedding-3-small` (Azure UAE North)

---

## 📊 MODEL SUMMARY

| Feature | Service | Model/Deployment | Region | API Key (Last 4) |
|---------|---------|------------------|--------|------------------|
| Chat | Azure OpenAI | gpt-35-turbo | Sweden Central | DSnb |
| Embeddings | Azure OpenAI | text-embedding-3-small | UAE North | MrGx |
| Pronunciation | Azure Speech | N/A | East Asia | KoCE |
| STT (Whisper) | OpenAI | whisper-1 | N/A | (fallback) |
| TTS | OpenAI | tts-1 | N/A | (fallback) |

---

## 🔧 CORRECTION FORMAT (ANDROID SIDE)

### What Android Receives:
```json
{
  "has_errors": true,
  "errors": [
    {
      "type": "grammar|register|vocabulary|pragmatic",
      "incorrect": "gonna",
      "correct": "going to",
      "explanation": "Use 'going to' in professional settings"
    }
  ],
  "feedback": "Priority: high. Keep practicing!"
}
```

### Error Types:
- `grammar` - Grammar mistakes (tenses, articles, etc.)
- `register` - Too casual/formal (e.g., "Hey" vs "Hello")
- `vocabulary` - Wrong word choice
- `pragmatic` - Culturally inappropriate or unclear

---

## ⚙️ QDRANT CONFIGURATION

```
URL: http://localhost:6333
Collection: rag_biz_english
Vector Dimension: 1536 (matches text-embedding-3-small)
```

⚠️ **Note:** If Android needs direct access to Qdrant, update URL to server's external IP/domain.

---

## 🚀 TESTING ENDPOINTS

### Quick Test Script (curl):

```bash
# Health check
curl http://localhost:8020/health

# Chat
curl -X POST http://localhost:8020/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'

# Start roleplay
curl -X POST http://localhost:8020/roleplay/start \
  -H "Content-Type: application/json" \
  -d '{"scenario_id":"job_interview","student_name":"Test"}'

# Submit turn (use session_id from above)
curl -X POST http://localhost:8020/roleplay/turn \
  -H "Content-Type: application/json" \
  -d '{"session_id":"YOUR_SESSION_ID","message":"Hello, nice to meet you"}'
```

---

## 🔐 SECURITY NOTES

1. **API Keys:** All shown for internal development. In production:
   - Use environment variables
   - Rotate keys regularly
   - Never commit to public repos

2. **Ngrok:** Free tier has 2-hour timeout. Restart and update Android URL.

3. **CORS:** Server allows all origins. In production, restrict to your domain.

---

## 📱 ANDROID IMPLEMENTATION CHECKLIST

### NetworkModule.kt:
```kotlin
private const val BASE_URL = "https://YOUR_NGROK_URL/"
// OR for local testing:
private const val BASE_URL = "http://10.0.2.2:8020/" // Android emulator
```

### API Service Interfaces:
```kotlin
interface RoleplayApi {
    @POST("roleplay/start")
    suspend fun startRoleplay(@Body request: StartRequest): StartResponse
    
    @POST("roleplay/turn")
    suspend fun submitTurn(@Body request: TurnRequest): TurnResponse
    
    @POST("roleplay/hint")
    suspend fun getHint(@Body request: HintRequest): HintResponse
}

interface PronunciationApi {
    @Multipart
    @POST("pronunciation/assess")
    suspend fun assessPronunciation(
        @Part audio: MultipartBody.Part,
        @Part("reference_text") referenceText: RequestBody
    ): PronunciationResult
}

interface ChatApi {
    @POST("chat")
    suspend fun sendMessage(@Body request: ChatRequest): ChatResponse
}
```

### Error Handling:
```kotlin
try {
    val response = api.submitTurn(request)
    if (response.correction.has_errors) {
        // Display correction in red box
    }
} catch (e: HttpException) {
    when (e.code()) {
        404 -> "Session not found"
        500 -> "Server error - check logs"
        else -> "Network error"
    }
}
```

---

## 🐛 COMMON ERRORS & FIXES

| Error | Cause | Fix |
|-------|-------|-----|
| HTTP 500: Model not found | Wrong deployment name | Use exact deployment names above |
| HTTP 404: Ngrok offline | Ngrok expired | Restart ngrok, update Android URL |
| HTTP 401: Unauthorized | Wrong API key | Check API keys above |
| Correction not showing | Format mismatch | ✅ Fixed - server now converts format |
| Empty response | Server crash | Check server logs, restart server |

---

**Last Updated:** October 25, 2025  
**Server Version:** 4.0 (Azure Optimized)  
**All Critical Issues:** ✅ FIXED

