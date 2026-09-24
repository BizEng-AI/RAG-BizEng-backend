from __future__ import annotations

from pathlib import Path

import retrieval


def test_local_rag_dirs_can_override_default_corpus(monkeypatch, tmp_path):
    sample_dir = tmp_path / "materials"
    sample_dir.mkdir()
    (sample_dir / "mini_handout.txt").write_text(
        "Negotiation basics:\n\nUse a clear agenda and make a polite counteroffer.",
        encoding="utf-8",
    )

    monkeypatch.setenv("LOCAL_RAG_DIRS", str(sample_dir))
    monkeypatch.delenv("LOCAL_RAG_INCLUDE_DEFAULTS", raising=False)
    retrieval.get_local_index.cache_clear()

    health = retrieval.local_retrieval_health()

    assert health["ok"] is True
    assert health["files"] == 1
    assert health["chunks"] >= 1


def test_curated_rag_material_beats_ocr_noise(monkeypatch):
    curated_dir = Path(__file__).resolve().parents[1] / "rag_materials"
    monkeypatch.setenv("LOCAL_RAG_DIRS", str(curated_dir))
    monkeypatch.delenv("LOCAL_RAG_INCLUDE_DEFAULTS", raising=False)
    monkeypatch.setattr(
        retrieval,
        "_retrieve_from_qdrant",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("qdrant unavailable")),
    )
    retrieval.get_local_index.cache_clear()

    result = retrieval.retrieve_grounding(
        query="Why is rail more cost-effective than air for this shipment?",
        k=3,
        max_context_chars=1200,
    )

    assert result.backend == "local_lexical"
    assert "sample_business_negotiation_playbook" in result.sources
    assert all("ocr" not in source for source in result.sources)
    assert "cost-effective" in result.context.lower()
