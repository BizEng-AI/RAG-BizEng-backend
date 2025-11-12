# 📥 INGESTION GUIDE - Upload Documents to Qdrant Cloud

**Date:** November 10, 2025  
**Status:** Ready to ingest to Qdrant Cloud (empty collection)

---

## 📊 Current Status

### Qdrant Cloud Collection
- **Name:** `bizeng`
- **Vectors:** 0 (EMPTY - needs ingestion)
- **Dimension:** 1536 (text-embedding-3-small)
- **Distance:** COSINE
- **Cluster:** https://9963ec6f-613b-4fc2-84a7-cdcd7712fed8.eu-central-1-0.aws.cloud.qdrant.io

### Available Documents
```
C:\Users\sanja\rag-biz-english\data\
├── book_1_ocr.txt (538 KB)
├── book_2_ocr.txt (207 KB)
└── book_3_ocr.txt (1.05 MB)
```

**Total:** ~1.8 MB of text data

---

## ⚠️ IMPORTANT: Cost Considerations

### Azure OpenAI Embeddings Pricing
- **Model:** text-embedding-3-small
- **Cost:** ~$0.00002 per 1,000 tokens
- **Estimated tokens:** ~450,000 tokens (1.8 MB text)
- **Estimated cost:** ~$0.01 (1 cent)

### Qdrant Cloud
- **Free tier:** Up to 1GB storage
- **Your usage:** ~700 KB vectors (well within free tier)

**Total estimated cost:** < $0.02 USD

---

## 🚀 STEP-BY-STEP INGESTION

### Step 1: Verify Environment
```bash
cd C:\Users\sanja\rag-biz-english\server

# Check connection to Qdrant Cloud
python setup_qdrant.py
# Should show: Points: 0
```

### Step 2: Set Confirmation Environment Variable
```bash
# PowerShell
$env:CONFIRM_INGEST="yes"

# Or add to .env file:
echo CONFIRM_INGEST=yes >> .env
```

This prevents accidental ingestion costs.

### Step 3: Run Ingestion (One Book at a Time)

The current `ingest.py` is hardcoded to ingest only `book_1_ocr.txt`. Let me create an improved version.

---

## 🔧 IMPROVED INGESTION SCRIPT

I'll create `ingest_all.py` that handles all three books:

---

## 📝 INGESTION PROCESS

### What Happens During Ingestion:

1. **Read text file** (book_1_ocr.txt)
2. **Detect units** (e.g., "Unit 1", "Unit 2")
3. **Chunk text** (500-char chunks with overlap)
4. **Generate embeddings** (Azure UAE North)
   - Batch size: 64 chunks at a time
   - Rate limited to avoid throttling
5. **Upload to Qdrant Cloud**
   - Each chunk becomes a vector point
   - Metadata: source_id, unit, text snippet

### Expected Output:
```
[ingest] starting…
[ingest] Using Azure Embeddings - Deployment: text-embedding-3-small
[ingest] reading: book_1_ocr.txt
[ingest] total_chunks=1200  using=1200
[ingest] embedding batch 1-64 / 1200
[ingest] upserting 64 points…
[ingest] embedding batch 65-128 / 1200
...
[ingest] ✅ Complete! Uploaded 1200 vectors
```

### Time Estimate:
- **Book 1:** ~3-5 minutes (1200 chunks)
- **Book 2:** ~1-2 minutes (400 chunks)
- **Book 3:** ~5-7 minutes (2000 chunks)
- **Total:** ~10-15 minutes

---

## 🎯 QUICK START (Use Current Script)

### Ingest Book 1 Only:
```bash
cd C:\Users\sanja\rag-biz-english\server

# Set confirmation
$env:CONFIRM_INGEST="yes"

# Run ingestion
python ingest.py
```

This will:
- Connect to Qdrant Cloud
- Read `book_1_ocr.txt`
- Generate embeddings via Azure (UAE North)
- Upload ~1200 vectors
- Cost: < $0.01

### Verify Ingestion:
```bash
# Check collection stats
python setup_qdrant.py
# Should show: Points: ~1200

# Test search
python -c "
from qdrant_client import QdrantClient
from settings import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION
qdr = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
info = qdr.get_collection(QDRANT_COLLECTION)
print(f'✅ Collection has {info.points_count} vectors')
"
```

---

## 🔄 INGEST ADDITIONAL BOOKS

To ingest books 2 and 3, you need to modify `ingest.py`:

### Option 1: Manual Edit
Edit `ingest.py` line 159:
```python
# Change from:
upsert_book("C:/Users/sanja/rag-biz-english/data/book_1_ocr.txt", source_id="book_1_ocr")

# To:
upsert_book("C:/Users/sanja/rag-biz-english/data/book_2_ocr.txt", source_id="book_2_ocr")
```

Then run:
```bash
python ingest.py
```

Repeat for book 3.

### Option 2: Use Improved Script
I can create `ingest_all.py` that does all three in one run. Want me to create that?

---

## 🧪 TEST AFTER INGESTION

### 1. Check Collection Size
```bash
python setup_qdrant.py
```

### 2. Test Search via API
```bash
# Start server
uvicorn app:app --host 0.0.0.0 --port 8020 --reload

# In another terminal:
curl "http://localhost:8020/debug/search?q=business+meeting&k=5"
```

Expected: Should return relevant chunks about business meetings.

### 3. Test RAG Chat
```bash
curl -X POST http://localhost:8020/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"What are the stages of a business meeting?","k":5}'
```

Expected: Should return answer with sources.

### 4. Test Roleplay (uses RAG)
```bash
curl -X POST http://localhost:8020/roleplay/start \
  -H "Content-Type: application/json" \
  -d '{"scenario_id":"job_interview","student_name":"Test","use_rag":true}'
```

---

## 🗑️ DELETE AND RE-INGEST

If you need to delete and re-ingest:

### Delete Specific Book:
```bash
python ingest.py delete book_1_ocr
```

### Delete All (Recreate Collection):
```bash
python -c "
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from settings import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION

qdr = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
qdr.recreate_collection(
    collection_name=QDRANT_COLLECTION,
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)
print('✅ Collection recreated (empty)')
"
```

Then re-run ingestion.

---

## ⚠️ TROUBLESHOOTING

### "CONFIRM_INGEST=yes" Required
**Error:** `[ingest][ABORT] Set CONFIRM_INGEST=yes for real embeddings`

**Solution:**
```bash
$env:CONFIRM_INGEST="yes"
python ingest.py
```

### Azure Rate Limiting
**Error:** `RateLimitError: Too many requests`

**Solution:** Script already has rate limiting. If it persists:
- Reduce `BATCH` size: `$env:BATCH="32"`
- Add delay between batches

### Connection Timeout
**Error:** `TimeoutError` or `Connection refused`

**Solution:**
```bash
# Verify Qdrant connection
python test_quick.py

# Check Azure credentials
python -c "from settings import AZURE_OPENAI_EMBEDDING_KEY; print(AZURE_OPENAI_EMBEDDING_KEY[:20])"
```

### Wrong Vector Dimension
**Error:** `Vector dimension mismatch`

**Solution:** Recreate collection with correct dimension (1536 for text-embedding-3-small)

---

## 📊 EXPECTED FINAL STATE

After ingesting all 3 books:

```
Collection: bizeng
├── book_1_ocr: ~1,200 vectors
├── book_2_ocr: ~400 vectors
└── book_3_ocr: ~2,000 vectors
────────────────────────────────
Total: ~3,600 vectors (~15 MB)
```

### Vector Metadata:
```json
{
  "id": "book_1_ocr_chunk_123",
  "vector": [0.123, -0.456, ...],  // 1536 dimensions
  "payload": {
    "source_id": "book_1_ocr",
    "unit": "unit_3",
    "text": "Business meetings typically have three stages..."
  }
}
```

---

## ✅ POST-INGESTION CHECKLIST

- [ ] Collection shows correct number of points
- [ ] Search returns relevant results
- [ ] `/ask` endpoint works with RAG
- [ ] Roleplay scenarios use RAG context
- [ ] Android app can query via server
- [ ] Fly.io deployment has same vectors (if deployed)

---

## 🚀 READY TO INGEST?

Run this command to start:

```bash
cd C:\Users\sanja\rag-biz-english\server
$env:CONFIRM_INGEST="yes"
python ingest.py
```

Watch for successful output, then verify with `python setup_qdrant.py`.

---

**Document Status:** Ready to execute  
**Risk:** Very low (< $0.02 cost)  
**Time:** ~15 minutes total  
**Next Step:** Run the ingestion command above

