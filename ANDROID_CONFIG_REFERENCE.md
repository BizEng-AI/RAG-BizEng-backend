# Azure Configuration Reference for Android App
**Generated:** October 25, 2025  
**Purpose:** This document contains all server-side Azure configurations that the Android app must match.

---

## 🔴 CRITICAL: All endpoints, API keys, and deployment names below MUST match exactly on Android side

---

## 1️⃣ Azure OpenAI - CHAT SERVICE (Sweden Central)

**Purpose:** Used for chat completions (GPT conversations, roleplay, etc.)

```
ENDPOINT: https://sanja-mh654t02-swedencentral.cognitiveservices.azure.com/
API_KEY: DuQJzDcQmb9siNeUiiUsgaENRgewWHd9FLM4dJd0FJdQe9SAulRhJQQJ99BJACfhMk5XJ3w3AAAAACOGDSnb
API_VERSION: 2024-12-01-preview
DEPLOYMENT_NAME: gpt-35-turbo
MODEL: gpt-35-turbo
REGION: swedencentral
```

**Full Chat Endpoint:**
```
https://sanja-mh654t02-swedencentral.cognitiveservices.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-12-01-preview
```

---

## 2️⃣ Azure OpenAI - EMBEDDING SERVICE (UAE North)

**Purpose:** Used for text embeddings (RAG, semantic search, Qdrant ingestion)

```
ENDPOINT: https://sanja-mh6697hv-uaenorth.cognitiveservices.azure.com/
API_KEY: 9fyw2LxxdqRgay7cAuK84FXP7TwWMm1HC2QOMy5u5oeKKVt8lyTdJQQJ99BJACF24PCXJ3w3AAAAACOGMrGx
API_VERSION: 2024-02-15-preview
DEPLOYMENT_NAME: text-embedding-3-small
MODEL: text-embedding-3-small
REGION: uaenorth
```

**Full Embedding Endpoint:**
```
https://sanja-mh6697hv-uaenorth.cognitiveservices.azure.com/openai/deployments/text-embedding-3-small/embeddings?api-version=2024-02-15-preview
```

---

## 3️⃣ Azure Speech Service (East Asia)

**Purpose:** Used for pronunciation assessment, speech-to-text, text-to-speech

```
API_KEY: CbZ50wqN8vOc9BwwgUZak4sKkHqtUZSjj31bayNGIVaIn47214zRJQQJ99BJAC3pKaRXJ3w3AAAYACOGKoCE
REGION: eastasia
ENDPOINT: https://eastasia.api.cognitive.microsoft.com/
```

---

## 4️⃣ Qdrant Vector Database

**Purpose:** Vector storage for RAG (Retrieval-Augmented Generation)

```
QDRANT_URL: http://localhost:6333
QDRANT_COLLECTION: rag_biz_english
```

⚠️ **Note:** If Android connects to remote Qdrant, update URL accordingly. Currently set to localhost (server-side).

---

## 🔧 Android Implementation Checklist

### ✅ What Android MUST do:

1. **Chat Requests:**
   - Use Sweden Central endpoint
   - Use `gpt-35-turbo` deployment name (NOT model name in path)
   - Use API version: `2024-12-01-preview`
   - Set header: `api-key: DuQJzDcQmb9siNeUiiUsgaENRgewWHd9FLM4dJd0FJdQe9SAulRhJQQJ99BJACfhMk5XJ3w3AAAAACOGDSnb`

2. **Embedding Requests:**
   - Use UAE North endpoint (DIFFERENT from chat!)
   - Use `text-embedding-3-small` deployment name
   - Use API version: `2024-02-15-preview`
   - Set header: `api-key: 9fyw2LxxdqRgay7cAuK84FXP7TwWMm1HC2QOMy5u5oeKKVt8lyTdJQQJ99BJACF24PCXJ3w3AAAAACOGMrGx`

3. **Speech/Pronunciation:**
   - Use East Asia region
   - Use speech API key (different from OpenAI keys!)
   - Set header: `Ocp-Apim-Subscription-Key: CbZ50wqN8vOc9BwwgUZak4sKkHqtUZSjj31bayNGIVaIn47214zRJQQJ99BJAC3pKaRXJ3w3AAAYACOGKoCE`

---

## ⚠️ Common Mistakes to Avoid

### ❌ DON'T:
- Mix up chat and embedding endpoints (they're in different regions!)
- Use model names like `gpt-3.5-turbo` in the path - use deployment name `gpt-35-turbo`
- Use the same API key for all services (Speech has its own key)
- Hardcode `gpt-4` or generic model names - use exact deployment names

### ✅ DO:
- Use exact deployment names as shown above
- Use correct API version for each service
- Keep endpoints with trailing slashes where shown
- Test each endpoint separately to isolate issues

---

## 🧪 Testing Commands (for verification)

### Test Chat Endpoint:
```bash
curl -X POST "https://sanja-mh654t02-swedencentral.cognitiveservices.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-12-01-preview" \
  -H "api-key: DuQJzDcQmb9siNeUiiUsgaENRgewWHd9FLM4dJd0FJdQe9SAulRhJQQJ99BJACfhMk5XJ3w3AAAAACOGDSnb" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"max_tokens":10}'
```

### Test Embedding Endpoint:
```bash
curl -X POST "https://sanja-mh6697hv-uaenorth.cognitiveservices.azure.com/openai/deployments/text-embedding-3-small/embeddings?api-version=2024-02-15-preview" \
  -H "api-key: 9fyw2LxxdqRgay7cAuK84FXP7TwWMm1HC2QOMy5u5oeKKVt8lyTdJQQJ99BJACF24PCXJ3w3AAAAACOGMrGx" \
  -H "Content-Type: application/json" \
  -d '{"input":"test"}'
```

---

## 📋 Server Files Using Azure (for reference)

These server files have been configured to use Azure OpenAI:

1. **roleplay_engine.py** - Chat completions
2. **roleplay_referee.py** - Chat completions
3. **ingest.py** - Embeddings
4. **app.py** - Both chat and embeddings
5. **settings.py** - Configuration source

All use the pattern:
```python
if USE_AZURE:
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version=AZURE_OPENAI_API_VERSION
    )
    model = AZURE_OPENAI_CHAT_DEPLOYMENT
```

---

## 🔐 Security Notes

- These API keys are shown for internal development
- In production, use environment variables or secure key storage
- Never commit keys to public repositories
- Rotate keys periodically in Azure Portal

---

## 📞 Support

If Android side encounters errors, check:

1. **401 Unauthorized** → Wrong API key
2. **404 Not Found** → Wrong deployment name or endpoint
3. **400 Bad Request** → Wrong API version or malformed request
4. **Resource not found** → Deployment name doesn't exist in that region

**Quick Fix:** Copy-paste the exact values from sections 1️⃣, 2️⃣, and 3️⃣ above.

---

## 🎯 Summary Table

| Service | Region | Deployment Name | API Key (last 4 chars) |
|---------|--------|----------------|----------------------|
| Chat | Sweden Central | gpt-35-turbo | DSnb |
| Embeddings | UAE North | text-embedding-3-small | MrGx |
| Speech | East Asia | N/A | KoCE |

---

**End of Configuration Reference**

