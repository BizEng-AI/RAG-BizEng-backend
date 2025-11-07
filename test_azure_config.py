"""
Test script to verify Azure OpenAI configuration
Tests both chat and embedding endpoints
"""
import sys
from openai import AzureOpenAI
from settings import (
    USE_AZURE,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_CHAT_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
)

print("=" * 70)
print("AZURE OPENAI CONFIGURATION TEST")
print("=" * 70)
print()

# Step 1: Check configuration
print("Step 1: Checking configuration...")
print(f"  USE_AZURE: {USE_AZURE}")
print(f"  Endpoint: {AZURE_OPENAI_ENDPOINT}")
print(f"  API Version: {AZURE_OPENAI_API_VERSION}")
print(f"  Chat Deployment: {AZURE_OPENAI_CHAT_DEPLOYMENT}")
print(f"  Embedding Deployment: {AZURE_OPENAI_EMBEDDING_DEPLOYMENT}")
print(f"  API Key: {'*' * 20}{AZURE_OPENAI_KEY[-10:] if AZURE_OPENAI_KEY else 'NOT SET'}")
print()

if not USE_AZURE:
    print("❌ Azure is not enabled (USE_AZURE=False)")
    print("   Check your .env file configuration")
    sys.exit(1)

if not AZURE_OPENAI_KEY or not AZURE_OPENAI_ENDPOINT:
    print("❌ Missing Azure credentials")
    sys.exit(1)

print("✅ Configuration looks good")
print()

# Step 2: Initialize client
print("Step 2: Initializing Azure OpenAI client...")
try:
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    print("✅ Client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize client: {e}")
    sys.exit(1)
print()

# Step 3: Test Chat Completion endpoint
print("Step 3: Testing Chat Completion endpoint...")
print(f"  Deployment: {AZURE_OPENAI_CHAT_DEPLOYMENT}")
try:
    response = client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, Azure!' if you can hear me."}
        ],
        max_tokens=50,
        temperature=0.7
    )

    message = response.choices[0].message.content
    print(f"✅ Chat endpoint working!")
    print(f"  Response: {message}")
    print(f"  Model: {response.model}")
    print(f"  Tokens used: {response.usage.total_tokens}")
except Exception as e:
    print(f"❌ Chat endpoint failed: {e}")
    print(f"   Error type: {type(e).__name__}")
    if hasattr(e, 'status_code'):
        print(f"   Status code: {e.status_code}")
    sys.exit(1)
print()

# Step 4: Test Embeddings endpoint
print("Step 4: Testing Embeddings endpoint...")
print(f"  Deployment: {AZURE_OPENAI_EMBEDDING_DEPLOYMENT}")
try:
    response = client.embeddings.create(
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input="This is a test sentence for embeddings."
    )

    embedding = response.data[0].embedding
    print(f"✅ Embeddings endpoint working!")
    print(f"  Embedding dimension: {len(embedding)}")
    print(f"  Model: {response.model}")
    print(f"  First 5 values: {embedding[:5]}")
    print(f"  Tokens used: {response.usage.total_tokens}")
except Exception as e:
    print(f"❌ Embeddings endpoint failed: {e}")
    print(f"   Error type: {type(e).__name__}")
    if hasattr(e, 'status_code'):
        print(f"   Status code: {e.status_code}")
    sys.exit(1)
print()

# Step 5: Test batch embeddings (like ingest.py uses)
print("Step 5: Testing batch embeddings (multiple texts)...")
try:
    test_texts = [
        "First business document.",
        "Second business document.",
        "Third business document."
    ]
    response = client.embeddings.create(
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input=test_texts
    )

    print(f"✅ Batch embeddings working!")
    print(f"  Processed {len(response.data)} texts")
    print(f"  Total tokens used: {response.usage.total_tokens}")
except Exception as e:
    print(f"❌ Batch embeddings failed: {e}")
    sys.exit(1)
print()

# Step 6: Test roleplay-style chat (like your app uses)
print("Step 6: Testing roleplay-style chat...")
try:
    response = client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "You are a business client in a roleplay scenario. Respond professionally."},
            {"role": "user", "content": "Hello, I'd like to discuss our project timeline."}
        ],
        max_tokens=100,
        temperature=0.8
    )

    message = response.choices[0].message.content
    print(f"✅ Roleplay chat working!")
    print(f"  Response: {message[:100]}...")
    print(f"  Tokens used: {response.usage.total_tokens}")
except Exception as e:
    print(f"❌ Roleplay chat failed: {e}")
    sys.exit(1)
print()

# Summary
print("=" * 70)
print("✅ ALL TESTS PASSED!")
print("=" * 70)
print()
print("Your Azure OpenAI configuration is working correctly:")
print(f"  ✅ Chat API ({AZURE_OPENAI_CHAT_DEPLOYMENT})")
print(f"  ✅ Embeddings API ({AZURE_OPENAI_EMBEDDING_DEPLOYMENT})")
print(f"  ✅ Batch processing")
print(f"  ✅ Roleplay scenarios")
print()
print("You can now safely run your server with Azure OpenAI!")
print()

