"""
Verify actual book content vs ingested vectors
"""
from pathlib import Path
import sys
sys.path.insert(0, '.')

from ingest import chunk_text

books = [
    ('Book 1', 'C:/Users/sanja/rag-biz-english/data/book_1_ocr.txt'),
    ('Book 2', 'C:/Users/sanja/rag-biz-english/data/book_2_ocr.txt'),
    ('Book 3', 'C:/Users/sanja/rag-biz-english/data/book_3_ocr.txt'),
]

print('='*70)
print('DETAILED BOOK CONTENT ANALYSIS')
print('='*70)

total_expected = 0

for name, path in books:
    if not Path(path).exists():
        print(f'\n{name}: FILE NOT FOUND')
        continue
    
    # Read file
    text = Path(path).read_text(encoding='utf-8')
    file_size = Path(path).stat().st_size
    char_count = len(text)
    
    # Calculate chunks with the SAME parameters used in ingestion
    chunks = chunk_text(text, max_tokens=900, overlap=150)
    chunk_count = len(chunks)
    total_expected += chunk_count
    
    print(f'\n{name}:')
    print(f'  File: {path}')
    print(f'  File size: {file_size:,} bytes')
    print(f'  Characters: {char_count:,}')
    print(f'  Expected chunks: {chunk_count:,}')
    
    # Show sample of first chunk
    if chunks:
        print(f'  First chunk preview: {chunks[0][:100]}...')

print(f'\n{'='*70}')
print(f'TOTAL EXPECTED CHUNKS: {total_expected:,}')
print(f'{'='*70}')

# Compare with Qdrant
print('\nComparing with Qdrant...')
from qdrant_client import QdrantClient
from settings import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION

qdr = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=30)
collection = qdr.get_collection(QDRANT_COLLECTION)
actual_count = collection.points_count

print(f'  In Qdrant: {actual_count:,} vectors')
print(f'  Expected: {total_expected:,} chunks')

if actual_count == total_expected:
    print(f'\n✅ PERFECT MATCH! All content is ingested.')
elif actual_count < total_expected:
    missing = total_expected - actual_count
    percent = (actual_count / total_expected) * 100
    print(f'\n⚠️  INCOMPLETE: Missing {missing:,} vectors ({percent:.1f}% complete)')
    print(f'   → Need to ingest remaining content')
else:
    extra = actual_count - total_expected
    print(f'\n⚠️  UNEXPECTED: {extra:,} extra vectors')
    print(f'   → Possible duplicates or old data')

