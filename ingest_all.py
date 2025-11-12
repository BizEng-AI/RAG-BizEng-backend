"""
ingest_all.py - Ingest all books to Qdrant Cloud
Improved version that handles multiple books in one run
"""
import os
import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ingest import upsert_book, ensure_collection, USE_MOCK

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

def main():
    # Safety gate for paid runs
    if not USE_MOCK and os.getenv("CONFIRM_INGEST", "no").lower() != "yes":
        print("[ingest_all][ABORT] Set CONFIRM_INGEST=yes for real embeddings, or USE_MOCK=1", flush=True)
        print("[ingest_all] This will cost approximately $0.02 USD for all 3 books", flush=True)
        sys.exit(1)

    print("=" * 70)
    print("INGESTING ALL BOOKS TO QDRANT CLOUD")
    print("=" * 70)
    print()

    # Ensure collection exists
    ensure_collection()
    print()

    # Ingest each book
    for i, book in enumerate(BOOKS, 1):
        print(f"\n{'=' * 70}")
        print(f"BOOK {i}/{len(BOOKS)}: {book['name']}")
        print(f"Source: {book['path']}")
        print(f"ID: {book['source_id']}")
        print("=" * 70)
        print()

        # Check if file exists
        if not Path(book['path']).exists():
            print(f"[ingest_all][SKIP] File not found: {book['path']}", flush=True)
            continue

        # Ingest the book
        try:
            upsert_book(book['path'], source_id=book['source_id'])
            print(f"\n✅ Successfully ingested: {book['name']}", flush=True)
        except Exception as e:
            print(f"\n❌ Failed to ingest {book['name']}: {e}", flush=True)
            import traceback
            traceback.print_exc()
            # Continue with next book

        print()

    print("\n" + "=" * 70)
    print("INGESTION COMPLETE!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Verify: python setup_qdrant.py")
    print("2. Test search: curl 'http://localhost:8020/debug/search?q=business&k=5'")
    print("3. Start server: uvicorn app:app --host 0.0.0.0 --port 8020 --reload")
    print()

if __name__ == "__main__":
    main()

