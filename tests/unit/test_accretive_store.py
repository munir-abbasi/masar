"""Unit tests for Accretive Ground Truth Store and Read-Through Overlay (ADR D011)."""

from pathlib import Path
import pytest
from masar.core.corpus_db import RiwayatCorpusAdapter
from masar.core.models import SplitBoundary
from masar.verification.accretive_store import AccretiveStore


def test_accretive_store_save_and_retrieve_override(tmp_path: Path):
    """Verify persisting and retrieving a boundary override."""
    db_file = tmp_path / "masar-curated.db"
    store = AccretiveStore(db_file)

    boundary = SplitBoundary(
        matn_start=149,
        matn_end=187,
        pre_matn_token="وسلم",
        post_isnad_token="إنما",
        anchor_window="صلى الله عليه وسلم إنما الأعمال",
    )
    store.save_boundary_override("bukhari_2529", boundary, curator="agent_test")

    retrieved = store.get_boundary_override("bukhari_2529")
    assert retrieved is not None
    assert retrieved.matn_start == 149
    assert retrieved.matn_end == 187
    assert retrieved.pre_matn_token == "وسلم"


def test_read_through_overlay_resolution(mock_db_path, tmp_path: Path):
    """Verify read-through overlay applies curated boundary over immutable base corpus."""
    base_adapter = RiwayatCorpusAdapter(mock_db_path)
    curated_db_file = tmp_path / "masar-curated.db"
    store = AccretiveStore(curated_db_file)

    # Base record 4 has the boundary bleed defect
    base_record = base_adapter.get_record("4")
    assert base_record is not None
    assert base_record.matn.startswith("قال قال رسول الله")

    # Persist curated override into accretive store
    repaired_boundary = SplitBoundary(
        matn_start=149,
        matn_end=187,
        pre_matn_token="وسلم",
        post_isnad_token="إنما",
    )
    store.save_boundary_override("4", repaired_boundary, curator="agent_verifier")

    # Resolve through read-through overlay
    resolved_record = store.resolve_record("4", base_adapter)
    assert resolved_record is not None
    assert not resolved_record.matn.startswith("قال قال رسول الله")
    assert resolved_record.matn.startswith("إنما الأعمال بالنية")

    # Verify base storage remains immutable
    fresh_base = base_adapter.get_record("4")
    assert fresh_base.matn.startswith("قال قال رسول الله")
