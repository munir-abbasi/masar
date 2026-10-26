"""E2E Test: Prosopographical Homonym Disambiguation (FM-02)."""

import json
from pathlib import Path
import pytest
from masar.discovery.isnad_filter import HomonymDisambiguator


def test_homonym_disambiguation_and_audit_artifact(test_artifacts_dir: Path):
    """Verify that ambiguous transmitter names like 'sufyan' are disambiguated by student-teacher context."""
    disambiguator = HomonymDisambiguator()

    # Case 1: Sufyan with student al_humaydi -> resolved to Sufyan ibn Uyaynah
    chain_humaydi = ["al_humaydi", "sufyan", "yahya_b_said"]
    resolved_1, warnings_1 = disambiguator.disambiguate_chain(chain_humaydi)

    assert "sufyan_b_uyaynah" in resolved_1
    assert "sufyan" not in resolved_1
    assert len(warnings_1) == 0

    # Case 2: Sufyan with student waki -> resolved to Sufyan al-Thawri
    chain_waki = ["waki", "sufyan", "mansur"]
    resolved_2, warnings_2 = disambiguator.disambiguate_chain(chain_waki)

    assert "sufyan_al_thawri" in resolved_2
    assert "sufyan" not in resolved_2
    assert len(warnings_2) == 0

    # Case 3: Ambiguous Sufyan with no distinguishing student/teacher edges -> emits warning
    chain_ambiguous = ["unknown_student", "sufyan", "unknown_teacher"]
    resolved_3, warnings_3 = disambiguator.disambiguate_chain(chain_ambiguous)

    assert len(warnings_3) > 0
    assert "Ambiguous transmitter" in warnings_3[0]

    # Terminate by generating verifiable artifact
    artifact_path = test_artifacts_dir / "homonym_audit_log.json"
    artifact_payload = {
        "scenario": "FM-02 Homonym Trap Disambiguation",
        "cases_tested": [
            {
                "input_chain": chain_humaydi,
                "resolved_chain": resolved_1,
                "warnings": warnings_1,
                "attribution": "Sufyan ibn Uyaynah (via al-Humaydi edge)",
            },
            {
                "input_chain": chain_waki,
                "resolved_chain": resolved_2,
                "warnings": warnings_2,
                "attribution": "Sufyan al-Thawri (via Waki edge)",
            },
            {
                "input_chain": chain_ambiguous,
                "resolved_chain": resolved_3,
                "warnings": warnings_3,
                "attribution": "Unresolved (Ambiguous warning emitted)",
            },
        ],
    }
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(artifact_payload, f, ensure_ascii=False, indent=2)

    assert artifact_path.exists()
    assert artifact_path.stat().st_size > 0
