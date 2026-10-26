"""E2E Test: Topical False Positive Quarantining / Topic Trap Guard (FM-03)."""

import json
from pathlib import Path
import sqlite3
import pytest

from masar.discovery.hybrid_engine import HybridTakhrijEngine
from masar.core.models import TakhrijQuery


def test_topical_false_positive_quarantine_and_artifact(mock_db_path, test_artifacts_dir: Path):
    """Verify that semantically similar topical matches without isnad or pericope backing are quarantined."""
    conn = sqlite3.connect(mock_db_path)
    engine = HybridTakhrijEngine(conn)
    engine.ensure_index()

    # Query seed: Hadith al-Niyyah (Umar b. al-Khattab)
    query = TakhrijQuery(
        seed_text="إنما الأعمال بالنيات وإنما لكل امرئ ما نوى",
        companion_id="umar_b_al_khattab",
        hub_narrator_ids=["yahya_b_said"],
        min_pericope_threshold=0.35,
        scope="all",
    )

    candidates = engine.discover(query, limit=10)

    # Candidate 2 (Muslim 1907) must be accepted as a true variant
    muslim_cand = next((c for c in candidates if c.id == "2"), None)
    assert muslim_cand is not None
    assert muslim_cand.receipt is not None
    assert muslim_cand.receipt.is_topical_false_positive is False
    assert muslim_cand.receipt.ensemble_score >= 0.50

    # Candidate 6 (Musnad Ahmad 21840 - "إنما الأعمال بخواتيمها") has high semantic cosine
    # but zero isnad overlap with Umar/Yahya and low pericope Jaccard.
    # It must be quarantined!
    ahmad_cand = next((c for c in candidates if c.id == "6"), None)
    assert ahmad_cand is not None
    assert ahmad_cand.receipt is not None
    assert ahmad_cand.receipt.is_topical_false_positive is True, "Musnad Ahmad 21840 must be quarantined as topical false positive"
    assert "Topic Trap" in ahmad_cand.receipt.quarantine_reason

    # Generate verifiable artifact
    artifact_path = test_artifacts_dir / "topical_quarantine_report.json"
    artifact_payload = {
        "scenario": "FM-03 Topical False Positive Quarantine",
        "query": query.model_dump(),
        "candidates_evaluated": len(candidates),
        "quarantined_candidates": [
            {
                "id": c.id,
                "collection": c.collection,
                "hadith_number": c.hadith_number,
                "matn": c.matn,
                "receipt": c.receipt.model_dump(),
            }
            for c in candidates
            if c.receipt and c.receipt.is_topical_false_positive
        ],
        "verified_variants": [
            {
                "id": c.id,
                "collection": c.collection,
                "hadith_number": c.hadith_number,
                "matn": c.matn,
                "receipt": c.receipt.model_dump(),
            }
            for c in candidates
            if c.receipt and not c.receipt.is_topical_false_positive
        ],
    }
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(artifact_payload, f, ensure_ascii=False, indent=2)

    assert artifact_path.exists()
    assert artifact_path.stat().st_size > 0
