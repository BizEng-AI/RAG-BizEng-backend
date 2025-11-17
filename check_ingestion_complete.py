"""
Check current ingestion status in Qdrant Cloud
"""
import os
from pathlib import Path
import sys

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent))

from qdrant_client import QdrantClient
from settings import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION

print("="*70)
print("CHECKING QDRANT INGESTION STATUS")
print("="*70)

# Connect to Qdrant Cloud
qdr = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=30,
)

print(f"\nConnected to: {QDRANT_URL}")
print(f"Collection: {QDRANT_COLLECTION}")

try:
    # Get collection info
    collection = qdr.get_collection(QDRANT_COLLECTION)
    total_vectors = collection.points_count

    print(f"\n✓ Collection exists")
    print(f"  Total vectors: {total_vectors:,}")
    print(f"  Vector dimension: {collection.config.params.vectors.size}")

    # Count vectors per source
    sources = ["book_1_ocr", "book_2_ocr", "book_3_ocr"]

    print("\nVectors per source:")
    for source in sources:
        result = qdr.count(
            collection_name=QDRANT_COLLECTION,
            count_filter={
                "must": [
                    {
                        "key": "source_id",
                        "match": {"value": source}
                    }
                ]
            }
        )
        count = result.count
        print(f"  {source}: {count:,} vectors")

    # Estimate book sizes
    print("\nEstimated book ingestion:")
    book_paths = [
        ("Book 1", "C:/Users/sanja/rag-biz-english/data/book_1_ocr.txt"),
        ("Book 2", "C:/Users/sanja/rag-biz-english/data/book_2_ocr.txt"),
        ("Book 3", "C:/Users/sanja/rag-biz-english/data/book_3_ocr.txt"),
    ]

    for name, path in book_paths:
        if Path(path).exists():
            size = Path(path).stat().st_size
            # Rough estimate: ~900 tokens per chunk, ~4 chars per token = 3600 chars per chunk
            estimated_chunks = size // 3600
            print(f"  {name}: ~{estimated_chunks:,} chunks expected ({size:,} bytes)")
        else:
            print(f"  {name}: FILE NOT FOUND")

    # Sample a few vectors
    print("\nSample vectors:")
    results = qdr.scroll(
        collection_name=QDRANT_COLLECTION,
        limit=3,
        with_payload=True,
        with_vectors=False
    )

    for i, point in enumerate(results[0], 1):
        text = point.payload.get('text', '')[:100]
        source = point.payload.get('source_id', 'unknown')
        print(f"  {i}. [{source}] {text}...")

    # Check if ingestion is complete
    print("\n" + "="*70)
    if total_vectors < 100:
        print("⚠️  WARNING: Very few vectors ingested!")
        print("   Expected: 500-1500 vectors for 3 books")
        print("   Current: Only", total_vectors, "vectors")
        print("\n   → Need to run full ingestion!")
    elif total_vectors < 500:
        print("⚠️  WARNING: Ingestion may be incomplete")
        print("   Expected: 500-1500 vectors for 3 books")
        print("   Current:", total_vectors, "vectors")
        print("\n   → Some books may be missing")
    else:
        print("✓ Ingestion appears complete")
        print(f"  {total_vectors:,} vectors is reasonable for 3 books")

    print("="*70)

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

