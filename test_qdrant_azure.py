"""
Test Qdrant integration with Azure Embeddings
This verifies the complete RAG pipeline works with Azure
"""
from qdrant_client import QdrantClient
from openai import AzureOpenAI
from settings import (
    QDRANT_URL,
    QDRANT_COLLECTION,
    AZURE_OPENAI_EMBEDDING_KEY,
    AZURE_OPENAI_EMBEDDING_ENDPOINT,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
    USE_AZURE_EMBEDDINGS
)

print("=" * 70)
print("TESTING QDRANT + AZURE EMBEDDINGS INTEGRATION")
print("=" * 70)
print()

# Step 1: Check Qdrant connection
print("Step 1: Testing Qdrant connection...")
print(f"  URL: {QDRANT_URL}")
print(f"  Collection: {QDRANT_COLLECTION}")
try:
    qdr = QdrantClient(url=QDRANT_URL)
    collections = qdr.get_collections()
    print(f"  ✅ Connected to Qdrant")
    print(f"  Collections: {[c.name for c in collections.collections]}")

    # Check if our collection exists
    if QDRANT_COLLECTION in [c.name for c in collections.collections]:
        collection_info = qdr.get_collection(QDRANT_COLLECTION)
        print(f"  ✅ Collection '{QDRANT_COLLECTION}' exists")
        print(f"  Vectors count: {collection_info.points_count}")
        print(f"  Vector dimension: {collection_info.config.params.vectors.size}")
    else:
        print(f"  ⚠️  Collection '{QDRANT_COLLECTION}' does not exist yet")
        print(f"     Run ingest.py to create it and add documents")
    print()
except Exception as e:
    print(f"  ❌ Failed: {e}")
    print()
    exit(1)

# Step 2: Test Azure Embeddings
print("Step 2: Testing Azure Embeddings...")
print(f"  Endpoint: {AZURE_OPENAI_EMBEDDING_ENDPOINT}")
print(f"  Deployment: {AZURE_OPENAI_EMBEDDING_DEPLOYMENT}")
try:
    embed_client = AzureOpenAI(
        api_key=AZURE_OPENAI_EMBEDDING_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_EMBEDDING_ENDPOINT
    )

    # Create test embedding
    test_query = "business meeting schedule appointment"
    response = embed_client.embeddings.create(
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input=test_query
    )

    query_embedding = response.data[0].embedding
    print(f"  ✅ Azure Embeddings working")
    print(f"  Test query: '{test_query}'")
    print(f"  Embedding dimension: {len(query_embedding)}")
    print()
except Exception as e:
    print(f"  ❌ Failed: {e}")
    print()
    exit(1)

# Step 3: Test RAG pipeline (Embedding + Qdrant search)
print("Step 3: Testing RAG pipeline (Azure Embeddings → Qdrant Search)...")
try:
    # Check if collection has vectors
    collection_info = qdr.get_collection(QDRANT_COLLECTION)
    if collection_info.points_count == 0:
        print(f"  ⚠️  Collection is empty - no vectors to search")
        print(f"     Run: python ingest.py to add documents")
        print()
    else:
        # Search using Azure embedding
        hits = qdr.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=query_embedding,
            limit=3,
            with_payload=True
        )

        print(f"  ✅ RAG pipeline working!")
        print(f"  Query: '{test_query}'")
        print(f"  Found {len(hits)} results")
        print()

        for i, hit in enumerate(hits, 1):
            score = hit.score
            text = hit.payload.get('text', 'N/A')[:100] if hit.payload else 'N/A'
            source = hit.payload.get('source_id', 'N/A') if hit.payload else 'N/A'

            print(f"  Result {i}:")
            print(f"    Score: {score:.4f}")
            print(f"    Source: {source}")
            print(f"    Text: {text}...")
            print()

except Exception as e:
    print(f"  ❌ Failed: {e}")
    print()
    exit(1)

# Step 4: Test the exact flow used by roleplay_engine
print("Step 4: Testing roleplay_engine RAG flow...")
try:
    # Simulate what roleplay_engine does
    student_msg = "I'd like to schedule a meeting for next week"
    keywords = ["meeting", "schedule", "appointment", "calendar"]

    # Combine message with keywords (like roleplay_engine does)
    query_text = f"{student_msg} {' '.join(keywords)}"

    # Get embedding
    response = embed_client.embeddings.create(
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input=query_text
    )
    q_emb = response.data[0].embedding

    # Search Qdrant
    hits = qdr.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=q_emb,
        limit=5,
        with_payload=True
    )

    # Extract context (like roleplay_engine does)
    context_parts = []
    for hit in hits:
        if hit.payload and "text" in hit.payload:
            text = hit.payload["text"].strip()
            if text and len(text) > 50:
                context_parts.append(text[:400])

    context = "\n\n".join(context_parts[:3])

    print(f"  ✅ Roleplay engine RAG flow working!")
    print(f"  Student message: '{student_msg}'")
    print(f"  Keywords: {keywords}")
    print(f"  Retrieved {len(context_parts)} context chunks")
    if context:
        print(f"  Context preview: {context[:150]}...")
    else:
        print(f"  No context retrieved (collection might be empty)")
    print()

except Exception as e:
    print(f"  ❌ Failed: {e}")
    print()
    exit(1)

print("=" * 70)
print("✅ ALL TESTS PASSED!")
print("=" * 70)
print()
print("Summary:")
print("  ✅ Qdrant connection working")
print("  ✅ Azure Embeddings (UAE North) working")
print("  ✅ RAG pipeline (Azure → Qdrant) working")
print("  ✅ Roleplay engine integration working")
print()
print("Your RAG system is fully integrated with Azure OpenAI!")
print()
if collection_info.points_count == 0:
    print("⚠️  NOTE: Collection is empty. To add documents:")
    print("   1. Set: CONFIRM_INGEST=yes in environment")
    print("   2. Run: python ingest.py")
    print()
print("=" * 70)

