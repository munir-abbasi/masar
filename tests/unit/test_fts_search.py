"""Unit tests for SQLite FTS5 lexical BM25 search engine."""

import sqlite3
import pytest
from masar.discovery.fts_search import FtsSearchEngine


def test_fts_engine_build_index_and_search(mock_db_path):
    """Verify FTS5 table creation, phrase search, and normalized BM25 ranking."""
    conn = sqlite3.connect(mock_db_path)
    engine = FtsSearchEngine(conn)
    engine.ensure_index()

    # Search for Niyyah
    results = engine.search("الأعمال بالنيات", scope="all", limit=10)
    assert len(results) > 0

    # Top result should be record 1 (Bukhari 1) or record 2 (Muslim 1907) or record 5 (al-Kafi 35)
    top_id, top_score = results[0]
    assert top_score > 0.0
    assert top_score <= 1.0


def test_fts_engine_sectarian_scoping(mock_db_path):
    """Verify sectarian filter in FTS5 queries."""
    conn = sqlite3.connect(mock_db_path)
    engine = FtsSearchEngine(conn)
    engine.ensure_index()

    # Shia search
    results_shia = engine.search("الأعمال", scope="shia", limit=10)
    for hid, score in results_shia:
        cur = conn.cursor()
        cur.execute("SELECT sect FROM hadiths WHERE id = ?", (hid,))
        sect = cur.fetchone()[0]
        assert sect == "shia"


def test_fts_engine_dynamic_index(mock_db_path):
    """Verify indexing an ad-hoc record dynamically."""
    conn = sqlite3.connect(mock_db_path)
    engine = FtsSearchEngine(conn)
    engine.ensure_index()

    engine.index_record(
        record_id=999,
        matn="طلب العلم فريضة على كل مسلم",
        collection="sunan_ibn_majah",
        sect="sunni",
    )

    results = engine.search("طلب العلم فريضة", scope="sunni")
    found_ids = [rid for rid, _ in results]
    assert "999" in found_ids or 999 in found_ids
