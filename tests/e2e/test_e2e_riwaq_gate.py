"""E2E Test: Four Deterministic Preflight Verification Gates for Riwaq (FM-06)."""

import json
from pathlib import Path
import pytest

from masar.core.models import HadithRecord, ImportBatch, IsnadVariant, SourceRef
from masar.export.preflight_gates import PreflightValidator


@pytest.fixture
def valid_record_1():
    return HadithRecord(
        hadith_id="bukhari_1",
        family_id="fam_niyyah_001",
        title="Bukhari 1",
        source_ref=SourceRef(
            collection="sahih_bukhari",
            source_type="print",
            source_locator="Book 1, Hadith 1",
            ingested_at="2026-10-26T12:00:00Z",
        ),
        variants=[
            IsnadVariant(
                variant_id="var_01",
                isnad_chain=["al_humaydi", "sufyan", "yahya_b_said", "umar_b_al_khattab"],
                matn_raw="إنما الأعمال بالنيات وإنما لكل امرئ ما نوى",
            )
        ],
        matn_raw="إنما الأعمال بالنيات وإنما لكل امرئ ما نوى",
    )


@pytest.fixture
def valid_record_2():
    return HadithRecord(
        hadith_id="muslim_1907",
        family_id="fam_niyyah_001",
        title="Muslim 1907",
        source_ref=SourceRef(
            collection="sahih_muslim",
            source_type="print",
            source_locator="Book 33, Hadith 1907",
            ingested_at="2026-10-26T12:00:00Z",
        ),
        variants=[
            IsnadVariant(
                variant_id="var_02",
                isnad_chain=["ibn_qanab", "malik", "yahya_b_said", "umar_b_al_khattab"],
                matn_raw="إنما الأعمال بالنية وإنما لامرئ ما نوى",
            )
        ],
        matn_raw="إنما الأعمال بالنية وإنما لامرئ ما نوى",
    )


def test_preflight_gate_valid_bundle(valid_record_1, valid_record_2, test_artifacts_dir: Path):
    """Verify clean multi-variant bundle passes all 4 deterministic gates."""
    batch = ImportBatch(
        schema_version=1,
        imported_at="2026-10-26T12:00:00Z",
        import_id="imp_valid_01",
        records=[valid_record_1, valid_record_2],
    )

    validator = PreflightValidator()
    report = validator.validate_batch(batch)

    assert report.all_passed is True
    assert report.gate_schema == "PASS"
    assert report.gate_family_consistency == "PASS"
    assert report.gate_boundary_hygiene == "PASS"
    assert report.gate_isnad_integrity == "PASS"
    assert len(report.errors) == 0

    # Write verifiable artifact
    artifact_path = test_artifacts_dir / "riwaq_preflight_pass.json"
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "scenario": "FM-06 Riwaq Preflight Gate Validation",
                "batch_id": batch.import_id,
                "record_count": len(batch.records),
                "report": report.model_dump(),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    assert artifact_path.exists()
    assert artifact_path.stat().st_size > 0


def test_preflight_gate_family_inconsistency_blocked(valid_record_1, valid_record_2):
    """Verify gate failure when records have mismatched family IDs."""
    # Modify second record to have different family ID
    record_bad_fam = valid_record_2.model_copy(update={"family_id": "fam_different_999"})
    batch = ImportBatch(
        schema_version=1,
        imported_at="2026-10-26T12:00:00Z",
        records=[valid_record_1, record_bad_fam],
    )

    validator = PreflightValidator()
    report = validator.validate_batch(batch)

    assert report.all_passed is False
    assert report.gate_family_consistency == "FAIL"
    assert any("GATE_FAMILY_CONSISTENCY" in err for err in report.errors)


def test_preflight_gate_boundary_bleed_blocked(valid_record_1):
    """Verify gate failure when matn contains un-trimmed isnad formulas."""
    bleeding_record = valid_record_1.model_copy(
        update={"matn_raw": "قال قال رسول الله صلى الله عليه وسلم إنما الأعمال بالنيات"}
    )
    batch = ImportBatch(
        schema_version=1,
        imported_at="2026-10-26T12:00:00Z",
        records=[bleeding_record],
    )

    validator = PreflightValidator()
    report = validator.validate_batch(batch)

    assert report.all_passed is False
    assert report.gate_boundary_hygiene == "FAIL"
    assert any("GATE_BOUNDARY_HYGIENE" in err for err in report.errors)


def test_preflight_gate_empty_isnad_blocked(valid_record_1):
    """Verify gate failure when isnad chain is empty."""
    variant_empty = valid_record_1.variants[0].model_copy(update={"isnad_chain": []})
    empty_isnad_record = valid_record_1.model_copy(update={"variants": [variant_empty]})
    batch = ImportBatch(
        schema_version=1,
        imported_at="2026-10-26T12:00:00Z",
        records=[empty_isnad_record],
    )

    validator = PreflightValidator()
    report = validator.validate_batch(batch)

    assert report.all_passed is False
    assert report.gate_isnad_integrity == "FAIL"
    assert any("GATE_ISNAD_INTEGRITY" in err for err in report.errors)
