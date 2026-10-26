"""E2E Test: Heuristic Bleed Guard and Dual Anchor-Offset Split Editor (FM-01, ADR D012)."""

import json
from pathlib import Path
import pytest

from masar.core.models import SplitBoundary
from masar.verification.split_editor import HeuristicBoundaryGuard, SplitEditor


def test_bleed_repair_and_diff_artifact(test_artifacts_dir: Path):
    """Verify detection of boundary bleed (CRF noise) and repair via dual token-anchor editor."""
    full_text = (
        "حدثنا يحيى بن قزعة حدثنا مالك عن يحيى بن سعيد عن محمد بن إبراهيم بن الحارث عن علقمة بن وقاص عن عمر رضي الله عنه "
        "قال قال رسول الله صلى الله عليه وسلم إنما الأعمال بالنية وإنما لامرئ ما نوى"
    )

    # Corrupted CRF boundary: matn starts at the isnad connector, capturing "قال قال رسول الله صلى الله عليه وسلم"
    corrupted_matn_start = full_text.index("قال قال رسول الله")
    corrupted_matn_end = len(full_text)
    corrupted_boundary = SplitBoundary(
        matn_start=corrupted_matn_start,
        matn_end=corrupted_matn_end,
    )

    corrupted_matn = full_text[corrupted_matn_start:corrupted_matn_end]
    assert "قال قال رسول الله" in corrupted_matn

    # Step 1: Detect Bleed
    guard = HeuristicBoundaryGuard()
    diag = guard.detect_bleed(corrupted_matn)

    assert diag.has_bleed is True
    assert diag.detected_prefix is not None

    # Step 2: Repair Split using SplitEditor
    editor = SplitEditor()
    repaired_boundary = editor.repair_split(full_text, corrupted_boundary)

    # Verification:
    repaired_matn = full_text[repaired_boundary.matn_start : repaired_boundary.matn_end].strip()
    assert not repaired_matn.startswith("قال قال رسول الله")
    assert repaired_matn.startswith("إنما الأعمال بالنية")
    assert repaired_boundary.pre_matn_token == "وسلم"
    assert repaired_boundary.post_isnad_token == "إنما"

    # Verify that repaired matn no longer has bleed
    diag_repaired = guard.detect_bleed(repaired_matn)
    assert diag_repaired.has_bleed is False

    # Terminate by generating verifiable artifact
    artifact_path = test_artifacts_dir / "bleed_repair_diff.json"
    artifact_payload = {
        "scenario": "FM-01 Boundary Bleed Repair",
        "full_text": full_text,
        "corrupted_boundary": corrupted_boundary.model_dump(),
        "corrupted_matn": corrupted_matn,
        "bleed_diagnostic": diag.model_dump(),
        "repaired_boundary": repaired_boundary.model_dump(),
        "repaired_matn": repaired_matn,
        "diff": {
            "start_offset_delta": repaired_boundary.matn_start - corrupted_boundary.matn_start,
            "removed_bleed_text": full_text[corrupted_boundary.matn_start : repaired_boundary.matn_start].strip(),
        },
    }
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(artifact_payload, f, ensure_ascii=False, indent=2)

    assert artifact_path.exists()
    assert artifact_path.stat().st_size > 0
