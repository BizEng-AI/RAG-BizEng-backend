"""
Setup Qdrant Cloud collection
Creates the 'bizeng' collection if it doesn't exist
"""
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "bizeng")

print(f"Connecting to: {QDRANT_URL}")
print(f"Collection: {QDRANT_COLLECTION}")
print()

try:
    # Initialize client
    qdr = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=30,
    )

    # Check existing collections
    collections = qdr.get_collections()
    collection_names = [c.name for c in collections.collections]

    print(f"✅ Connected! Found {len(collection_names)} collections:")
    for name in collection_names:
        print(f"  - {name}")
    print()

    # Check if our collection exists
    if QDRANT_COLLECTION in collection_names:
        print(f"✅ Collection '{QDRANT_COLLECTION}' already exists")
        info = qdr.get_collection(QDRANT_COLLECTION)
        print(f"   Vector size: {info.config.params.vectors.size}")
        print(f"   Distance: {info.config.params.vectors.distance}")
        print(f"   Points: {info.points_count}")
    else:
        print(f"⚠️  Collection '{QDRANT_COLLECTION}' does NOT exist")
        print(f"Creating collection '{QDRANT_COLLECTION}'...")

        qdr.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=1536,  # text-embedding-3-small dimension
                distance=Distance.COSINE
            )
        )

        print(f"✅ Collection '{QDRANT_COLLECTION}' created!")
        print("   Vector size: 1536")
        print("   Distance: COSINE")
        print("   Points: 0")

    print()
    print("=" * 60)
    print("🎉 Setup complete! Your Qdrant Cloud is ready!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Run 'python ingest.py' to upload your documents")
    print("2. Start server: 'uvicorn app:app --host 0.0.0.0 --port 8020 --reload'")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

