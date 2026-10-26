"""E2E Test: Pericope sliding-window alignment for fragmented hadiths / Taqṭīʿ (FM-04)."""

import json
from pathlib import Path
import pytest
from masar.discovery.pericope_aligner import PericopeAligner, PericopeMatch


def test_taqtic_fragment_alignment_and_artifact(test_artifacts_dir: Path):
    """Verify that a short hadith fragment (taqṭīʿ) is accurately aligned against a long tradition."""
    # 1. Target: Full Bukhari 1 tradition matn
    full_target_matn = (
        "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى فمن كانت هجرته إلى دنيا يصيبها "
        "أو إلى امرأة ينكحها فهجرته إلى ما هاجر إليه"
    )

    # 2. Seed excerpt: Fragment citing only the migration/marriage clause (Bukhari 54)
    seed_fragment = "فمن كانت هجرته إلى دنيا يصيبها أو امرأة ينكحها فهجرته إلى ما هاجر إليه"

    aligner = PericopeAligner()
    match = aligner.align(seed_text=seed_fragment, target_text=full_target_matn)

    # Verification:
    # A naive whole-text Jaccard will be diluted because full_target_matn has the first half "إنما الأعمال بالنيات..."
    assert isinstance(match, PericopeMatch)
    assert match.max_jaccard >= 0.85, f"Expected high local alignment, got {match.max_jaccard}"
    assert match.global_jaccard < match.max_jaccard, "Global Jaccard must be lower than pericope Jaccard"
    assert "امرأة ينكحها" in match.matched_snippet or "امراه ينكحها" in match.matched_snippet

    # Write verifiable artifact
    artifact_path = test_artifacts_dir / "taqtic_alignment_dump.json"
    artifact_payload = {
        "scenario": "FM-04 Taqṭīʿ Pericope Alignment",
        "seed_fragment": seed_fragment,
        "full_target_matn": full_target_matn,
        "max_jaccard": match.max_jaccard,
        "global_jaccard": match.global_jaccard,
        "start_token_idx": match.start_token_idx,
        "end_token_idx": match.end_token_idx,
        "matched_snippet": match.matched_snippet,
    }
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(artifact_payload, f, ensure_ascii=False, indent=2)

    assert artifact_path.exists()
    assert artifact_path.stat().st_size > 0
