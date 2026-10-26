"""E2E Test: Cross-Sectarian Takhrīj Parity and Common Stock Bundling (FM-05)."""

import json
from pathlib import Path
import sqlite3
import pytest

from masar.core.corpus_db import RiwayatCorpusAdapter
from masar.core.models import SplitBoundary, TakhrijQuery
from masar.discovery.hybrid_engine import HybridTakhrijEngine
from masar.export.riwaq_exporter import RiwaqExporter
from masar.verification.accretive_store import AccretiveStore
from masar.verification.split_editor import SplitEditor


def test_cross_sectarian_takhrij_pipeline_and_artifact(mock_db_path, tmp_path: Path, test_artifacts_dir: Path):
    """Verify end-to-end takhrīj across Sunni and Shīʿī collections for shared 1st/2nd century traditions."""
    conn = sqlite3.connect(mock_db_path)
    engine = HybridTakhrijEngine(conn)
    engine.ensure_index()

    # 1. Query with cross-sectarian scope ("all")
    query = TakhrijQuery(
        seed_text="إنما الأعمال بالنيات وإنما لكل امرئ ما نوى",
        scope="all",
        min_pericope_threshold=0.35,
    )
    candidates = engine.discover(query, limit=10)

    # Verify both sects are represented
    sects_found = {c.sect for c in candidates if c.receipt and not c.receipt.is_topical_false_positive}
    assert "sunni" in sects_found
    assert "shia" in sects_found

    # Identify Sunni record (Bukhari 1) and Shīʿī record (al-Kāfī 35)
    bukhari_rec = next(c for c in candidates if c.collection == "sahih_bukhari" and c.hadith_number == "1")
    kafi_rec = next(c for c in candidates if c.collection == "al_kafi")

    assert bukhari_rec is not None
    assert kafi_rec is not None

    # 2. Boundary Curation: Repair bleed on Bukhari 2529 (record 4)
    curated_db = tmp_path / "masar-curated.db"
    curated_store = AccretiveStore(curated_db)
    base_adapter = RiwayatCorpusAdapter(mock_db_path)

    editor = SplitEditor()
    rec_4 = base_adapter.get_record("4")
    repaired_boundary = editor.repair_split(
        rec_4.full_text,
        SplitBoundary(matn_start=112, matn_end=len(rec_4.full_text)),
    )
    curated_store.save_boundary_override("4", repaired_boundary, curator="agent_e2e")

    # 3. Export verified cross-sectarian family bundle to Riwaq
    exporter = RiwaqExporter(base_adapter, curated_store)
    family_id = "fam_niyyah_common_stock"
    batch = exporter.build_batch(
        record_ids=["1", "2", "4", "5"],
        family_id=family_id,
        import_id="imp_cross_sect_001",
    )

    assert batch.schema_version == 1
    assert len(batch.records) == 4
    batch_sects = {r.source_ref.collection for r in batch.records}
    assert "sahih_bukhari" in batch_sects
    assert "sahih_muslim" in batch_sects
    assert "al_kafi" in batch_sects

    # 4. Generate verifiable artifact
    artifact_path = test_artifacts_dir / "cross_sectarian_family.json"
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "scenario": "FM-05 Cross-Sectarian Takhrīj Parity",
                "family_id": family_id,
                "collections_represented": sorted(list(batch_sects)),
                "records_count": len(batch.records),
                "export_batch": batch.model_dump(mode="json"),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    assert artifact_path.exists()
    assert artifact_path.stat().st_size > 0
