"""Complete check of ingestion status"""
from qdrant_client import QdrantClient
from settings import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION

qdr = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Get collection info
info = qdr.get_collection(QDRANT_COLLECTION)
print("=" * 70)
print("QDRANT CLOUD COLLECTION STATUS")
print("=" * 70)
print(f"Collection: {QDRANT_COLLECTION}")
print(f"Total vectors: {info.points_count}")
print(f"Vector dimension: {info.config.params.vectors.size}")
print(f"Distance metric: {info.config.params.vectors.distance}")
print()

# Count vectors by source (scroll through ALL points)
print("Counting vectors by source...")
sources = {}
offset = None

while True:
    result = qdr.scroll(
        collection_name=QDRANT_COLLECTION,
        limit=100,
        with_payload=True,
        offset=offset
    )

    points, offset = result

    if not points:
        break

    for point in points:
        source_id = point.payload.get('source_id', 'unknown')
        sources[source_id] = sources.get(source_id, 0) + 1

    if offset is None:
        break

print()
print("=" * 70)
print("VECTORS BY SOURCE")
print("=" * 70)
total = 0
for source, count in sorted(sources.items()):
    print(f"  {source:20s}: {count:4d} vectors")
    total += count

print(f"  {'TOTAL':20s}: {total:4d} vectors")
print()

# Expected counts
expected = {
    "book_1_ocr": 1200,
    "book_2_ocr": 400,
    "book_3_ocr": 2000
}

print("=" * 70)
print("INGESTION STATUS")
print("=" * 70)

all_complete = True
for book, expected_count in expected.items():
    actual = sources.get(book, 0)
    if actual == 0:
        status = "❌ NOT INGESTED"
        all_complete = False
    elif actual < expected_count * 0.5:
        status = f"⚠️  PARTIAL ({actual}/{expected_count} expected)"
        all_complete = False
    else:
        status = "✅ COMPLETE"

    print(f"  {book:20s}: {status}")

print()
if all_complete:
    print("🎉 All books fully ingested!")
else:
    print("⚠️  Some books are missing or incomplete")
    print()
    print("To ingest all books:")
    print("  1. Set CONFIRM_INGEST=yes in environment")
    print("  2. Run: python ingest_all.py")
print()
print("=" * 70)

