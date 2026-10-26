"""Unit tests for FastAPI REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

from masar.api.app import create_app


@pytest.fixture
def api_client(mock_db_path, tmp_path):
    curated_db = tmp_path / "masar-curated.db"
    session_db = tmp_path / "masar_session.db"
    app = create_app(db_path=mock_db_path, curated_db=curated_db, session_db=session_db)
    return TestClient(app)


def test_api_diagnose(api_client):
    """Verify GET /api/diagnose returns healthy status."""
    resp = api_client.get("/api/diagnose")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert data["record_count"] == 6


def test_api_search(api_client):
    """Verify POST /api/search executes multi-signal query."""
    resp = api_client.post(
        "/api/search",
        json={"seed_text": "إنما الأعمال بالنيات", "scope": "all", "semantic_top_k": 10},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["receipt"] is not None


def test_api_get_hadith(api_client):
    """Verify GET /api/hadith/{id} returns candidate record."""
    resp = api_client.get("/api/hadith/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "1"
    assert "إنما الأعمال بالنيات" in data["matn"]


def test_api_adjust_split_and_export(api_client):
    """Verify POST /api/split and POST /api/export."""
    # Split repair
    resp_split = api_client.post(
        "/api/split",
        json={"hadith_id": "4", "matn_start": 149, "matn_end": 187},
    )
    assert resp_split.status_code == 200
    assert resp_split.json()["status"] == "SUCCESS"

    # Export batch
    resp_export = api_client.post(
        "/api/export",
        json={"record_ids": ["1", "4"], "family_id": "fam_api_test"},
    )
    assert resp_export.status_code == 200
    batch = resp_export.json()
    assert batch["schema_version"] == 1
    assert len(batch["records"]) == 2
