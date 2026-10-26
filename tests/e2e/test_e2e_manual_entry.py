"""E2E Test: First-class manual text entry with heuristic split proposal (FM-07)."""

import json
from pathlib import Path
import pytest
from masar.core.manual_entry import ManualEntryPipeline, ManualEntryRequest
from masar.core.models import SplitBoundary


def test_manual_entry_heuristic_split_and_artifact(test_artifacts_dir: Path):
    """Verify raw unsegmented report is parsed with heuristic split and saves verifiable artifact."""
    raw_text = (
        "حدثنا مسدد قال حدثنا يحيى عن شعبة عن قتادة عن أنس قال: "
        "قال رسول الله صلى الله عليه وسلم إنما الأعمال بالنيات وإنما لكل امرئ ما نوى"
    )

    pipeline = ManualEntryPipeline()
    proposal = pipeline.propose_split(raw_text)

    # Heuristic proposal must detect the isnad-matn transition
    assert isinstance(proposal, SplitBoundary)
    assert proposal.matn_start > 0
    assert proposal.matn_end == len(raw_text)

    # Matn should contain the actual content, not the preceding isnad
    matn = raw_text[proposal.matn_start:proposal.matn_end].strip()
    assert "إنما الأعمال بالنيات" in matn
    assert "حدثنا مسدد" not in matn

    # Isnad should contain the transmission chain
    isnad = raw_text[:proposal.matn_start].strip()
    assert "حدثنا مسدد" in isnad
    assert "أنس" in isnad

    # Ingest full record with source provenance
    req = ManualEntryRequest(
        raw_text=raw_text,
        collection="Rare Manuscript MS-402",
        source_type="manuscript",
        source_locator="Folio 12b",
        hadith_number="MS-01",
        sect="sunni",
        family_id="fam_niyyah_ms",
        split_boundary=proposal,
        collector_note="Manual transcription from Berlin Staatsbibliothek MS 402",
    )
    hadith_record = pipeline.create_record(req)

    assert hadith_record.hadith_id.startswith("manual_")
    assert hadith_record.family_id == "fam_niyyah_ms"
    assert hadith_record.source_ref.source_type == "manuscript"
    assert hadith_record.source_ref.collection == "Rare Manuscript MS-402"
    assert len(hadith_record.variants) == 1
    assert "مسدد" in hadith_record.variants[0].isnad_raw

    # Terminate by generating verifiable artifact
    artifact_path = test_artifacts_dir / "manual_entry_verified.json"
    artifact_payload = {
        "scenario": "FM-07 Manual Entry & Heuristic Split",
        "raw_text": raw_text,
        "split_boundary": proposal.model_dump(),
        "parsed_isnad": isnad,
        "parsed_matn": matn,
        "hadith_record": hadith_record.model_dump(mode="json"),
    }
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(artifact_payload, f, ensure_ascii=False, indent=2)

    assert artifact_path.exists()
    assert artifact_path.stat().st_size > 0
