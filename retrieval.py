"""
Shared retrieval helpers.

Strategy:
- Prefer Qdrant vector retrieval when healthy.
- Fall back to lightweight local lexical retrieval from bundled course texts.
- Use short backoff after repeated Qdrant failures to avoid latency spikes.
"""
from __future__ import annotations

import math
import os
import re
import threading
import time
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from qdrant_client.models import SearchParams
from tiktoken import get_encoding

from services import (
    describe_qdrant_error,
    expected_embedding_dim,
    get_embed_client,
    get_embed_model_name,
    get_qdrant_client,
    get_qdrant_collection_info,
    qdrant_health,
)
from settings import QDRANT_COLLECTION, QDRANT_URL

_ENC = get_encoding("cl100k_base")
_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z'-]*")

_MATERIAL_MARKERS = {
    "business",
    "travel",
    "meeting",
    "negotiation",
    "contract",
    "client",
    "logistics",
    "shipment",
    "transport",
    "delivery",
    "market",
    "trade",
    "supply",
    "demand",
    "budget",
    "salary",
    "finance",
    "inflation",
    "customs",
    "reimbursement",
    "stakeholder",
    "entrepreneur",
    "counteroffer",
    "presentation",
    "discussion",
    "pronunciation",
    "vocabulary",
    "grammar",
    "phrase",
    "email",
    "report",
}

_QDRANT_BACKOFF_UNTIL = 0.0
_QDRANT_FAILURES = 0
_QDRANT_LOCK = threading.Lock()


def _tokenize(value: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(value or "")]


def is_material_related_query(query: str, extra_markers: Iterable[str] | None = None) -> bool:
    normalized = (query or "").strip().lower()
    if len(normalized) < 8:
        return False

    markers = set(_MATERIAL_MARKERS)
    if extra_markers:
        markers.update(marker.lower() for marker in extra_markers)
    if any(marker in normalized for marker in markers):
        return True

    query_tokens = [token for token in _tokenize(normalized) if len(token) > 3]
    return len(query_tokens) >= 6


def _candidate_material_dirs() -> list[Path]:
    base_dir = Path(__file__).resolve().parent
    env_candidates: list[Path] = []

    env_dirs = os.getenv("LOCAL_RAG_DIRS", "").strip()
    if env_dirs:
        for raw_value in env_dirs.split(","):
            raw_value = raw_value.strip()
            if raw_value:
                env_candidates.append(Path(raw_value))

    include_defaults = os.getenv("LOCAL_RAG_INCLUDE_DEFAULTS", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    if env_candidates and not include_defaults:
        candidates = list(env_candidates)
    else:
        candidates: list[Path] = list(env_candidates)
        candidates.append(base_dir / "rag_materials")
        candidates.append(base_dir.parent / "data")

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.resolve()) if candidate.exists() else str(candidate)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def _iter_material_files() -> list[Path]:
    files: list[Path] = []
    for directory in _candidate_material_dirs():
        if not directory.exists() or not directory.is_dir():
            continue
        files.extend(sorted(directory.glob("*.txt")))
    return files


def _chunk_text(text: str, max_chars: int = 700) -> list[str]:
    normalized = (text or "").replace("\r\n", "\n")
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", normalized) if paragraph.strip()]
    if not paragraphs:
        paragraphs = [normalized.strip()]

    chunks: list[str] = []
    buffer = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_chars * 2:
            if buffer:
                chunks.append(buffer.strip())
                buffer = ""
            for start in range(0, len(paragraph), max_chars):
                piece = paragraph[start : start + max_chars].strip()
                if piece:
                    chunks.append(piece)
            continue

        candidate = paragraph if not buffer else f"{buffer}\n\n{paragraph}"
        if len(candidate) <= max_chars:
            buffer = candidate
        else:
            chunks.append(buffer.strip())
            buffer = paragraph

    if buffer.strip():
        chunks.append(buffer.strip())
    return chunks


def _source_weight(path: Path) -> float:
    name = path.name.lower()
    parent = path.parent.name.lower()

    weight = 1.0
    if parent == "rag_materials":
        weight += 0.35
    if any(marker in name for marker in ("sample", "lesson", "course", "focus", "meeting", "negotiation")):
        weight += 0.2
    if "ocr" in name:
        weight -= 0.3
    return max(weight, 0.5)


class LocalGroundingIndex:
    def __init__(self):
        self.files: list[str] = []
        self.chunks: list[dict[str, Any]] = []
        self.idf: dict[str, float] = {}
        self._build_error: str | None = None
        self._build()

    def _build(self) -> None:
        try:
            doc_freq: Counter[str] = Counter()
            for path in _iter_material_files():
                text = path.read_text(encoding="utf-8", errors="ignore")
                source_id = path.stem
                source_weight = _source_weight(path)
                self.files.append(path.name)
                for chunk in _chunk_text(text):
                    tokens = [token for token in _tokenize(chunk) if len(token) > 2]
                    if not tokens:
                        continue
                    tf = Counter(tokens)
                    self.chunks.append(
                        {
                            "text": chunk,
                            "source_id": source_id,
                            "token_count": len(tokens),
                            "tf": tf,
                            "source_weight": source_weight,
                        }
                    )
                    doc_freq.update(tf.keys())

            total_docs = max(len(self.chunks), 1)
            self.idf = {
                term: math.log(1.0 + (total_docs / (1.0 + frequency)))
                for term, frequency in doc_freq.items()
            }
        except Exception as exc:
            self._build_error = f"{type(exc).__name__}: {exc}"

    def health(self) -> dict[str, Any]:
        if self._build_error:
            return {
                "ok": False,
                "backend": "local_lexical",
                "error": self._build_error,
            }
        return {
            "ok": bool(self.chunks),
            "backend": "local_lexical",
            "files": len(self.files),
            "chunks": len(self.chunks),
        }

    def search(self, query: str, k: int, max_context_chars: int) -> tuple[str, list[str]]:
        if not self.chunks:
            return "", []

        query_terms = [token for token in _tokenize(query) if len(token) > 2]
        if not query_terms:
            return "", []

        scored: list[tuple[float, dict[str, Any]]] = []
        query_term_count = len(query_terms)

        for chunk in self.chunks:
            tf: Counter[str] = chunk["tf"]
            overlap = 0
            score = 0.0
            for term in query_terms:
                term_count = tf.get(term, 0)
                if term_count:
                    overlap += 1
                    score += (1.0 + math.log(term_count)) * self.idf.get(term, 1.0)
            if overlap == 0:
                continue
            coverage = overlap / query_term_count
            length_penalty = 1.0 / (1.0 + math.log(1.0 + chunk["token_count"]))
            final_score = score * (0.75 + coverage) * (1.1 + length_penalty) * chunk["source_weight"]
            scored.append((final_score, chunk))

        if not scored:
            return "", []

        scored.sort(key=lambda item: item[0], reverse=True)
        chosen = [chunk for _, chunk in scored[: max(k * 3, k)]]

        context_parts: list[str] = []
        sources: list[str] = []
        used_chars = 0
        seen_source: set[str] = set()
        for chunk in chosen:
            text_value = chunk["text"].strip()
            if not text_value:
                continue
            extra_chars = len(text_value) + (5 if context_parts else 0)
            if used_chars + extra_chars > max_context_chars:
                continue
            context_parts.append(text_value)
            used_chars += extra_chars

            source = str(chunk["source_id"])
            if source and source not in seen_source:
                seen_source.add(source)
                sources.append(source)
            if len(context_parts) >= k:
                break

        context = "\n\n---\n\n".join(context_parts)
        return context, sources


@lru_cache(maxsize=1)
def get_local_index() -> LocalGroundingIndex:
    return LocalGroundingIndex()


def local_retrieval_health() -> dict[str, Any]:
    return get_local_index().health()


def _qdrant_circuit_open() -> bool:
    return time.time() < _QDRANT_BACKOFF_UNTIL


def _mark_qdrant_failure() -> None:
    global _QDRANT_BACKOFF_UNTIL, _QDRANT_FAILURES
    with _QDRANT_LOCK:
        _QDRANT_FAILURES = min(_QDRANT_FAILURES + 1, 6)
        backoff_seconds = min(180.0, 5.0 * (2 ** (_QDRANT_FAILURES - 1)))
        _QDRANT_BACKOFF_UNTIL = time.time() + backoff_seconds


def _mark_qdrant_success() -> None:
    global _QDRANT_BACKOFF_UNTIL, _QDRANT_FAILURES
    with _QDRANT_LOCK:
        _QDRANT_FAILURES = 0
        _QDRANT_BACKOFF_UNTIL = 0.0


def _bm25ish_score(text_value: str, query: str) -> int:
    query_words = _tokenize(query)
    text_words = set(_tokenize(text_value))
    return sum(1 for word in query_words if word in text_words)


def _pack_context(hits: list[Any], token_budget: int = 1200) -> str:
    chunks: list[str] = []
    used = 0
    for hit in hits:
        text_value = (hit.payload.get("text") or "").strip()
        if not text_value:
            continue
        token_count = len(_ENC.encode(text_value))
        if used + token_count > token_budget:
            continue
        chunks.append(text_value)
        used += token_count
    return "\n\n---\n\n".join(chunks)


@lru_cache(maxsize=1)
def _qdrant_vector_size() -> int:
    info = get_qdrant_collection_info()
    vectors = info.config.params.vectors
    if hasattr(vectors, "size"):
        return int(vectors.size)
    if isinstance(vectors, dict) and vectors:
        return int(next(iter(vectors.values())).size)
    raise RuntimeError("Unable to determine Qdrant vector size")


def _retrieve_from_qdrant(query: str, k: int, max_context_chars: int) -> tuple[str, list[str]]:
    if not QDRANT_URL:
        raise RuntimeError("QDRANT_URL is not configured")
    if _qdrant_circuit_open():
        seconds_left = max(1, int(_QDRANT_BACKOFF_UNTIL - time.time()))
        raise RuntimeError(f"Qdrant backoff active ({seconds_left}s left)")

    vector_size = _qdrant_vector_size()
    expected_size = expected_embedding_dim()
    if vector_size != expected_size:
        raise RuntimeError(
            f"Embedding model dimension {expected_size} does not match collection dimension {vector_size}"
        )

    embedding = get_embed_client().embeddings.create(
        model=get_embed_model_name(),
        input=query,
    ).data[0].embedding

    raw_hits = get_qdrant_client().search(
        collection_name=QDRANT_COLLECTION,
        query_vector=embedding,
        limit=max(k, 50),
        with_payload=True,
        search_params=SearchParams(hnsw_ef=128, exact=False),
    )
    if not raw_hits:
        return "", []

    raw_hits.sort(
        key=lambda hit: (hit.score or 0.0) + 0.001 * _bm25ish_score((hit.payload or {}).get("text", ""), query),
        reverse=True,
    )
    hits = raw_hits[:k]
    context = _pack_context(hits, token_budget=1200)
    if len(context) > max_context_chars:
        context = context[:max_context_chars]
    sources = [
        str((hit.payload or {}).get("source_id") or "")
        for hit in hits
        if (hit.payload or {}).get("source_id")
    ]
    return context, sources


@dataclass
class GroundingResult:
    context: str
    sources: list[str]
    backend: str
    degraded_reason: str | None = None


def retrieve_grounding(query: str, k: int, max_context_chars: int) -> GroundingResult:
    qdrant_error: str | None = None
    try:
        context, sources = _retrieve_from_qdrant(query=query, k=k, max_context_chars=max_context_chars)
        _mark_qdrant_success()
        if context:
            return GroundingResult(context=context, sources=sources, backend="qdrant")
    except Exception as exc:
        _mark_qdrant_failure()
        qdrant_error = describe_qdrant_error(exc)
        print(f"[retrieval] qdrant unavailable -> fallback: {qdrant_error}", flush=True)

    local_context, local_sources = get_local_index().search(
        query=query,
        k=max(k, 1),
        max_context_chars=max_context_chars,
    )
    if local_context:
        return GroundingResult(
            context=local_context,
            sources=local_sources,
            backend="local_lexical",
            degraded_reason=qdrant_error,
        )
    return GroundingResult(context="", sources=[], backend="none", degraded_reason=qdrant_error)


def retrieval_health() -> dict[str, Any]:
    vector = qdrant_health()
    local = local_retrieval_health()
    preferred_backend = "qdrant" if vector.get("ok") else ("local_lexical" if local.get("ok") else "none")
    return {
        "ok": bool(vector.get("ok") or local.get("ok")),
        "preferred_backend": preferred_backend,
        "qdrant": vector,
        "local_lexical": local,
    }
