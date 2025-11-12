# 🎭 ROLEPLAY ENDPOINTS - ANDROID INTEGRATION GUIDE

**Date:** November 10, 2025  
**Status:** ✅ Endpoints tested and working  
**Base URL:** `https://bizeng-server.fly.dev`

---

## 🎯 ROLEPLAY FEATURE OVERVIEW

The roleplay system allows students to practice business English conversations in realistic scenarios with AI feedback.

### Available Scenarios:
1. **job_interview** (intermediate) - Practice interviewing for a job
2. **client_meeting** (advanced) - Negotiate with a potential client
3. **customer_complaint** (beginner) - Handle an unhappy customer
4. **team_meeting** (advanced) - Lead or participate in team discussions
5. **business_call** (beginner) - Professional phone conversation

---

## 📋 COMPLETE ENDPOINT REFERENCE

### 1. List All Scenarios
**Endpoint:** `GET /roleplay/scenarios`

**Request:**
```http
GET /roleplay/scenarios
```

**Response:**
```json
{
  "scenarios": [
    {
      "id": "job_interview",
      "title": "Job Interview",
      "description": "Practice interviewing for a marketing manager position",
      "difficulty": "intermediate",
      "student_role": "Job Candidate",
      "ai_role": "Hiring Manager"
    }
  ]
}
```

**Android DTO:**
```kotlin
data class ScenarioDto(
    val id: String,
    val title: String,
    val description: String,
    val difficulty: String,  // "beginner", "intermediate", "advanced"
    @SerialName("student_role") val studentRole: String,
    @SerialName("ai_role") val aiRole: String
)

data class ScenariosResponse(
    val scenarios: List<ScenarioDto>
)
```

---

### 2. Start Roleplay Session
**Endpoint:** `POST /roleplay/start`

**Request:**
```json
{
  "scenario_id": "job_interview",
  "student_name": "John Doe"
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "scenario_title": "Job Interview",
  "scenario_description": "Practice interviewing for a marketing manager position",
  "context": "You are interviewing for a marketing manager position at a tech startup...",
  "student_role": "Job Candidate",
  "ai_role": "Hiring Manager",
  "current_stage": "opening",
  "initial_message": "Good morning! Thank you for coming in today. I'm excited to learn more about you..."
}
```

**Android DTOs:**
```kotlin
data class RoleplayStartReqDto(
    @SerialName("scenario_id") val scenarioId: String,
    @SerialName("student_name") val studentName: String = "Student"
)

data class RoleplayStartRespDto(
    @SerialName("session_id") val sessionId: String,
    @SerialName("scenario_title") val scenarioTitle: String,
    @SerialName("scenario_description") val scenarioDescription: String,
    val context: String,
    @SerialName("student_role") val studentRole: String,
    @SerialName("ai_role") val aiRole: String,
    @SerialName("current_stage") val currentStage: String,
    @SerialName("initial_message") val initialMessage: String
)
```

---

### 3. Submit Turn (Main Roleplay Interaction)
**Endpoint:** `POST /roleplay/turn`

**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Hello, I'm very excited for this job opportunity"
}
```

**Response (No Errors):**
```json
{
  "ai_message": "I'm glad to hear that! Let's start by discussing your experience...",
  "correction": {
    "has_errors": false,
    "errors": [],
    "feedback": "Great job! Your response was appropriate."
  },
  "current_stage": "experience_discussion",
  "is_completed": false,
  "feedback": null
}
```

**Response (With Errors):**
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
        "explanation": "In formal interviews, use 'going to' instead of 'gonna'"
      },
      {
        "type": "grammar",
        "incorrect": "I done",
        "correct": "I did",
        "explanation": "Past tense should be 'did' not 'done'"
      }
    ],
    "feedback": "Priority: high. Keep practicing formal language!"
  },
  "current_stage": "experience_discussion",
  "is_completed": false,
  "feedback": null
}
```

**Android DTOs:**
```kotlin
data class RoleplayTurnReqDto(
    @SerialName("session_id") val sessionId: String,
    val message: String
)

data class ErrorDetailDto(
    val type: String,        // "grammar", "register", "vocabulary", "pragmatic"
    val incorrect: String,   // What the user said
    val correct: String,     // Correct version
    val explanation: String  // Why it's wrong and how to fix it
)

data class CorrectionDto(
    @SerialName("has_errors") val hasErrors: Boolean = false,
    val errors: List<ErrorDetailDto> = emptyList(),
    val feedback: String? = null  // Overall feedback like "Priority: high"
)

data class RoleplayTurnRespDto(
    @SerialName("ai_message") val aiMessage: String,
    val correction: CorrectionDto? = null,
    @SerialName("current_stage") val currentStage: String,
    @SerialName("is_completed") val isCompleted: Boolean = false,
    val feedback: String? = null  // Session completion feedback
)
```

---

### 4. Get Hint (Optional Feature)
**Endpoint:** `POST /roleplay/hint`

**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "hint": "Try asking about the company culture or team structure",
  "hints_used": 1
}
```

**Android DTOs:**
```kotlin
data class HintRequest(
    @SerialName("session_id") val sessionId: String
)

data class HintResponse(
    val hint: String,
    @SerialName("hints_used") val hintsUsed: Int
)
```

---

### 5. Get Session Info
**Endpoint:** `GET /roleplay/session/{session_id}`

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "scenario_id": "job_interview",
  "scenario_title": "Job Interview",
  "student_name": "John Doe",
  "current_stage": 2,
  "total_stages": 5,
  "started_at": "2025-11-10T10:30:00Z",
  "updated_at": "2025-11-10T10:45:00Z",
  "is_completed": false,
  "dialogue_history": [
    {
      "speaker": "ai",
      "message": "Good morning!",
      "timestamp": "2025-11-10T10:30:00Z",
      "correction": null
    },
    {
      "speaker": "student",
      "message": "Hello, I'm excited",
      "timestamp": "2025-11-10T10:31:00Z",
      "correction": null
    }
  ],
  "corrections_count": 0,
  "hints_used": 0
}
```

---

### 6. Delete Session
**Endpoint:** `DELETE /roleplay/session/{session_id}`

**Response:**
```json
{
  "status": "deleted",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## 🏗️ ANDROID ARCHITECTURE

### Recommended Structure:

```
app/src/main/java/com/example/bizeng/
├── data/
│   ├── remote/
│   │   ├── api/
│   │   │   └── RoleplayApi.kt          ← API calls
│   │   └── dto/
│   │       └── RoleplayDtos.kt         ← Request/Response models
│   └── repository/
│       └── RoleplayRepository.kt       ← Business logic
├── domain/
│   └── model/
│       ├── RoleplaySession.kt          ← Domain models
│       └── RoleplayMessage.kt
└── ui/
    └── roleplay/
        ├── RoleplayViewModel.kt        ← State management
        ├── RoleplayScreen.kt           ← Main conversation UI
        ├── ScenarioListScreen.kt       ← Scenario selection
        └── components/
            ├── MessageBubble.kt        ← Chat bubble
            ├── CorrectionCard.kt       ← Error feedback
            └── StageIndicator.kt       ← Progress indicator
```

---

## 💻 COMPLETE ANDROID IMPLEMENTATION

### 1. API Interface (Ktor)

```kotlin
// data/remote/api/RoleplayApi.kt
package com.example.bizeng.data.remote.api

import com.example.bizeng.data.remote.dto.*
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.request.*
import io.ktor.http.*

class RoleplayApi(
    private val client: HttpClient,
    private val baseUrl: String
) {
    suspend fun getScenarios(): ScenariosResponse {
        return client.get("$baseUrl/roleplay/scenarios").body()
    }

    suspend fun startSession(request: RoleplayStartReqDto): RoleplayStartRespDto {
        return client.post("$baseUrl/roleplay/start") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.body()
    }

    suspend fun submitTurn(request: RoleplayTurnReqDto): RoleplayTurnRespDto {
        return client.post("$baseUrl/roleplay/turn") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.body()
    }

    suspend fun getHint(sessionId: String): HintResponse {
        return client.post("$baseUrl/roleplay/hint") {
            contentType(ContentType.Application.Json)
            setBody(HintRequest(sessionId))
        }.body()
    }

    suspend fun deleteSession(sessionId: String) {
        client.delete("$baseUrl/roleplay/session/$sessionId")
    }
}
```

---

### 2. DTOs (Complete)

```kotlin
// data/remote/dto/RoleplayDtos.kt
package com.example.bizeng.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class ScenarioDto(
    val id: String,
    val title: String,
    val description: String,
    val difficulty: String,
    @SerialName("student_role") val studentRole: String,
    @SerialName("ai_role") val aiRole: String
)

@Serializable
data class ScenariosResponse(
    val scenarios: List<ScenarioDto>
)

@Serializable
data class RoleplayStartReqDto(
    @SerialName("scenario_id") val scenarioId: String,
    @SerialName("student_name") val studentName: String = "Student"
)

@Serializable
data class RoleplayStartRespDto(
    @SerialName("session_id") val sessionId: String,
    @SerialName("scenario_title") val scenarioTitle: String,
    @SerialName("scenario_description") val scenarioDescription: String,
    val context: String,
    @SerialName("student_role") val studentRole: String,
    @SerialName("ai_role") val aiRole: String,
    @SerialName("current_stage") val currentStage: String,
    @SerialName("initial_message") val initialMessage: String
)

@Serializable
data class RoleplayTurnReqDto(
    @SerialName("session_id") val sessionId: String,
    val message: String
)

@Serializable
data class ErrorDetailDto(
    val type: String,
    val incorrect: String,
    val correct: String,
    val explanation: String
)

@Serializable
data class CorrectionDto(
    @SerialName("has_errors") val hasErrors: Boolean = false,
    val errors: List<ErrorDetailDto> = emptyList(),
    val feedback: String? = null
)

@Serializable
data class RoleplayTurnRespDto(
    @SerialName("ai_message") val aiMessage: String,
    val correction: CorrectionDto? = null,
    @SerialName("current_stage") val currentStage: String,
    @SerialName("is_completed") val isCompleted: Boolean = false,
    val feedback: String? = null
)

@Serializable
data class HintRequest(
    @SerialName("session_id") val sessionId: String
)

@Serializable
data class HintResponse(
    val hint: String,
    @SerialName("hints_used") val hintsUsed: Int
)
```

---

### 3. Repository

```kotlin
// data/repository/RoleplayRepository.kt
package com.example.bizeng.data.repository

import com.example.bizeng.data.remote.api.RoleplayApi
import com.example.bizeng.data.remote.dto.*
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import javax.inject.Inject

class RoleplayRepository @Inject constructor(
    private val api: RoleplayApi
) {
    suspend fun getScenarios(): Result<List<ScenarioDto>> = runCatching {
        api.getScenarios().scenarios
    }

    suspend fun startSession(
        scenarioId: String,
        studentName: String
    ): Result<RoleplayStartRespDto> = runCatching {
        api.startSession(RoleplayStartReqDto(scenarioId, studentName))
    }

    suspend fun submitTurn(
        sessionId: String,
        message: String
    ): Result<RoleplayTurnRespDto> = runCatching {
        api.submitTurn(RoleplayTurnReqDto(sessionId, message))
    }

    suspend fun getHint(sessionId: String): Result<String> = runCatching {
        api.getHint(sessionId).hint
    }

    suspend fun endSession(sessionId: String): Result<Unit> = runCatching {
        api.deleteSession(sessionId)
    }
}
```

---

### 4. ViewModel

```kotlin
// ui/roleplay/RoleplayViewModel.kt
package com.example.bizeng.ui.roleplay

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.bizeng.data.remote.dto.*
import com.example.bizeng.data.repository.RoleplayRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class RoleplayViewModel @Inject constructor(
    private val repository: RoleplayRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<RoleplayUiState>(RoleplayUiState.Idle)
    val uiState: StateFlow<RoleplayUiState> = _uiState.asStateFlow()

    private val _messages = MutableStateFlow<List<Message>>(emptyList())
    val messages: StateFlow<List<Message>> = _messages.asStateFlow()

    private var currentSessionId: String? = null

    fun loadScenarios() {
        viewModelScope.launch {
            _uiState.value = RoleplayUiState.Loading
            repository.getScenarios()
                .onSuccess { scenarios ->
                    _uiState.value = RoleplayUiState.ScenarioSelection(scenarios)
                }
                .onFailure { error ->
                    _uiState.value = RoleplayUiState.Error(error.message ?: "Failed to load scenarios")
                }
        }
    }

    fun startSession(scenarioId: String, studentName: String) {
        viewModelScope.launch {
            _uiState.value = RoleplayUiState.Loading
            repository.startSession(scenarioId, studentName)
                .onSuccess { response ->
                    currentSessionId = response.sessionId
                    _messages.value = listOf(
                        Message(
                            id = "0",
                            sender = MessageSender.AI,
                            content = response.initialMessage,
                            timestamp = System.currentTimeMillis(),
                            correction = null
                        )
                    )
                    _uiState.value = RoleplayUiState.Active(
                        sessionId = response.sessionId,
                        scenarioTitle = response.scenarioTitle,
                        currentStage = response.currentStage,
                        isCompleted = false
                    )
                }
                .onFailure { error ->
                    _uiState.value = RoleplayUiState.Error(error.message ?: "Failed to start session")
                }
        }
    }

    fun sendMessage(message: String) {
        val sessionId = currentSessionId ?: return
        
        // Add user message immediately
        val userMessage = Message(
            id = System.currentTimeMillis().toString(),
            sender = MessageSender.Student,
            content = message,
            timestamp = System.currentTimeMillis(),
            correction = null
        )
        _messages.value += userMessage

        viewModelScope.launch {
            _uiState.value = (_uiState.value as? RoleplayUiState.Active)?.copy(isProcessing = true)
                ?: _uiState.value

            repository.submitTurn(sessionId, message)
                .onSuccess { response ->
                    // Add AI response
                    val aiMessage = Message(
                        id = System.currentTimeMillis().toString(),
                        sender = MessageSender.AI,
                        content = response.aiMessage,
                        timestamp = System.currentTimeMillis(),
                        correction = null
                    )
                    _messages.value += aiMessage

                    // Show correction if any
                    if (response.correction?.hasErrors == true) {
                        _messages.value = _messages.value.map { msg ->
                            if (msg.id == userMessage.id) {
                                msg.copy(correction = response.correction)
                            } else msg
                        }
                    }

                    // Update state
                    _uiState.value = RoleplayUiState.Active(
                        sessionId = sessionId,
                        scenarioTitle = (_uiState.value as? RoleplayUiState.Active)?.scenarioTitle ?: "",
                        currentStage = response.currentStage,
                        isCompleted = response.isCompleted,
                        isProcessing = false
                    )
                }
                .onFailure { error ->
                    _uiState.value = RoleplayUiState.Error(error.message ?: "Failed to send message")
                }
        }
    }

    fun requestHint() {
        val sessionId = currentSessionId ?: return
        viewModelScope.launch {
            repository.getHint(sessionId)
                .onSuccess { hint ->
                    _messages.value += Message(
                        id = System.currentTimeMillis().toString(),
                        sender = MessageSender.System,
                        content = "💡 Hint: $hint",
                        timestamp = System.currentTimeMillis(),
                        correction = null
                    )
                }
                .onFailure { error ->
                    // Handle error silently or show toast
                }
        }
    }

    fun endSession() {
        val sessionId = currentSessionId ?: return
        viewModelScope.launch {
            repository.endSession(sessionId)
            currentSessionId = null
            _messages.value = emptyList()
            _uiState.value = RoleplayUiState.Idle
        }
    }
}

// UI State
sealed class RoleplayUiState {
    object Idle : RoleplayUiState()
    object Loading : RoleplayUiState()
    data class ScenarioSelection(val scenarios: List<ScenarioDto>) : RoleplayUiState()
    data class Active(
        val sessionId: String,
        val scenarioTitle: String,
        val currentStage: String,
        val isCompleted: Boolean,
        val isProcessing: Boolean = false
    ) : RoleplayUiState()
    data class Error(val message: String) : RoleplayUiState()
}

// Message Model
data class Message(
    val id: String,
    val sender: MessageSender,
    val content: String,
    val timestamp: Long,
    val correction: CorrectionDto?
)

enum class MessageSender {
    Student, AI, System
}
```

---

## 🧪 TESTING CHECKLIST

### Local Testing (localhost:8020)
```kotlin
// Change base URL temporarily
val baseUrl = "http://10.0.2.2:8020"  // Emulator
// val baseUrl = "http://YOUR_LOCAL_IP:8020"  // Physical device
```

Test sequence:
1. [ ] Load scenarios → Should show 5 scenarios
2. [ ] Start session → Should receive initial AI message
3. [ ] Send message → Should get AI response
4. [ ] Send message with errors → Should get correction
5. [ ] Complete session → Should mark as completed
6. [ ] Request hint → Should receive helpful suggestion

### Production Testing (bizeng-server.fly.dev)
```kotlin
val baseUrl = "https://bizeng-server.fly.dev"
```

Same tests as local.

---

## 🎨 UI RECOMMENDATIONS

### Message Bubble Colors
- **Student messages:** Blue/Purple (right-aligned)
- **AI messages:** Gray (left-aligned)
- **System messages:** Yellow/Orange (centered)

### Correction Display
When `correction.has_errors == true`:
```
┌─────────────────────────────────┐
│ ⚠️ Language Feedback           │
├─────────────────────────────────┤
│ ❌ "gonna" → ✅ "going to"     │
│ 📝 Use formal language         │
├─────────────────────────────────┤
│ Priority: high                  │
└─────────────────────────────────┘
```

### Stage Progress
```
Opening ━━━●━━━━━━━ Experience ━━━━━━━━━ Closing
```

---

## ⚠️ IMPORTANT NOTES

### 1. Session Management
- Sessions are stored server-side
- Session IDs are UUIDs (unique per session)
- Save session ID in ViewModel or local storage
- Sessions persist across app restarts

### 2. Error Types
- **grammar**: Tense, subject-verb agreement, articles
- **register**: Too casual/formal for business context
- **vocabulary**: Wrong word choice
- **pragmatic**: Culturally inappropriate or unclear

### 3. Stage Progression
- Stages automatically advance based on conversation
- `current_stage` changes when AI determines student is ready
- No manual stage progression needed

### 4. Completion
- `is_completed = true` when all stages finished
- Show completion feedback to user
- Offer to start new scenario

---

## 📊 EXPECTED USER FLOW

```
1. User opens Roleplay feature
   ↓
2. App calls GET /roleplay/scenarios
   ↓
3. User selects "Job Interview"
   ↓
4. App calls POST /roleplay/start
   ↓
5. Display AI's initial message
   ↓
6. User types response
   ↓
7. App calls POST /roleplay/turn
   ↓
8. Display AI response + corrections (if any)
   ↓
9. Repeat steps 6-8 until is_completed = true
   ↓
10. Show completion screen
    ↓
11. App calls DELETE /roleplay/session/{id}
```

---

## ✅ QUICK START SUMMARY

1. **Copy DTOs** from this document
2. **Implement API calls** using Ktor
3. **Create ViewModel** with state management
4. **Build UI** with message list + input field
5. **Test** with production URL

**All endpoints are working and tested!** 🎉

---

**Status:** ✅ Complete implementation guide  
**Tested:** ✅ All endpoints verified on localhost and production  
**Ready for:** Android integration

