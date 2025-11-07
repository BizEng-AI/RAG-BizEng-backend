# ingest.py — loud, env-driven, 2-arg API
from pathlib import Path
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from openai import OpenAI, AzureOpenAI
from tiktoken import get_encoding
from settings import *
import sys
import re
import uuid  # <-- Added missing import

print("[ingest] starting…", flush=True)
print("[ingest] cwd:", Path.cwd(), flush=True)

# ---- config from env (so you don't pass extra function args) ----
LIMIT_CHUNKS = int(os.getenv("LIMIT_CHUNKS", "0"))
BATCH = int(os.getenv("BATCH", "64"))
USE_MOCK = os.getenv("USE_MOCK", "0") == "1"

print(f"[ingest] USE_MOCK={USE_MOCK}  LIMIT_CHUNKS={LIMIT_CHUNKS}  BATCH={BATCH}", flush=True)
print(f"[ingest] QDRANT_URL={QDRANT_URL}  COLLECTION={QDRANT_COLLECTION}", flush=True)
print(f"[ingest] EMBED_MODEL={EMBED_MODEL}", flush=True)

enc = get_encoding("cl100k_base")
qdr = QdrantClient(url=QDRANT_URL)

# Initialize OpenAI client for embeddings (Azure UAE North or regular OpenAI)
if USE_AZURE_EMBEDDINGS:
    oai = AzureOpenAI(
        api_key=AZURE_OPENAI_EMBEDDING_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_EMBEDDING_ENDPOINT
    )
    embed_model = AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    print(f"[ingest] Using Azure Embeddings - Deployment: {embed_model} (Endpoint: {AZURE_OPENAI_EMBEDDING_ENDPOINT})", flush=True)
else:
    oai = OpenAI(api_key=OPENAI_API_KEY)
    embed_model = EMBED_MODEL
    print(f"[ingest] Using OpenAI - Embed model: {embed_model}", flush=True)

def chunk_text(text: str, max_tokens=900, overlap=150) -> List[str]:
    toks = enc.encode(text)
    chunks, i = [], 0
    while i < len(toks):
        chunks.append(enc.decode(toks[i:i+max_tokens]))
        i += max_tokens - overlap
    return chunks

def detect_unit(text: str) -> str | None:
    """
    Try to find a heading like 'Unit 5', 'Chapter 3', 'Lesson 2' in the text.
    Returns the matched label (e.g., 'Unit 5') or None.
    """
    m = re.search(r'\b(?:unit|chapter|lesson)\s+(\d{1,3})\b', text, flags=re.IGNORECASE)
    if not m:
        return None
    word = re.search(r'(unit|chapter|lesson)', m.group(0), flags=re.IGNORECASE).group(1).title()
    num = m.group(1)
    return f"{word} {num}"

def embed_texts(texts: List[str]) -> List[List[float]]:
    if USE_MOCK:
        import random
        print(f"[ingest] MOCK embedding {len(texts)} chunks", flush=True)
        return [[random.random() for _ in range(1536)] for _ in texts]
    print(f"[ingest] calling OpenAI embeddings for {len(texts)} chunks…", flush=True)
    data = oai.embeddings.create(model=embed_model, input=texts, timeout=60).data
    return [e.embedding for e in data]

def ensure_collection():
    dim = 1536 if "3-small" in embed_model else 3072
    if not qdr.collection_exists(QDRANT_COLLECTION):
        print(f"[ingest] creating collection '{QDRANT_COLLECTION}' (dim={dim})", flush=True)
        qdr.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            hnsw_config={"m": 16, "ef_construct": 128}
        )
    else:
        print(f"[ingest] collection '{QDRANT_COLLECTION}' exists", flush=True)

def upsert_book(path: str, source_id: str):
    p = Path(path)
    if not p.exists():
        print(f"[ingest][ERROR] file not found: {p.resolve()}", flush=True)
        sys.exit(2)

    print(f"[ingest] reading: {p.resolve()}", flush=True)
    text = p.read_text(encoding="utf-8")
    chunks = chunk_text(text)
    total = len(chunks)
    chunks = chunks[:LIMIT_CHUNKS] if LIMIT_CHUNKS > 0 else chunks
    print(f"[ingest] total_chunks={total}  using={len(chunks)}", flush=True)

    vectors = []
    for i in range(0, len(chunks), BATCH):
        part = chunks[i:i+BATCH]
        print(f"[ingest] embedding batch {i+1}-{i+len(part)} / {len(chunks)}", flush=True)
        vectors += embed_texts(part)

    points = []
    for v, c in zip(vectors, chunks):
        c_clean = clean_ocr_text(c)
        payload = {"text": c_clean, "source_id": source_id}
        # (skip unit entirely for now)
        points.append(PointStruct(id=str(uuid.uuid4()), vector=v, payload=payload))

    print(f"[ingest] upserting {len(points)} points…", flush=True)
    qdr.upsert(collection_name=QDRANT_COLLECTION, points=points)
    print("[ingest] done ✅", flush=True)

def delete_book_vectors(source_id: str):
    """
    Delete all vectors in Qdrant collection with the given source_id.
    """
    from qdrant_client.http import models
    print(f"[ingest] Deleting all vectors with source_id='{source_id}' from collection '{QDRANT_COLLECTION}'", flush=True)
    qdr.delete(
        collection_name=QDRANT_COLLECTION,
        points_selector=models.Filter(
            must=[
                models.FieldCondition(
                    key="source_id",
                    match=models.MatchValue(value=source_id)
                )
            ]
        )
    )
    print(f"[ingest] Deleted all vectors with source_id='{source_id}'", flush=True)

def clean_ocr_text(t: str) -> str:
    # normalize quotes/ligatures and drop non-printables
    t = t.replace("\u2018","'").replace("\u2019","'").replace("\u201c","\"").replace("\u201d","\"")
    t = t.replace("\u2013","-").replace("\u2014","-")
    t = re.sub(r"[^ -~\n\t]", " ", t)   # keep ASCII range + whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t

# ... inside upsert_book():


if __name__ == "__main__":
    # safety gate for paid runs
    if not USE_MOCK and os.getenv("CONFIRM_INGEST", "no").lower() != "yes":
        print("[ingest][ABORT] Set CONFIRM_INGEST=yes for real embeddings, or USE_MOCK=1", flush=True)
        sys.exit(1)

    ensure_collection()
    if len(sys.argv) > 2 and sys.argv[1] == "delete":
        delete_book_vectors(sys.argv[2])
    else:
        # 👉 point to your real file
        upsert_book("C:/Users/sanja/rag-biz-english/data/book_1_ocr.txt", source_id="book_1_ocr")
