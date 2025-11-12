"""
Simple Qdrant Cloud connection test
"""
from qdrant_client import QdrantClient

# Correct Qdrant Cloud endpoint (no port needed)
QDRANT_URL = "https://9963ec6f-613b-4fc2-84a7-cdcd7712fed8.eu-central-1-0.aws.cloud.qdrant.io"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.JqQKtcPaZgl-zLwfngmGn-f5oAzghkNtZP6Tv1EfHKY"

print(f"URL: {QDRANT_URL}")
print(f"Key: {QDRANT_API_KEY[:30]}...")
print("Connecting...")

try:
    qdr = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=10,
    )
    print("Client created")

    collections = qdr.get_collections()
    print(f"✅ SUCCESS! Collections: {[c.name for c in collections.collections]}")

except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")

