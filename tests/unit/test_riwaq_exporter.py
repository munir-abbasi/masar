"""Unit tests for Riwaq Batch Serializer."""

from pathlib import Path
import pytest

from masar.core.corpus_db import RiwayatCorpusAdapter
from masar.core.models import CandidateRecord, ImportBatch
from masar.export.riwaq_exporter import RiwaqExporter, PreflightGateError
from masar.verification.accretive_store import AccretiveStore


def test_export_clean_batch(mock_db_path, tmp_path: Path):
    """Verify exporting discovered candidates into Riwaq schema_version: 1 payload."""
    curated_db = tmp_path / "masar-curated.db"
    curated_store = AccretiveStore(curated_db)
    base_adapter = RiwayatCorpusAdapter(mock_db_path)

    exporter = RiwaqExporter(base_adapter, curated_store)

    # Candidates: Record 1 (Bukhari 1) and Record 2 (Muslim 1907)
    batch = exporter.build_batch(
        record_ids=["1", "2"],
        family_id="fam_niyyah_001",
        import_id="imp_niyyah_test",
    )

    assert isinstance(batch, ImportBatch)
    assert batch.schema_version == 1
    assert len(batch.records) == 2
    assert batch.records[0].family_id == "fam_niyyah_001"
    assert len(batch.records[0].variants[0].isnad_chain) > 0


def test_export_gate_failure_on_unrepaired_bleed(mock_db_path, tmp_path: Path):
    """Verify exporter refuses to export when a record has boundary bleed and raises PreflightGateError."""
    curated_db = tmp_path / "masar-curated.db"
    curated_store = AccretiveStore(curated_db)
    base_adapter = RiwayatCorpusAdapter(mock_db_path)

    exporter = RiwaqExporter(base_adapter, curated_store)

    # Record 4 has un-repaired boundary bleed in base corpus!
    with pytest.raises(PreflightGateError) as exc_info:
        exporter.build_batch(
            record_ids=["1", "4"],
            family_id="fam_niyyah_001",
        )

    assert "GATE_BOUNDARY_HYGIENE" in str(exc_info.value)
