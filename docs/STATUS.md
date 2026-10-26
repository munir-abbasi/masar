# Masar System Status & Capability Triage

Current as of: 2026-10-26

## 1. System Capability Triage

| Subsystem | State | Health | Primary Owner | Critical Gates Passed |
| :--- | :--- | :--- | :--- | :--- |
| **Core Substrate** | Operational | 🟢 Verified Phase 1 | `src/masar/core/` | Schema, Adapter, Ingestion |
| **Arabic Normalization** | Operational | 🟢 Verified Phase 1 | `normalizer.py` | Diacritic, Ligature, Tokenizer |
| **Multi-Signal Discovery**| In-Design / Planned | 🟡 Pending Phase 2 | `discovery/` | - |
| **Verification & Split** | In-Design / Planned | 🟡 Pending Phase 3 | `verification/` | - |
| **Accretive Store** | In-Design / Planned | 🟡 Pending Phase 3 | `accretive_store.py` | - |
| **Agent CLI (`masar`)** | In-Design / Planned | 🟡 Pending Phase 3 | `cli.py` | - |
| **Model Context Protocol (MCP)** | In-Design / Planned | 🟡 Pending Phase 3 | `mcp_server.py` | - |
| **Proposal Staging Buffer** | In-Design / Planned | 🟡 Pending Phase 3 | `proposal_store.py` | - |
| **Riwaq Preflight Gates**| In-Design / Planned | 🟡 Pending Phase 4 | `preflight_gates.py` | - |
| **Workbench Web UI** | In-Design / Planned | 🟡 Pending Phase 5 | `src/web/` | - |

---

## 2. Tested Failure Modes (E2E Verification Matrix)

| Failure Mode ID | Scenario Name | Test Target | Status | Artifact Target |
| :--- | :--- | :--- | :--- | :--- |
| **FM-01** | Boundary Bleed Repair | `tests/e2e/test_e2e_bleed_repair.py` | ⏳ Pending Phase 3 | `test-artifacts/bleed_repair_diff.json` |
| **FM-02** | Homonym Disambiguation | `tests/e2e/test_e2e_homonym_disambig.py` | ⏳ Pending Phase 2 | `test-artifacts/homonym_audit_log.json` |
| **FM-03** | Topical False Positive Quarantine | `tests/e2e/test_e2e_topic_trap.py` | ⏳ Pending Phase 2 | `test-artifacts/topical_quarantine_report.json` |
| **FM-04** | Taqṭīʿ Fragment Alignment | `tests/e2e/test_e2e_taqtic.py` | ⏳ Pending Phase 2 | `test-artifacts/taqtic_alignment_dump.json` |
| **FM-05** | Cross-Sectarian Takhrīj Parity | `tests/e2e/test_e2e_cross_sect.py` | ⏳ Pending Phase 4 | `test-artifacts/cross_sectarian_family.json` |
| **FM-06** | Riwaq Schema Preflight Gate | `tests/e2e/test_e2e_riwaq_gate.py` | ⏳ Pending Phase 4 | `test-artifacts/riwaq_preflight_pass.json` |
| **FM-07** | Manual Entry & Custom Ingestion | `tests/e2e/test_e2e_manual_entry.py` | 🟢 Passed | `test-artifacts/manual_entry_verified.json` |
| **FM-08** | AI Proposal Staging & Drift Guard | `tests/e2e/test_e2e_ai_staging.py` | ⏳ Pending Phase 3 | `test-artifacts/ai_proposal_staged.json` |

---

## 3. Known Project Constraints & Technical Facts

1. **Schema Authority**: Downstream Riwaq's inline validator in `json-validator.js` requires `schema_version: 1`, `family_id` alphanumeric pattern `^[a-zA-Z0-9_-]+$`, and structured `source_ref` (`collection`, `source_type`, `source_locator`, `ingested_at`).
2. **Corpus Footprint**: Full `riwayat-corpus` SQLite archive is ~925,000 hadiths. Test suites use a curated mock fixture (`tests/fixtures/mock_hadiths.db`) containing multi-sectarian test records to run tests in < 5 seconds.
3. **CPU-First Embedding Requirement**: To preserve portability on developer and agent environments, embeddings must operate via local CPU ONNX runtime without demanding GPU/CUDA setups.
