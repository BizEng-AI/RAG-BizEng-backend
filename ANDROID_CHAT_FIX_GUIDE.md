# 📱 ANDROID CHAT ENDPOINT INTEGRATION GUIDE
**Last Updated:** October 25, 2025  
**Server Status:** ✅ Fully Operational  
**Purpose:** Fix Android chat feature to work with server `/chat` endpoint

---

## 🚨 CURRENT ISSUE

Android is getting **HTTP 500 errors** when sending chat messages, but the server is working perfectly. The issue is a **request format mismatch**.

---

## ✅ WHAT THE SERVER EXPECTS

### Endpoint Details:
```
POST http://YOUR_SERVER_URL/chat
Content-Type: application/json
```

### Request Body Format:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, can you help me with business English?"
    }
  ]
}
```

### Response Format (200 OK):
```json
{
  "answer": "Of course! I'd be happy to help you with business English...",
  "sources": []
}
```

---

## 🔧 ANDROID IMPLEMENTATION FIX

### Step 1: Check Your DTOs (Data Classes)

**File: `ChatApi.kt` or `ChatModels.kt`**

Make sure your data classes look EXACTLY like this:

```kotlin
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class ChatReqDto(
    val messages: List<ChatMessage>
    // DO NOT include k, maxContextChars, or unit for simple chat
)

@Serializable
data class ChatMessage(
    val role: String,      // ← CRITICAL: Must be "role" not "sender", "type", "from", etc.
    val content: String
)

@Serializable
data class ChatRespDto(
    val answer: String,    // ← Server returns "answer" not "message" or "response"
    val sources: List<String> = emptyList()
)
```

---

### Step 2: Fix Your API Call

**File: `ChatRepository.kt` or `ChatViewModel.kt`**

#### ❌ WRONG - Common Mistakes:

```kotlin
// MISTAKE 1: Wrong role value
val message = ChatMessage(
    role = "me",           // ❌ Server only accepts "user", "assistant", "system"
    content = userInput
)

// MISTAKE 2: Wrong field name
val message = ChatMessage(
    sender = "user",       // ❌ Field must be "role" not "sender"
    content = userInput
)

// MISTAKE 3: Using wrong DTO
val request = AskReq(     // ❌ Don't use AskReq for chat, use ChatReqDto
    query = userInput
)
```

#### ✅ CORRECT Implementation:

```kotlin
// In your ChatViewModel or ChatRepository
suspend fun sendChatMessage(userInput: String): Result<String> {
    return try {
        // Build the message with correct format
        val userMessage = ChatMessage(
            role = "user",              // ✅ Must be "user" for student messages
            content = userInput
        )
        
        // Get conversation history (optional - for multi-turn chat)
        val conversationHistory = chatHistory.value.map { msg ->
            ChatMessage(
                role = if (msg.isFromUser) "user" else "assistant",
                content = msg.text
            )
        }
        
        // Create request with full history
        val request = ChatReqDto(
            messages = conversationHistory + userMessage
        )
        
        // Call API
        val response = chatApi.sendMessage(request)
        
        // Extract answer
        Result.success(response.answer)
        
    } catch (e: Exception) {
        Log.e("ChatViewModel", "Error sending message", e)
        Result.failure(e)
    }
}
```

---

### Step 3: Fix Your Retrofit/Ktor API Interface

**File: `ChatApi.kt`**

#### Using Retrofit:
```kotlin
interface ChatApi {
    @POST("chat")
    suspend fun sendMessage(
        @Body request: ChatReqDto
    ): ChatRespDto
}
```

#### Using Ktor:
```kotlin
class ChatApi(
    private val client: HttpClient,
    private val baseUrl: String
) {
    suspend fun sendMessage(request: ChatReqDto): ChatRespDto {
        val response = client.post("$baseUrl/chat") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        return response.body<ChatRespDto>()
    }
}
```

---

## 🧪 TESTING CHECKLIST

### Test Case 1: Simple Message
**Send:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello"}
  ]
}
```

**Expected Response:** HTTP 200 with answer

### Test Case 2: Conversation History
**Send:**
```json
{
  "messages": [
    {"role": "user", "content": "What is a professional greeting?"},
    {"role": "assistant", "content": "Use 'Dear' followed by name."},
    {"role": "user", "content": "Give me an example"}
  ]
}
```

**Expected Response:** HTTP 200 with contextual answer

### Test Case 3: Empty Message
**Send:**
```json
{
  "messages": [
    {"role": "user", "content": ""}
  ]
}
```

**Expected Response:** HTTP 200 (server handles it gracefully)

---

## 🐛 DEBUGGING GUIDE

### Error: HTTP 500 with "BadRequestError"

**Symptom:** Server returns 500 error with message about invalid role

**Cause:** Wrong `role` value in your ChatMessage

**Fix:**
```kotlin
// ❌ WRONG:
ChatMessage(role = "me", content = "...")
ChatMessage(role = "human", content = "...")
ChatMessage(role = "person", content = "...")

// ✅ CORRECT (only these 3 values are valid):
ChatMessage(role = "user", content = "...")      // For student messages
ChatMessage(role = "assistant", content = "...")  // For AI responses
ChatMessage(role = "system", content = "...")     // For system prompts (optional)
```

---

### Error: HTTP 422 "Field required"

**Symptom:** 
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "messages", 0, "role"],
      "msg": "Field required"
    }
  ]
}
```

**Cause:** Missing `role` or `content` field in ChatMessage

**Fix:**
```kotlin
// Make sure BOTH fields are present
data class ChatMessage(
    val role: String,     // ← Must be present
    val content: String   // ← Must be present
)
```

---

### Error: Can't deserialize response

**Symptom:** JsonDecodingException or similar error

**Cause:** Your response DTO expects wrong field names

**Fix:**
```kotlin
// ❌ WRONG:
data class ChatRespDto(
    val message: String    // Server sends "answer" not "message"
)

// ✅ CORRECT:
data class ChatRespDto(
    val answer: String     // Must match server's field name
)

// OR use @SerialName if you want different field names:
data class ChatRespDto(
    @SerialName("answer") val message: String  // Maps server's "answer" to your "message"
)
```

---

## 📊 COMPARISON: Chat vs Ask Endpoints

| Feature | `/chat` Endpoint | `/ask` Endpoint |
|---------|------------------|-----------------|
| Purpose | Free conversation | RAG-based Q&A |
| Request Field | `messages` (array) | `query` (string) |
| Conversation History | ✅ Supports multi-turn | ❌ Single question |
| Uses RAG/Qdrant | ❌ No | ✅ Yes |
| Response Field | `answer` | `answer` |
| Sources | Empty array `[]` | Array of source IDs |

**Don't mix them up!** Use `/chat` for conversational practice, use `/ask` for searching course materials.

---

## 🎯 COMPLETE WORKING EXAMPLE

Here's a full implementation that will work:

```kotlin
// ChatMessage.kt
@Serializable
data class ChatMessage(
    val role: String,
    val content: String
)

// ChatReqDto.kt
@Serializable
data class ChatReqDto(
    val messages: List<ChatMessage>
)

// ChatRespDto.kt
@Serializable
data class ChatRespDto(
    val answer: String,
    val sources: List<String> = emptyList()
)

// ChatApi.kt
interface ChatApi {
    @POST("chat")
    suspend fun sendMessage(@Body request: ChatReqDto): ChatRespDto
}

// ChatViewModel.kt
class ChatViewModel(
    private val chatApi: ChatApi
) : ViewModel() {
    
    private val _messages = MutableStateFlow<List<ChatUiMessage>>(emptyList())
    val messages: StateFlow<List<ChatUiMessage>> = _messages.asStateFlow()
    
    fun sendMessage(text: String) {
        viewModelScope.launch {
            try {
                // Add user message to UI
                _messages.value += ChatUiMessage(text, isFromUser = true)
                
                // Build conversation history for API
                val apiMessages = _messages.value.map { msg ->
                    ChatMessage(
                        role = if (msg.isFromUser) "user" else "assistant",
                        content = msg.text
                    )
                }
                
                // Call API
                val request = ChatReqDto(messages = apiMessages)
                val response = chatApi.sendMessage(request)
                
                // Add AI response to UI
                _messages.value += ChatUiMessage(
                    text = response.answer,
                    isFromUser = false
                )
                
            } catch (e: Exception) {
                Log.e("ChatViewModel", "Error sending message", e)
                // Show error to user
                _messages.value += ChatUiMessage(
                    text = "Error: ${e.message}",
                    isFromUser = false,
                    isError = true
                )
            }
        }
    }
}

// UI Message (for display only - not sent to server)
data class ChatUiMessage(
    val text: String,
    val isFromUser: Boolean,
    val isError: Boolean = false,
    val timestamp: Long = System.currentTimeMillis()
)
```

---

## ✅ VALIDATION CHECKLIST

Before testing, verify:

- [ ] DTO has `messages` field (array of ChatMessage objects)
- [ ] ChatMessage has BOTH `role` and `content` fields
- [ ] `role` value is EXACTLY `"user"` for student messages
- [ ] `role` value is EXACTLY `"assistant"` for AI responses (in history)
- [ ] Response DTO expects `answer` field (not `message` or `response`)
- [ ] Using POST method (not GET)
- [ ] Content-Type is `application/json`
- [ ] Endpoint is `/chat` (not `/ask` or `/roleplay/turn`)

---

## 🚀 EXPECTED BEHAVIOR AFTER FIX

1. User types message in chat screen
2. Android sends: `{"messages": [{"role": "user", "content": "..."}]}`
3. Server responds: HTTP 200 with `{"answer": "...", "sources": []}`
4. Android displays AI response in chat UI
5. For next message, Android includes full conversation history

---

## 📞 STILL HAVING ISSUES?

If you still get errors after following this guide:

1. **Enable logging** to see exact request/response:
```kotlin
val loggingInterceptor = HttpLoggingInterceptor().apply {
    level = HttpLoggingInterceptor.Level.BODY
}
```

2. **Check logs** for:
   - Actual JSON being sent
   - Server's error response
   - Any serialization exceptions

3. **Test with curl** to verify server is working:
```bash
curl -X POST http://YOUR_SERVER_URL/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'
```

If curl works but Android doesn't, the issue is definitely in Android's request formatting.

---

## 🎓 KEY TAKEAWAYS

1. **`role` field must be exactly:** `"user"`, `"assistant"`, or `"system"`
2. **Field names matter:** Use `role` not `sender`, use `answer` not `message`
3. **Include conversation history** for context-aware responses
4. **Don't confuse `/chat` with `/ask`** - they're different endpoints

---

**Server is ready and waiting! Just match this format and your chat will work perfectly.** ✅

