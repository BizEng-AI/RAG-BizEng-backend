# 🎭 ROLEPLAY QUICK REFERENCE - FOR ANDROID

**Status:** ✅ Endpoints working on production  
**Base URL:** `https://bizeng-server.fly.dev`

---

## 📋 QUICK ENDPOINT SUMMARY

### 1. List Scenarios
```
GET /roleplay/scenarios
→ Returns list of 5 available scenarios
```

### 2. Start Session
```
POST /roleplay/start
Body: {"scenario_id": "job_interview", "student_name": "John"}
→ Returns session_id + initial AI message
```

### 3. Submit Turn (Main Interaction)
```
POST /roleplay/turn
Body: {"session_id": "uuid", "message": "Hello"}
→ Returns AI response + corrections + stage info
```

### 4. Get Hint (Optional)
```
POST /roleplay/hint
Body: {"session_id": "uuid"}
→ Returns helpful suggestion
```

### 5. Delete Session
```
DELETE /roleplay/session/{session_id}
→ Cleans up completed session
```

---

## 💻 MINIMAL ANDROID CODE

### DTOs (Copy These Exactly)
```kotlin
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
```

### API Calls (Ktor)
```kotlin
class RoleplayApi(private val client: HttpClient, private val baseUrl: String) {
    
    suspend fun startSession(scenarioId: String, studentName: String): RoleplayStartRespDto {
        return client.post("$baseUrl/roleplay/start") {
            contentType(ContentType.Application.Json)
            setBody(RoleplayStartReqDto(scenarioId, studentName))
        }.body()
    }

    suspend fun submitTurn(sessionId: String, message: String): RoleplayTurnRespDto {
        return client.post("$baseUrl/roleplay/turn") {
            contentType(ContentType.Application.Json)
            setBody(RoleplayTurnReqDto(sessionId, message))
        }.body()
    }
}
```

---

## 🎯 TYPICAL FLOW

```kotlin
// 1. Start session
val startResponse = api.startSession("job_interview", "John")
val sessionId = startResponse.sessionId
displayMessage(startResponse.initialMessage, isAI = true)

// 2. User types and sends message
val userMessage = "Hello, I'm excited for this opportunity"
displayMessage(userMessage, isAI = false)

// 3. Submit turn
val turnResponse = api.submitTurn(sessionId, userMessage)

// 4. Display AI response
displayMessage(turnResponse.aiMessage, isAI = true)

// 5. Show corrections if any
if (turnResponse.correction?.hasErrors == true) {
    displayCorrections(turnResponse.correction.errors)
}

// 6. Repeat 2-5 until isCompleted = true
```

---

## ⚠️ KEY POINTS

### Response Structure
```json
{
  "ai_message": "AI's conversational response",
  "correction": {
    "has_errors": true/false,
    "errors": [
      {
        "type": "grammar",
        "incorrect": "what user said",
        "correct": "correct version",
        "explanation": "why it's wrong"
      }
    ],
    "feedback": "Priority: high"
  },
  "current_stage": "experience_discussion",
  "is_completed": false
}
```

### Error Types
- `grammar` - Tense, articles, subject-verb agreement
- `register` - Too casual/formal for business
- `vocabulary` - Wrong word choice
- `pragmatic` - Culturally inappropriate

### Scenarios Available
1. `job_interview` (intermediate)
2. `client_meeting` (advanced)
3. `customer_complaint` (beginner)
4. `team_meeting` (advanced)
5. `business_call` (beginner)

---

## ✅ TESTING URLS

**Local:**
- `http://10.0.2.2:8020/roleplay/scenarios` (emulator)
- `http://YOUR_LOCAL_IP:8020/roleplay/scenarios` (physical device)

**Production:**
- `https://bizeng-server.fly.dev/roleplay/scenarios`
- `https://bizeng-server.fly.dev/roleplay/start`
- `https://bizeng-server.fly.dev/roleplay/turn`

---

## 📄 FULL DOCUMENTATION

For complete implementation with ViewModel, Repository, and UI examples:
→ See `ROLEPLAY_ANDROID_INTEGRATION.md`

---

**Quick Start:** Copy the DTOs and API calls above, test with production URL, you're done! 🚀

