"""
Complete Book Ingestion Script with Verification
Ensures 100% of all 3 books are ingested
"""
import os
import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent))

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, FieldCondition, MatchValue, Filter
from settings import *
from ingest import chunk_text, embed_texts, clean_ocr_text
import uuid

print("="*70)
print("COMPLETE BOOK INGESTION - 100% VERIFICATION")
print("="*70)

# Connect to Qdrant
qdr = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=60,  # Longer timeout for large operations
)

# Books to ingest
BOOKS = [
    {
        "path": "C:/Users/sanja/rag-biz-english/data/book_1_ocr.txt",
        "source_id": "book_1_ocr",
        "name": "Business English Book 1"
    },
    {
        "path": "C:/Users/sanja/rag-biz-english/data/book_2_ocr.txt",
        "source_id": "book_2_ocr",
        "name": "Business English Book 2"
    },
    {
        "path": "C:/Users/sanja/rag-biz-english/data/book_3_ocr.txt",
        "source_id": "book_3_ocr",
        "name": "Business English Book 3"
    }
]

def count_book_vectors(source_id: str) -> int:
    """Count vectors for a specific source_id using scroll (doesn't require index)"""
    try:
        count = 0
        offset = None
        while True:
            results, offset = qdr.scroll(
                collection_name=QDRANT_COLLECTION,
                scroll_filter=Filter(
                    must=[FieldCondition(key="source_id", match=MatchValue(value=source_id))]
                ),
                limit=100,
                offset=offset,
                with_payload=False,
                with_vectors=False
            )
            count += len(results)
            if offset is None:
                break
        return count
    except Exception as e:
        print(f"  Error counting {source_id}: {e}")
        return -1

def ensure_collection_with_index():
    """Ensure collection exists with proper index on source_id"""
    dim = 1536  # text-embedding-3-small dimension

    if not qdr.collection_exists(QDRANT_COLLECTION):
        print(f"\n✓ Creating collection '{QDRANT_COLLECTION}'...")
        qdr.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            hnsw_config={"m": 16, "ef_construct": 128}
        )
    else:
        print(f"\n✓ Collection '{QDRANT_COLLECTION}' exists")

    # Create index on source_id for faster filtering
    try:
        qdr.create_payload_index(
            collection_name=QDRANT_COLLECTION,
            field_name="source_id",
            field_schema="keyword"
        )
        print("✓ Created index on source_id")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("✓ Index on source_id already exists")
        else:
            print(f"  Warning: Could not create index: {e}")

def check_book_status():
    """Check current ingestion status"""
    print("\n" + "="*70)
    print("CURRENT STATUS")
    print("="*70)

    collection = qdr.get_collection(QDRANT_COLLECTION)
    total_vectors = collection.points_count
    print(f"\nTotal vectors in collection: {total_vectors:,}")

    print("\nChecking each book...")
    book_status = []

    for book in BOOKS:
        if not Path(book['path']).exists():
            print(f"\n✗ {book['name']}: FILE NOT FOUND at {book['path']}")
            book_status.append({'book': book, 'status': 'missing_file', 'current': 0, 'expected': 0})
            continue

        # Count current vectors
        print(f"\n{book['name']}:")
        print(f"  Path: {book['path']}")
        current_count = count_book_vectors(book['source_id'])
        print(f"  Current vectors: {current_count:,}")

        # Calculate expected vectors
        text = Path(book['path']).read_text(encoding='utf-8')
        chunks = chunk_text(text, max_tokens=900, overlap=150)
        expected_count = len(chunks)
        print(f"  Expected vectors: {expected_count:,}")

        # Determine status
        if current_count == expected_count:
            print(f"  ✓ COMPLETE (100%)")
            status = 'complete'
        elif current_count > 0:
            percent = (current_count / expected_count) * 100
            print(f"  ⚠️  INCOMPLETE ({percent:.1f}%)")
            status = 'incomplete'
        else:
            print(f"  ✗ NOT INGESTED (0%)")
            status = 'not_ingested'

        book_status.append({
            'book': book,
            'status': status,
            'current': current_count,
            'expected': expected_count
        })

    return book_status

def ingest_book(book_info, force=False):
    """Ingest a single book"""
    book = book_info['book']

    print(f"\n{'='*70}")
    print(f"INGESTING: {book['name']}")
    print(f"{'='*70}")

    # Check if already complete
    if not force and book_info['status'] == 'complete':
        print(f"✓ Book already fully ingested ({book_info['current']} vectors)")
        print("  Use force=True to re-ingest")
        return True

    # Read and chunk the book
    path = Path(book['path'])
    print(f"\n1. Reading: {path}")
    text = path.read_text(encoding='utf-8')
    print(f"   File size: {len(text):,} characters")

    print(f"\n2. Chunking text...")
    chunks = chunk_text(text, max_tokens=900, overlap=150)
    print(f"   Total chunks: {len(chunks):,}")

    # Generate embeddings in batches
    print(f"\n3. Generating embeddings...")
    print(f"   Using: Azure text-embedding-3-small")
    print(f"   Batch size: 64")

    vectors = []
    BATCH_SIZE = 64

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"   Batch {batch_num}/{total_batches} ({i+1}-{i+len(batch)}/{len(chunks)})", flush=True)

        try:
            batch_vectors = embed_texts(batch)
            vectors.extend(batch_vectors)
        except Exception as e:
            print(f"   ✗ Error in batch {batch_num}: {e}")
            raise

    print(f"   ✓ Generated {len(vectors):,} embeddings")

    # Create points
    print(f"\n4. Creating Qdrant points...")
    points = []
    for vec, chunk in zip(vectors, chunks):
        clean_chunk = clean_ocr_text(chunk)
        payload = {
            "text": clean_chunk,
            "source_id": book['source_id']
        }
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload=payload
        ))

    print(f"   ✓ Created {len(points):,} points")

    # Upsert to Qdrant
    print(f"\n5. Uploading to Qdrant Cloud...")
    try:
        qdr.upsert(
            collection_name=QDRANT_COLLECTION,
            points=points,
            wait=True  # Wait for operation to complete
        )
        print(f"   ✓ Successfully uploaded {len(points):,} vectors")
    except Exception as e:
        print(f"   ✗ Upload failed: {e}")
        raise

    # Verify
    print(f"\n6. Verifying upload...")
    actual_count = count_book_vectors(book['source_id'])
    print(f"   Vectors in Qdrant: {actual_count:,}")

    if actual_count >= len(chunks):
        print(f"   ✓ VERIFICATION PASSED")
        return True
    else:
        print(f"   ✗ VERIFICATION FAILED: Expected {len(chunks)}, got {actual_count}")
        return False

def main():
    # Safety check
    if os.getenv("CONFIRM_FULL_INGEST") != "yes":
        print("\n⚠️  WARNING: This will ingest/re-ingest all books")
        print("   Cost: ~$0.02 USD for embeddings")
        print("   Time: ~5-10 minutes")
        print("\n   Set CONFIRM_FULL_INGEST=yes to proceed")
        sys.exit(1)

    # Setup
    print("\nStep 1: Ensuring collection and indexes...")
    ensure_collection_with_index()

    # Check status
    print("\nStep 2: Checking current status...")
    book_status = check_book_status()

    # Determine what needs ingesting
    print("\n" + "="*70)
    print("INGESTION PLAN")
    print("="*70)

    to_ingest = []
    for info in book_status:
        if info['status'] == 'missing_file':
            print(f"✗ {info['book']['name']}: SKIP (file not found)")
        elif info['status'] == 'complete':
            print(f"✓ {info['book']['name']}: OK (already complete)")
        elif info['status'] == 'incomplete':
            print(f"⚠️  {info['book']['name']}: NEEDS COMPLETION ({info['current']}/{info['expected']} vectors)")
            to_ingest.append(info)
        else:  # not_ingested
            print(f"✗ {info['book']['name']}: NEEDS INGESTION (0/{info['expected']} vectors)")
            to_ingest.append(info)

    if not to_ingest:
        print("\n✓ All books are fully ingested!")
        print(f"\nTotal vectors: {sum(info['current'] for info in book_status):,}")
        return

    # Ingest missing/incomplete books
    print(f"\n{len(to_ingest)} book(s) need ingestion...")
    print("\nProceeding in 3 seconds...")
    import time
    time.sleep(3)

    for info in to_ingest:
        try:
            success = ingest_book(info, force=True)
            if not success:
                print(f"\n✗ Failed to ingest {info['book']['name']}")
        except Exception as e:
            print(f"\n✗ Error ingesting {info['book']['name']}: {e}")
            import traceback
            traceback.print_exc()

    # Final verification
    print("\n" + "="*70)
    print("FINAL VERIFICATION")
    print("="*70)

    book_status_final = check_book_status()

    all_complete = all(info['status'] == 'complete' for info in book_status_final if info['status'] != 'missing_file')

    if all_complete:
        print("\n" + "="*70)
        print("✓✓✓ SUCCESS! ALL BOOKS 100% INGESTED! ✓✓✓")
        print("="*70)
        total_vectors = sum(info['current'] for info in book_status_final)
        print(f"\nTotal vectors: {total_vectors:,}")
    else:
        print("\n" + "="*70)
        print("⚠️  WARNING: Some books are still incomplete")
        print("="*70)

if __name__ == "__main__":
    main()

