"""Unit tests for CorpusAdapter protocol and RiwayatCorpusAdapter."""

import time
import pytest
from masar.core.corpus_adapter import CorpusAdapter
from masar.core.corpus_db import RiwayatCorpusAdapter
from masar.core.models import TakhrijQuery


def test_riwayat_adapter_implements_protocol(mock_db_path):
    """Verify RiwayatCorpusAdapter conforms to CorpusAdapter protocol."""
    adapter = RiwayatCorpusAdapter(mock_db_path)
    assert isinstance(adapter, CorpusAdapter)


def test_get_record_by_id(mock_db_path):
    """Verify retrieval of a single record with proper fields."""
    adapter = RiwayatCorpusAdapter(mock_db_path)
    record = adapter.get_record("1")
    assert record is not None
    assert record.id == "1"
    assert record.collection == "sahih_bukhari"
    assert record.hadith_number == "1"
    assert record.sect == "sunni"
    assert "إنما الأعمال بالنيات" in record.matn
    assert len(record.narrator_ids) == 6


def test_get_nonexistent_record(mock_db_path):
    """Verify None is returned for non-existent record."""
    adapter = RiwayatCorpusAdapter(mock_db_path)
    record = adapter.get_record("999999")
    assert record is None


def test_list_collections(mock_db_path):
    """Verify unique collections listed across database."""
    adapter = RiwayatCorpusAdapter(mock_db_path)
    collections = adapter.list_collections()
    assert "sahih_bukhari" in collections
    assert "sahih_muslim" in collections
    assert "al_kafi" in collections
    assert "musnad_ahmad" in collections


def test_sectarian_scoping(mock_db_path):
    """Verify filtering by sectarian scope (sunni, shia, all)."""
    adapter = RiwayatCorpusAdapter(mock_db_path)

    # All scope
    q_all = TakhrijQuery(seed_text="الأعمال", scope="all")
    results_all = list(adapter.query_candidates(q_all, limit=50))
    assert len(results_all) == 6

    # Sunni only
    q_sunni = TakhrijQuery(seed_text="الأعمال", scope="sunni")
    results_sunni = list(adapter.query_candidates(q_sunni, limit=50))
    assert len(results_sunni) == 5
    for r in results_sunni:
        assert r.sect == "sunni"

    # Shīʿī only
    q_shia = TakhrijQuery(seed_text="الأعمال", scope="shia")
    results_shia = list(adapter.query_candidates(q_shia, limit=50))
    assert len(results_shia) == 1
    assert results_shia[0].sect == "shia"
    assert results_shia[0].collection == "al_kafi"


def test_query_performance(mock_db_path):
    """Verify sub-50ms candidate query response time."""
    adapter = RiwayatCorpusAdapter(mock_db_path)
    q = TakhrijQuery(seed_text="الأعمال", scope="all")

    t0 = time.perf_counter()
    results = list(adapter.query_candidates(q, limit=50))
    duration_ms = (time.perf_counter() - t0) * 1000

    assert len(results) > 0
    assert duration_ms < 50.0
