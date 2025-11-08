# peek_qdrant.py
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from settings import QDRANT_URL, QDRANT_COLLECTION
from tiktoken import get_encoding

enc = get_encoding("cl100k_base")
qdr = QdrantClient(url=QDRANT_URL)

# 1) Count points
cnt = qdr.count(QDRANT_COLLECTION, count_filter=None, exact=True).count
print(f"[peek] total points in '{QDRANT_COLLECTION}':", cnt)

# 2) Scroll (page through all points, payload only)
scroll_res, next_off = qdr.scroll(
    collection_name=QDRANT_COLLECTION,
    limit=20,
    with_payload=True,
    with_vectors=False,
)
print(f"[peek] first {len(scroll_res)} payloads:")
for i, pt in enumerate(scroll_res, 1):
    text = (pt.payload.get("text") or "").strip().replace("\n", " ")[:180]
    unit = pt.payload.get("unit")
    src  = pt.payload.get("source_id")
    toks = len(enc.encode(pt.payload.get("text") or ""))
    print(f"{i:02d}. unit={unit!r} src={src!r} toks={toks} text={text!r}")

# 2b) Show samples from each book
for book_source_id in ["book_1_ocr", "book_2_ocr", "book_3_ocr"]:
    flt_book = Filter(must=[FieldCondition(key="source_id", match=MatchValue(value=book_source_id))])
    scroll_res, next_off = qdr.scroll(
        collection_name=QDRANT_COLLECTION,
        limit=10,
        with_payload=True,
        with_vectors=False,
        scroll_filter=flt_book,
    )
    print(f"\n[peek] first {len(scroll_res)} payloads for source_id={book_source_id!r}:")
    for i, pt in enumerate(scroll_res, 1):
        text = (pt.payload.get("text") or "").strip().replace("\n", " ")[:180]
        unit = pt.payload.get("unit")
        src  = pt.payload.get("source_id")
        toks = len(enc.encode(pt.payload.get("text") or ""))
        print(f"{i:02d}. unit={unit!r} src={src!r} toks={toks} text={text!r}")

# 3) (Optional) filter by unit as currently stored (case-sensitive!)
want = "Unit 1"
flt = Filter(must=[FieldCondition(key="unit", match=MatchValue(value=want))])
scroll_res, _ = qdr.scroll(QDRANT_COLLECTION, limit=10, with_payload=True, with_vectors=False, scroll_filter=flt)
print(f"\n[peek] points with unit={want!r}: {len(scroll_res)}")
