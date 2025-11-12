"""Check what's in the Qdrant collection"""
from qdrant_client import QdrantClient
from settings import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION

qdr = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Get collection info
info = qdr.get_collection(QDRANT_COLLECTION)
print(f"Collection: {QDRANT_COLLECTION}")
print(f"Total vectors: {info.points_count}")
print()

# Sample some points to see what sources we have
result = qdr.scroll(
    collection_name=QDRANT_COLLECTION,
    limit=100,
    with_payload=True
)

sources = {}
for point in result[0]:
    source_id = point.payload.get('source_id', 'unknown')
    sources[source_id] = sources.get(source_id, 0) + 1

print("Sources found:")
for source, count in sorted(sources.items()):
    print(f"  {source}: {count} vectors (sampled)")

print()
print("=" * 60)
if len(sources) == 1:
    print("⚠️  Only 1 book ingested!")
    print("To ingest all books, run: python ingest_all.py")
elif len(sources) == 3:
    print("✅ All 3 books ingested!")
else:
    print(f"📊 {len(sources)} book(s) ingested")

