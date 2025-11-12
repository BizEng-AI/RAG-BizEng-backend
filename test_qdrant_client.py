"""
Test Qdrant Cloud connection using the official client
"""
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

QDRANT_URL = "https://bizeng-cluster-3f7c04d8-1cbf-4c2b-8cd7-f6b7b3e75b0c.eu-central-1-0.aws.cloud.qdrant.io:6333"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.JqQKtcPaZgl-zLwfngmGn-f5oAzghkNtZP6Tv1EfHKY"
COLLECTION_NAME = "bizeng"

print(f"Testing connection to: {QDRANT_URL}")
print(f"Using API key: {QDRANT_API_KEY[:20]}...")
print()

try:
    # Initialize client
    qdr = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        prefer_grpc=False,  # Use HTTP
        timeout=30,
    )

    print("✅ Client initialized")
    print(f"Effective URL: {qdr._client.rest_uri if hasattr(qdr, '_client') else 'N/A'}")
    print()

    # Test 1: Get collections
    print("Test 1: Listing collections...")
    collections = qdr.get_collections()
    print(f"✅ SUCCESS! Found {len(collections.collections)} collections")
    for coll in collections.collections:
        print(f"  - {coll.name}")
    print()

    # Test 2: Check if our collection exists
    print(f"Test 2: Checking for collection '{COLLECTION_NAME}'...")
    collection_names = [c.name for c in collections.collections]

    if COLLECTION_NAME in collection_names:
        print(f"✅ Collection '{COLLECTION_NAME}' exists")
        info = qdr.get_collection(COLLECTION_NAME)
        print(f"   Vector size: {info.config.params.vectors.size}")
        print(f"   Vector distance: {info.config.params.vectors.distance}")
        print(f"   Points count: {info.points_count}")
    else:
        print(f"⚠️  Collection '{COLLECTION_NAME}' does NOT exist")
        print(f"   Creating collection '{COLLECTION_NAME}'...")
        qdr.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )
        print(f"✅ Collection '{COLLECTION_NAME}' created!")

    print()
    print("=" * 60)
    print("🎉 ALL TESTS PASSED! Connection is working!")
    print("=" * 60)

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

