from __future__ import annotations

import retrieval


def test_local_retrieval_health_has_materials():
    retrieval.get_local_index.cache_clear()
    health = retrieval.local_retrieval_health()
    assert health["ok"] is True
    assert health["backend"] == "local_lexical"
    assert health["files"] >= 1
    assert health["chunks"] >= 1


def test_retrieve_grounding_falls_back_to_local(monkeypatch):
    def _raise_qdrant_failure(*_args, **_kwargs):
        raise RuntimeError("qdrant unreachable")

    monkeypatch.setattr(retrieval, "_retrieve_from_qdrant", _raise_qdrant_failure)

    retrieval.get_local_index.cache_clear()
    result = retrieval.retrieve_grounding(
        query="How can I open a contract negotiation meeting with a clear timeline?",
        k=3,
        max_context_chars=1800,
    )
    assert result.backend == "local_lexical"
    assert result.context
    assert len(result.sources) >= 1
