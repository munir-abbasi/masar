# Masar Agent Guide

This file contains project-specific facts, invariants, and operating constraints for agents working in this repository. General agent behavior belongs in the user's global policy.

## Orientation

- **Product**: Masar (مسار), a high-precision, agent-ergonomic Hadith Takhrīj (variant discovery and bundling) engine.
- **Ecosystem Role**: Upstream feeder for **Riwaq** (Isnad-cum-Matn Analysis engine). Masar identifies, aligns, and bundles variant traditions into verified `family_id` bundles; Riwaq analyzes stemmas, CL/PCLs, and matn apparatuses.
- **Core Technology**: Python 3.11+, SQLite (FTS5 + JSON1), FastEmbed/ONNX (CPU dense embeddings), FastAPI, Typer (`masar` CLI), and Vite/React for the verification workbench.
- **Primary CLI**: `masar` (`src/masar/cli.py`) with `--compact`, `--format json`, and `--receipts`.
- **Authoritative Schemas**:
  - Ingestion & Corpus: `src/masar/core/models.py`.
  - Downstream Interop: `schemas/riwaq-import-batch.json` and `schemas/riwaq-hadith-record.json` (`schema_version: 1`).
- **Persistent Accretion Store**: `masar-curated.db` (stores verified boundaries, narrator corrections, and false-positive quarantines).

## Read Path

For any non-trivial change, read in this order:

1. This file (`AGENTS.md`).
2. `docs/AGENT-OPERATING-MODEL.md` — The Abstraction Tower ($L_0 \to L_5$), control-semantics taxonomy, and minimal-read set for your change class.
3. The owning source and closest test for the layer being changed.
4. `docs/DECISIONS.md` when an architectural decision constrains the change.

For **current runtime behavior**, source plus the closest tests outrank prose. `docs/AGENT-OPERATING-MODEL.md` routes across layers; `docs/STATUS.md` records mutable state; `docs/DECISIONS.md` records durable architectural intent. If these disagree, record a contradiction and repair it deliberately (never rewrite prose to paper over broken code).

## System Invariants

- **Discovery ≠ Canonical Ground Truth**: Raw scraped corpora (`riwayat-corpus`, ~925K records) are low-stakes, high-recall search indices only. Automated CRF parser boundaries (Tier C 68%–88% accuracy) must never be treated as authoritative ground truth without verification.
- **Orthogonal Signal Decomposition**: Every candidate search score must be decomposed into its 4 independent signals (Lexical BM25, Pericope Jaccard, Semantic Cosine, Isnad Hub overlap) via an immutable `ExplainabilityReceipt`.
- **Topical False Positive Quarantine**: High semantic embedding similarity without pericope overlap or isnad convergence must be quarantined as `TOPICAL_FALSE_POSITIVE` and must never pollute a tradition bundle.
- **Accretive Knowledge**: Every human or agent boundary split adjustment must be permanently recorded in `masar-curated.db` so future corpus queries automatically inherit verified boundaries.
- **Reversible Agent Execution**: All session actions (`ADD`, `PRUNE`, `SPLIT`) must be recorded in an append-only, event-sourced journal supporting single-step rollback (`masar session undo`).
- **Token-Thrifty Observability (Agent Lens)**: Triage queries must support a `--compact` mode returning high-density output under 300 tokens; full text and diff matrices are progressive disclosures on explicit request only.
- **Deterministic Preflight Publication Gate**: A candidate bundle cannot be exported to Riwaq unless it passes all 4 deterministic gates (`GateSchema`, `GateFamilyConsistency`, `GateBoundaryHygiene`, `GateIsnadIntegrity`).
- **Zero Downstream Compensation**: Never compensate in Riwaq for an upstream boundary defect. Fix the split in Masar, record it in the accretive store, and export clean data.

### Invariant → Enforcement Evidence

| Invariant | Enforced in | Proven by |
| :--- | :--- | :--- |
| Raw corpus is index-only; CRF splits unverified | `src/masar/core/corpus_db.py` | `tests/unit/test_corpus_db.py` |
| Decomposed score & Explainability Receipts | `src/masar/discovery/hybrid_engine.py` | `tests/unit/test_models.py` |
| Topical False Positives Quarantined | `src/masar/discovery/hybrid_engine.py` | `tests/e2e/test_e2e_topic_trap.py` |
| Taqṭīʿ (fragmentation) detected & aligned | `src/masar/discovery/pericope_aligner.py` | `tests/e2e/test_e2e_taqtic.py` |
| Accretive boundary overrides persistent | `src/masar/verification/accretive_store.py` | `tests/e2e/test_e2e_bleed_repair.py` |
| Reversible session journal & undo | `src/masar/verification/session_store.py` | `tests/unit/test_session_store.py` |
| Token-thrifty agent CLI projections | `src/masar/cli.py` | `tests/unit/test_cli.py` |
| Riwaq schema_version: 1 preflight gate | `src/masar/export/preflight_gates.py` | `tests/e2e/test_e2e_riwaq_gate.py` |
| Cross-sectarian takhrij parity | `src/masar/discovery/hybrid_engine.py` | `tests/e2e/test_e2e_cross_sect.py` |

## Source Ownership

| Concern | Primary Source of Truth |
| :--- | :--- |
| Arabic Orthography Normalization | `src/masar/core/normalizer.py` |
| Data Contracts & Explainability Models | `src/masar/core/models.py` |
| Corpus Database Adapter & Sectarian Scoping | `src/masar/core/corpus_db.py` |
| Lexical BM25 Search (FTS5) | `src/masar/discovery/fts_search.py` |
| Pericope Alignment (Taqṭīʿ) | `src/masar/discovery/pericope_aligner.py` |
| Dense Vector Semantic Similarity | `src/masar/discovery/semantic_search.py` |
| Isnad Hub Anchoring & Common Links | `src/masar/discovery/isnad_filter.py` |
| Multi-Signal Ensemble & Triage | `src/masar/discovery/hybrid_engine.py` |
| Boundary Split Editor & Bleed Guard | `src/masar/verification/split_editor.py` |
| Accretive Ground Truth Store | `src/masar/verification/accretive_store.py` |
| Event-Sourced Workspace Journal | `src/masar/verification/session_store.py` |
| Preflight Verification Gates | `src/masar/export/preflight_gates.py` |
| Riwaq ImportBatch Serializer | `src/masar/export/riwaq_exporter.py` |
| Agent Control CLI | `src/masar/cli.py` |
| REST API Endpoints | `src/masar/api/routes.py` |
| Verification Workbench UI | `src/web/src/App.tsx` |
