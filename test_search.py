"""
Direct test of Qdrant search to diagnose why retrieval isn't working.
"""
from qdrant_client import QdrantClient
from qdrant_client.models import SearchParams
from openai import OpenAI, AzureOpenAI
from settings import (
    QDRANT_URL,
    QDRANT_COLLECTION,
    OPENAI_API_KEY,
    EMBED_MODEL,
    USE_AZURE,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT
)

print(f"[test] Connecting to Qdrant at {QDRANT_URL}")
print(f"[test] Collection: {QDRANT_COLLECTION}")

# Initialize OpenAI client (Azure or regular OpenAI)
if USE_AZURE:
    oai = AzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    embed_model = AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    print(f"[test] Using Azure OpenAI - Embed deployment: {embed_model}")
else:
    oai = OpenAI(api_key=OPENAI_API_KEY)
    embed_model = EMBED_MODEL
    print(f"[test] Using OpenAI - Embed model: {embed_model}")

qdr = QdrantClient(url=QDRANT_URL)

# Check collection info
info = qdr.get_collection(QDRANT_COLLECTION)
print(f"[test] Collection vectors count: {info.points_count}")
print(f"[test] Collection vector size: {info.config.params.vectors.size}")

# Test queries
test_queries = [
    "how to write a business email",
    "what is employment law",
    "business communication skills",
    "colleagues and teamwork"
]

for query in test_queries:
    print(f"\n{'='*60}")
    print(f"[test] Query: '{query}'")
    
    # Embed the query
    print("[test] Embedding query...")
    q_emb = oai.embeddings.create(model=embed_model, input=query).data[0].embedding
    print(f"[test] Embedding dim: {len(q_emb)}")
    
    # Search Qdrant
    print("[test] Searching Qdrant...")
    hits = qdr.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=q_emb,
        limit=5,
        with_payload=True,
        search_params=SearchParams(hnsw_ef=128, exact=False),
    )
    
    print(f"[test] Found {len(hits)} hits")
    
    if not hits:
        print("[test] ❌ NO RESULTS - This is the problem!")
        
        # Try with exact search
        print("[test] Trying exact search...")
        hits_exact = qdr.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=q_emb,
            limit=5,
            with_payload=True,
            search_params=SearchParams(exact=True),
        )
        print(f"[test] Exact search found {len(hits_exact)} hits")
        
    else:
        print("[test] ✓ Got results!")
        for i, h in enumerate(hits, 1):
            text_snippet = (h.payload.get("text", "")[:150]).replace("\n", " ")
            print(f"  {i}. score={h.score:.4f} | {text_snippet}...")

print(f"\n{'='*60}")
print("[test] Done")
