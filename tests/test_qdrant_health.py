from __future__ import annotations

import services


def test_qdrant_health_surfaces_invalid_endpoint_hint(monkeypatch):
    monkeypatch.setattr(services, "QDRANT_URL", "https://example.cloud.qdrant.io")
    monkeypatch.setattr(services, "QDRANT_COLLECTION", "bizeng")
    monkeypatch.setattr(
        services,
        "get_qdrant_collection_info",
        lambda: (_ for _ in ()).throw(
            RuntimeError("Unexpected Response: 404 (Not Found)\nRaw response content:\nb'404 page not found\\n'")
        ),
    )

    status = services.qdrant_health()

    assert status["ok"] is False
    assert "does not appear to point to a live Qdrant API endpoint" in status["error"]
