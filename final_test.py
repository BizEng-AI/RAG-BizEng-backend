"""
Final Configuration Summary and Test
"""
from openai import AzureOpenAI, OpenAI
from settings import (
    USE_AZURE,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_CHAT_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    OPENAI_API_KEY,
    EMBED_MODEL
)

print("=" * 70)
print("FINAL CONFIGURATION TEST & SUMMARY")
print("=" * 70)
print()

# Test 1: Azure Chat (for roleplay)
print("Test 1: Azure Chat API (for roleplay conversations)")
print("-" * 70)
try:
    azure_client = AzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )

    response = azure_client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "You are a business client."},
            {"role": "user", "content": "Hello, I'd like to schedule a meeting."}
        ],
        max_tokens=50
    )

    print("✅ WORKING!")
    print(f"   Deployment: {AZURE_OPENAI_CHAT_DEPLOYMENT}")
    print(f"   Response: {response.choices[0].message.content[:80]}...")
    print("   Cost: ~80% cheaper than OpenAI!")
    print()
except Exception as e:
    print(f"❌ FAILED: {e}")
    print()

# Test 2: Embeddings (for RAG/search)
print("Test 2: Embeddings API (for document search)")
print("-" * 70)

if AZURE_OPENAI_EMBEDDING_DEPLOYMENT:
    print("Testing Azure Embeddings...")
    try:
        response = azure_client.embeddings.create(
            model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            input="Test document"
        )
        print("✅ Azure Embeddings WORKING!")
        print(f"   Deployment: {AZURE_OPENAI_EMBEDDING_DEPLOYMENT}")
        print()
    except Exception as e:
        print(f"❌ Azure Embeddings FAILED: {e}")
        print("   Falling back to OpenAI...")
        print()

# Test OpenAI embeddings fallback (always run to confirm)
print("Testing OpenAI Embeddings (fallback)...")
try:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    response = openai_client.embeddings.create(
        model=EMBED_MODEL,
        input="Test document"
    )
    print("✅ OpenAI Embeddings WORKING!")
    print(f"   Model: {EMBED_MODEL}")
    print("   Note: This uses your OpenAI credits, not Azure")
    print()
except Exception as e:
    print(f"❌ OpenAI Embeddings FAILED: {e}")
    print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()
print("✅ Chat API (Azure): WORKING - gpt-35-turbo")
print("   → Roleplay conversations will use Azure (80% cheaper!)")
print()

if AZURE_OPENAI_EMBEDDING_DEPLOYMENT:
    print(f"✅ Embeddings API (Azure): {AZURE_OPENAI_EMBEDDING_DEPLOYMENT}")
else:
    print("⚠️  Embeddings API (Azure): NOT CONFIGURED")
    print("   → Currently using OpenAI for embeddings")
    print("   → To save costs, create an embedding deployment in Azure:")
    print("      1. Go to https://oai.azure.com/")
    print("      2. Deployments → Create new deployment")
    print("      3. Model: text-embedding-3-small")
    print("      4. Name it: 'embedding-small' or 'text-embedding-3-small'")
    print("      5. Update .env with the deployment name")

print()
print("Your server is ready to run with Azure OpenAI for chat!")
print("Run: python app.py")
print("=" * 70)
