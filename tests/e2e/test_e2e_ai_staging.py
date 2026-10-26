"""E2E Test: AI Proposal Staging Buffer and Drift Guard (FM-08, ADR D015)."""

import json
from pathlib import Path
import pytest

from masar.core.corpus_db import RiwayatCorpusAdapter
from masar.core.models import SplitBoundary
from masar.verification.accretive_store import AccretiveStore
from masar.verification.proposal_store import ProposalStore, ProposalStatus


def test_ai_proposal_staging_and_drift_guard(mock_db_path, tmp_path: Path, test_artifacts_dir: Path):
    """Verify AI proposal lifecycle: staging buffer, preflight gating, and safe commit to curated overlay."""
    curated_db = tmp_path / "masar-curated.db"
    staging_db = tmp_path / "staging_buffer.db"

    curated_store = AccretiveStore(curated_db)
    proposal_store = ProposalStore(staging_db, curated_store)

    # 1. Invalid Proposal (Hallucination Drift): inverted boundary coordinates
    invalid_prop_id = proposal_store.stage_split_proposal(
        hadith_id="4",
        matn_start=200,
        matn_end=100,  # Invalid: end < start!
        agent_id="subagent_drift_test",
        rationale="Hallucinated inverted slice",
    )
    assert invalid_prop_id is not None
    inv_res = proposal_store.evaluate_proposal(invalid_prop_id)
    assert inv_res.status == ProposalStatus.REJECTED
    assert inv_res.rejection_reason is not None

    # Assert invalid proposal never reached curated overlay
    assert curated_store.get_boundary_override("4") is None

    # 2. Valid Proposal: clean split repair for record 4
    valid_boundary = SplitBoundary(
        matn_start=149,
        matn_end=187,
        pre_matn_token="وسلم",
        post_isnad_token="إنما",
    )
    valid_prop_id = proposal_store.stage_split_proposal(
        hadith_id="4",
        matn_start=149,
        matn_end=187,
        pre_matn_token="وسلم",
        post_isnad_token="إنما",
        agent_id="subagent_verified",
        rationale="Trimmed isnad connector bleed",
    )
    assert valid_prop_id.startswith("prop_")

    eval_res = proposal_store.evaluate_proposal(valid_prop_id)
    assert eval_res.status == ProposalStatus.PREFLIGHT_PASSED
    assert eval_res.sha256_receipt is not None

    # Commit approved proposal
    commit_ok = proposal_store.commit_proposal(valid_prop_id)
    assert commit_ok is True

    # 3. Verify curated overlay now reflects the approved proposal
    override = curated_store.get_boundary_override("4")
    assert override is not None
    assert override.matn_start == 149
    assert override.matn_end == 187

    # 4. Generate verifiable artifact
    artifact_path = test_artifacts_dir / "ai_proposal_staged.json"
    artifact_payload = {
        "scenario": "FM-08 AI Proposal Staging & Drift Guard",
        "invalid_proposal": {
            "proposal_id": invalid_prop_id,
            "status": inv_res.status.value,
            "rejection_reason": inv_res.rejection_reason,
        },
        "valid_proposal": {
            "proposal_id": valid_prop_id,
            "status": eval_res.status.value,
            "sha256_receipt": eval_res.sha256_receipt,
            "boundary": valid_boundary.model_dump(),
        },
        "curated_override_verified": override.model_dump(),
    }
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(artifact_payload, f, ensure_ascii=False, indent=2)

    assert artifact_path.exists()
    assert artifact_path.stat().st_size > 0
