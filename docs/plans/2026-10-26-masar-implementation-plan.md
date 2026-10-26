# Masar (مسار) Master Implementation Plan: Agent-Ergonomic Hadith Takhrīj Engine

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Announced:** I'm using the `writing-plans` and `architecture` skills to create this comprehensive, agent-centric implementation plan.

---

## 1. System Vision: The Agent in the Driver's Seat

Masar (مسار) is architected as an **Agent-Ergonomic, Agent-Intuitive, and Agent-Accretive Synthetic System**. It is designed so that an autonomous coding/research agent can operate it with maximum situational awareness, minimal token expenditure, and zero-defect execution.

```
                           THE TOWER OF LINKED ABSTRACTIONS
┌──────────────────────────────────────────────────────────────────────────────────┐
│ LAYER 5: ECOSYSTEM INTEROP & PREFLIGHT GATES                                     │
│ • Riwaq schema_version: 1 serializer • Deterministic Gate Checkers (Zero-Defect) │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼─────────────────────────────────────────┐
│ LAYER 4: AGENT CONTROL PLANE & ERGONOMICS (THE AGENT LENS)                       │
│ • Token-Thrifty Compact Views (--compact) • Explainability Receipts (Receipts)   │
│ • Append-Only Session Journal (Undo/Redo) • Atomic Machine-Callable Actions      │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼─────────────────────────────────────────┐
│ LAYER 3: VERIFICATION, SPLIT REMEDIATION & KNOWLEDGE ACCRETION                  │
│ • Two-Stage "Discovery vs. Canonical" Architecture • 1-Click Boundary Adjuster   │
│ • Accretive Ground-Truth Store (Persistent Curated Overrides)                    │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼─────────────────────────────────────────┐
│ LAYER 2: TRADITION HYPOTHESIS & BUNDLE STATE MACHINE                             │
│ • Family Bundle Aggregate (family_id) • Variant Typology (Primary, Fragment, etc)│
│ • Multi-Signal Consensus Score Matrix                                            │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼─────────────────────────────────────────┐
│ LAYER 1: ORTHOGONAL SIGNAL DECOMPOSITION                                         │
│ • Lexical (BM25) • Pericope Alignment (Jaccard) • Semantic Dense Vectors        │
│ • Isnad Topology & Hub Anchoring (Common Link Graphs)                            │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼─────────────────────────────────────────┐
│ LAYER 0: CORPUS SUBSTRATE & REPRESENTATION                                       │
│ • Normalized Arabic Orthography • SQLite FTS5 Virtual Tables • Raw Corpora       │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Enforced Testing Rules & Harness Requirements

All development across all phases MUST strictly adhere to these testing rules:
1. **Failure-mode first**: Before writing implementation code, articulate the failure mode and scenario; write the test that catches that failure.
2. **High-value E2E / Integration tests first**: Primary verification is done via end-to-end pipelines against medium-to-hard hadith scenarios (e.g. cross-sectarian transmission, complex taqṭīʿ, CRF boundary bleed).
3. **Repeatable, verifiable artifacts**: Every E2E test must terminate by writing an inspectable artifact to `test-artifacts/` (e.g. serialized batch JSON, diff dumps, gate validation logs).
4. **Unit tests selectively**: Pure logic only (Arabic normalization, sliding window alignment, schema serialization). Never as change-detector mirrors.
5. **No tautological tests & no change-detector tests**: Tests must verify behavioral contracts, not internal implementation syntax.
6. **Bug-fix regression mandate**: Every fix must start with a regression test failing on pre-fix code.

---

## 3. Technology Stack & Architectural Baseline

- **Runtime & Language**: Python 3.11+
- **Agent CLI & Control Interface**: `masar` CLI powered by `typer` / `click` with `--compact`, `--format json`, `--receipts`.
- **Search & Storage**:
  - `corpus_index.db`: Read-only SQLite FTS5 with custom Arabic normalization.
  - `masar_workspaces.db`: Read-write SQLite session journal and accretive curated overrides.
- **NLP & Alignment**:
  - `pyarabic` / custom Unicode regex normalizer.
  - ONNX / FastEmbed (`paraphrase-multilingual-MiniLM-L12-v2` or Arabic-specialized ONNX model) for local CPU embeddings.
- **API & Workbench UI**:
  - FastAPI headless backend for external agents and UI.
  - Vite + React + Tailwind CSS interactive workbench with side-by-side split adjuster.
- **Interop Target**:
  - Riwaq `schema_version: 1` (`import-batch.json` and `hadith-record.json`).

---

## 4. Repository File Decomposition

```text
masar/
├── pyproject.toml                     # Dependencies, scripts (masar CLI), pytest config
├── context.md                         # Foundational domain specifications
├── docs/
│   ├── ARCHITECTURE.md                # System conceptual architecture & failure modes
│   ├── SKILLPACK_ROUTING.md           # Skills audit & routing record
│   └── plans/
│       └── 2026-10-26-masar-implementation-plan.md
├── schemas/
│   ├── riwaq-import-batch.json        # Synced Riwaq schema_version: 1
│   └── riwaq-hadith-record.json       # Synced Riwaq HadithRecord schema
├── test-artifacts/                    # Generated test verification receipts (ignored in git)
├── src/
│   ├── masar/
│   │   ├── __init__.py
│   │   ├── cli.py                     # Agent-First CLI (masar search, inspect, split, export)
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── normalizer.py          # Arabic text & diacritic normalization (pure logic)
│   │   │   ├── models.py              # Pydantic V2 models (Internal, Receipts, Riwaq)
│   │   │   ├── corpus_adapter.py      # Generic CorpusAdapter interface (Agnostic storage)
│   │   │   ├── corpus_db.py           # SQLite adapter for riwayat-corpus
│   │   │   └── manual_entry.py        # Manual record ingestion & heuristic boundary proposal
│   │   ├── discovery/
│   │   │   ├── __init__.py
│   │   │   ├── fts_search.py          # BM25 search via SQLite FTS5
│   │   │   ├── pericope_aligner.py    # Substring Jaccard sliding window (taqṭīʿ)
│   │   │   ├── semantic_search.py     # Dense vector similarity (riwāyah bi-l-maʿnā)
│   │   │   ├── isnad_filter.py        # Transmitter hub / Companion anchoring
│   │   │   └── hybrid_engine.py       # Multi-signal ensemble & explainability receipts
│   │   ├── verification/
│   │   │   ├── __init__.py
│   │   │   ├── session_store.py       # Event-sourced workspace journal (undo/redo)
│   │   │   ├── accretive_store.py     # Persistent curated overrides (masar-curated.db)
│   │   │   └── split_editor.py        # Boundary adjustment & heuristic bleed guard
│   │   ├── export/
│   │   │   ├── __init__.py
│   │   │   ├── riwaq_exporter.py      # Riwaq import-batch.json builder
│   │   │   └── preflight_gates.py     # 4 Deterministic validation gates (Schema, Family, etc)
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── app.py                 # FastAPI application
│   │       └── routes.py              # Agent-ergonomic REST endpoints
│   └── web/                           # Vite + React Verification Workbench
│       ├── package.json
│       ├── vite.config.ts
│       └── src/
│           ├── App.tsx
│           ├── components/
│           │   ├── QueryBar.tsx
│           │   ├── CandidateList.tsx
│           │   ├── DiffViewer.tsx
│           │   ├── SplitEditor.tsx
│           │   └── ExportModal.tsx
│           └── api/client.ts
└── tests/
    ├── conftest.py                    # Multi-sectarian hadith fixtures & mock databases
    ├── e2e/
    │   ├── test_e2e_bleed_repair.py   # FM-01: Boundary Bleed E2E
    │   ├── test_e2e_taqtic.py         # FM-04: Taqṭīʿ alignment E2E
    │   ├── test_e2e_cross_sect.py     # FM-05: Cross-sectarian takhrij E2E
    │   ├── test_e2e_topic_trap.py     # FM-03: Topical false positive rejection E2E
    │   ├── test_e2e_riwaq_gate.py     # FM-06: Riwaq preflight gate validation E2E
    │   ├── test_e2e_manual_entry.py   # FM-07: Manual text entry & heuristic split E2E
    │   └── test_e2e_custom_corpus.py  # FM-07: Custom JSON/CSV corpus ingestion E2E
    └── unit/
        ├── test_normalizer.py         # Pure logic: Arabic diacritics & ligatures
        ├── test_models.py             # Schema serialization & receipt integrity
        └── test_pericope_aligner.py   # Sliding window Jaccard mathematics
```

---

## 5. Detailed Task Breakdown & Implementation Protocol

### Phase 1: Core Substrate, Arabic Normalizer & Data Contracts
*Objective: Build the foundational text normalization, Pydantic contracts, and corpus database abstraction.*

#### Task 1.1: Project Tooling & Test Harness Setup
- **Failure Mode / Scenario**: Inconsistent environments, broken import paths, or untracked test artifacts.
- **Files**: `pyproject.toml`, `tests/conftest.py`, `src/masar/__init__.py`
- [ ] Step 1: Write `pyproject.toml` specifying `fastapi`, `uvicorn`, `pydantic>=2.5`, `pytest`, `jsonschema`, `numpy`, `typer`, `rich`.
- [ ] Step 2: Configure `tests/conftest.py` with multi-sectarian test fixtures (including Bukhari, Muslim, and al-Kāfī samples with known boundary errors).
- [ ] Step 3: Run `pytest` to confirm test harness boots cleanly.
- [ ] Step 4: Commit.

#### Task 1.2: Arabic Normalization Substrate (Pure Logic Unit Test)
- **Failure Mode / Scenario**: Search fails or calculates inaccurate Jaccard overlap because of diacritics (tashkeel), inconsistent alif spelling (`أ`, `إ`, `آ`), ta marbuta vs ha (`ة`/`ه`), or tatweel (`ـ`).
- **Files**: `src/masar/core/normalizer.py`, `tests/unit/test_normalizer.py`
- [ ] Step 1: Write failing unit tests in `tests/unit/test_normalizer.py`:
  - Stripping all Quranic/Arabic harakat, shaddah, sukun, tanween.
  - Normalizing alifs to bare `ا`, alif maqsura `ى` to `ي`, ta marbuta `ة` to `ه`.
  - Normalizing honorific ligatures (`ﷺ`, `رضي الله عنه`).
- [ ] Step 2: Run `pytest tests/unit/test_normalizer.py` (verify failure).
- [ ] Step 3: Implement `normalize_arabic(text: str) -> str` and `tokenize_arabic(text: str) -> list[str]` in `normalizer.py`.
- [ ] Step 4: Run `pytest tests/unit/test_normalizer.py` (verify 100% pass).
- [ ] Step 5: Check cyclomatic complexity (must be <= 8, flat loops).
- [ ] Step 6: Commit.

#### Task 1.3: Data Contracts & Explainability Receipts
- **Failure Mode / Scenario**: Incompatible JSON serialization or loss of explanation provenance during discovery.
- **Files**: `src/masar/core/models.py`, `tests/unit/test_models.py`
- [ ] Step 1: Write failing tests verifying that Pydantic models validate Riwaq `import-batch.json` and generate `ExplainabilityReceipt` objects.
- [ ] Step 2: Implement models: `CandidateRecord`, `ExplainabilityReceipt`, `SplitState`, `ImportBatch`, `HadithRecord`, `IsnadVariant`.
- [ ] Step 3: Run `pytest tests/unit/test_models.py` (verify pass).
- [ ] Step 4: Commit.

#### Task 1.4: Pluggable Corpus Database Interface & Riwayat Adapter
- **Failure Mode / Scenario**: Tightly coupling to `riwayat-corpus` schema prevents querying custom collections or unindexed books; memory blowout when querying 925K records; failure to respect sectarian scoping flags (`all`, `sunni`, `shia`).
- **Files**: `src/masar/core/corpus_adapter.py`, `src/masar/core/corpus_db.py`, `tests/unit/test_corpus_db.py`
- [ ] Step 1: Define `CorpusAdapter` protocol with abstract methods (`get_record`, `query_candidates`, `list_collections`).
- [ ] Step 2: Write integration test: load sample SQLite database, query hadiths by collection, filter by sect, retrieve narrator chains via `RiwayatCorpusAdapter`.
- [ ] Step 3: Implement `RiwayatCorpusAdapter` implementing `CorpusAdapter` with indexed queries, generator streaming (zero memory bloat), and sectarian filters.
- [ ] Step 4: Run test and verify query response time < 50ms.
- [ ] Step 5: Commit.

#### Task 1.5: First-Class Manual Entry & Custom Dataset Ingestion (Solving FM-07)
- **Failure Mode / Scenario**: Pasted raw manuscript text lacks isnad/matn split boundaries, causing matn pollution or missing narrator chains; custom JSON/CSV hadith datasets cannot be imported into the workspace.
- **Files**: `src/masar/core/manual_entry.py`, `tests/e2e/test_e2e_manual_entry.py`, `tests/e2e/test_e2e_custom_corpus.py`
- [ ] Step 1: Write failing E2E test `test_e2e_manual_entry.py`:
  - Input: Raw unsegmented Arabic report with citation metadata ("حدثنا مسدد قال حدثنا يحيى عن شعبة عن قتادة عن أنس قال قال رسول الله...").
  - Test heuristic boundary detector: verifies proposed `matn_start` index cleanly isolates the isnad formula.
  - Test confirmation: stages manual record into active workspace with valid `source_ref` (`source_type: "print"`).
  - Verify artifact output in `test-artifacts/manual_entry_verified.json`.
- [ ] Step 2: Write failing E2E test `test_e2e_custom_corpus.py`:
  - Ingest custom JSON/CSV file containing 50 traditions from a rare regional manuscript.
  - Verify `CustomFileCorpusAdapter` indexes them for FTS search and parallel variant discovery.
- [ ] Step 3: Implement `ManualEntryPipeline` (with heuristic splitter) and `CustomFileCorpusAdapter`.
- [ ] Step 4: Run tests and verify 100% pass.
- [ ] Step 5: Commit.

---

### Phase 2: Multi-Signal Discovery Engine & Explainability
*Objective: Build high-recall retrieval combining BM25, pericope alignment, dense semantic embeddings, and isnad anchoring.*

#### Task 2.1: Lexical FTS5 Engine
- **Failure Mode / Scenario**: Classical text keyword searches fail due to missing morphological matches or slow full-table scans.
- **Files**: `src/masar/discovery/fts_search.py`
- [ ] Step 1: Write failing test querying normalized matn via SQLite FTS5 table with phrase queries and boolean operators.
- [ ] Step 2: Implement `FtsSearchEngine` with automated virtual table indexing on `normalized_matn`.
- [ ] Step 3: Verify BM25 score generation and sub-millisecond retrieval.
- [ ] Step 4: Commit.

#### Task 2.2: Pericope Sliding-Window Aligner (Solving FM-04: Taqṭīʿ)
- **Failure Mode / Scenario**: A 2-line cited excerpt is missed because whole-hadith Jaccard score is < 0.10.
- **Files**: `src/masar/discovery/pericope_aligner.py`, `tests/e2e/test_e2e_taqtic.py`
- [ ] Step 1: Write failing E2E test `test_e2e_taqtic.py`: feed a 12-token excerpt against a 140-token hadith from Sahih Muslim. Assert that the sliding-window aligner identifies the exact substring span with alignment score > 0.85.
- [ ] Step 2: Implement `PericopeAligner.align(seed_tokens, target_tokens, window_step=1)` with sliding window Jaccard calculation.
- [ ] Step 3: Run `pytest tests/e2e/test_e2e_taqtic.py`.
- [ ] Step 4: Assert artifact written to `test-artifacts/taqtic_alignment_dump.json`.
- [ ] Step 5: Commit.

#### Task 2.3: Dense Semantic Embeddings (Solving Riwāyah bi-l-Maʿnā)
- **Failure Mode / Scenario**: Lexical search misses parallel reports due to complete synonym substitution (e.g., *dhahaba* vs *inṭalaqa*).
- **Files**: `src/masar/discovery/semantic_search.py`
- [ ] Step 1: Write failing test: compare two synonymous Arabic sentences with zero token overlap; assert cosine similarity > 0.70.
- [ ] Step 2: Implement `SemanticMatcher` with pluggable local ONNX / FastEmbed backend and vector caching.
- [ ] Step 3: Verify test passes and CPU inference takes < 80ms per batch.
- [ ] Step 4: Commit.

#### Task 2.4: Isnad & Authority Hub Anchoring
- **Failure Mode / Scenario**: Sifting through thousands of topical matches without knowing if they originate from the same Companion or Common Link.
- **Files**: `src/masar/discovery/isnad_filter.py`
- [ ] Step 1: Write failing test: given a list of candidate variants, detect if they converge on a shared authority (e.g. ʿUmar ibn al-Khaṭṭāb) or 2nd-century hub (al-Zuhrī).
- [ ] Step 2: Implement `IsnadAnchorFilter.score_chain_overlap(seed_chain, candidate_chain)`.
- [ ] Step 3: Verify test passes.
- [ ] Step 4: Commit.

#### Task 2.5: Hybrid Engine, Explainability Receipts & Topic Trap Quarantining (Solving FM-03)
- **Failure Mode / Scenario**: Topical false positives (different traditions discussing the same topic) pollute the bundle.
- **Files**: `src/masar/discovery/hybrid_engine.py`, `tests/e2e/test_e2e_topic_trap.py`
- [ ] Step 1: Write failing E2E test `test_e2e_topic_trap.py`: query seed *Hadith al-Niyyah*; inject unrelated tradition on *Niyyah*; assert hybrid engine flags the unrelated tradition as `TOPICAL_FALSE_POSITIVE` due to lack of pericope overlap and zero isnad convergence.
- [ ] Step 2: Implement `HybridTakhrijEngine` emitting composite score and `ExplainabilityReceipt` per candidate.
- [ ] Step 3: Run `pytest tests/e2e/test_e2e_topic_trap.py`.
- [ ] Step 4: Assert artifact written to `test-artifacts/topical_quarantine_report.json`.
- [ ] Step 5: Commit.

---

### Phase 3: Verification Layer, Accretive Store & Agent CLI
*Objective: Empower the agent to inspect candidates with minimal tokens, adjust noisy boundaries, and persist curated ground truth.*

#### Task 3.1: Boundary Split Editor & Heuristic Bleed Guard (Solving FM-01)
- **Failure Mode / Scenario**: CRF parser mistakenly places narrator names or *ḥaddathanā* into the matn.
- **Files**: `src/masar/verification/split_editor.py`, `tests/e2e/test_e2e_bleed_repair.py`
- [ ] Step 1: Write failing E2E test `test_e2e_bleed_repair.py`: load a corrupted hadith record where the first 5 words of matn contain isnad formulas. Assert that `HeuristicBoundaryGuard` detects the bleed and `SplitEditor` cleanly adjusts the character slice.
- [ ] Step 2: Implement `SplitEditor` and `HeuristicBoundaryGuard`.
- [ ] Step 3: Run `pytest tests/e2e/test_e2e_bleed_repair.py`.
- [ ] Step 4: Assert artifact written to `test-artifacts/bleed_repair_diff.json`.
- [ ] Step 5: Commit.

#### Task 3.2: Accretive Ground Truth Store (Persistent Flywheel)
- **Failure Mode / Scenario**: Manual boundary adjustments are lost when the session ends, forcing the agent to repeat work on future runs.
- **Files**: `src/masar/verification/accretive_store.py`
- [ ] Step 1: Write failing test: adjust split for `hadith_id: bukhari-1`; save to accretive store; perform fresh query; assert that retrieved candidate automatically applies curated boundary.
- [ ] Step 2: Implement SQLite-backed `AccretiveStore` (`masar-curated.db`).
- [ ] Step 3: Verify test passes.
- [ ] Step 4: Commit.

#### Task 3.3: Event-Sourced Session Journal (Reversible Agent Actions)
- **Failure Mode / Scenario**: Agent hallucinates or applies an incorrect boundary split without any undo capability.
- **Files**: `src/masar/verification/session_store.py`
- [ ] Step 1: Write failing test: create session, apply 3 boundary changes, execute undo, verify state reverts cleanly to step 2.
- [ ] Step 2: Implement `SessionJournal` with immutable event log and rollback support.
- [ ] Step 3: Verify test passes.
- [ ] Step 4: Commit.

#### Task 3.4: Agent-First CLI (`masar`)
- **Failure Mode / Scenario**: Agent must make brittle HTTP calls or inspect complex JSON to perform basic takhrīj operations; inability to manually add an external hadith or ingest a custom file from terminal.
- **Files**: `src/masar/cli.py`
- [ ] Step 1: Write failing CLI tests for:
  - `masar search --seed <text> --scope all --compact` (must return compact ASCII table under 300 tokens).
  - `masar inspect --id <hadith_id> --receipt` (must output JSON explainability receipt).
  - `masar split --id <hadith_id> --start <offset> --end <offset>`.
  - `masar add --text <arabic_text> --collection <str> --ref <str>` (manual entry CLI).
  - `masar ingest --source <path> --format [json|csv|sqlite]` (custom file ingestion CLI).
  - `masar session undo`.
- [ ] Step 2: Implement CLI commands using `typer` and `rich`.
- [ ] Step 3: Verify CLI tests pass with zero regression.
- [ ] Step 4: Commit.

---

### Phase 4: Riwaq Export Engine & Preflight Verification Gates
*Objective: Guarantee zero-defect export to Riwaq with 100% schema compliance.*

#### Task 4.1: Four Deterministic Preflight Gates (Solving FM-06)
- **Failure Mode / Scenario**: Invalid JSON format, mismatched `family_id`, or empty isnad chains break downstream Riwaq ICMA analysis.
- **Files**: `src/masar/export/preflight_gates.py`, `tests/e2e/test_e2e_riwaq_gate.py`
- [ ] Step 1: Write failing E2E test `test_e2e_riwaq_gate.py`:
  - Test Case A: Valid bundle passes all 4 gates with 0 errors.
  - Test Case B: Bundle with missing `family_id` is blocked with exact error: `GATE_FAMILY_CONSISTENCY: missing family_id`.
  - Test Case C: Bundle with isnad introductory formula in matn is blocked with: `GATE_BOUNDARY_HYGIENE: narrator formula in matn`.
- [ ] Step 2: Implement `PreflightValidator` executing:
  - `GateSchema` (draft-07 against `schemas/riwaq-import-batch.json`).
  - `GateFamilyConsistency` (single family_id, >= 2 variants).
  - `GateBoundaryHygiene` (checks matn for isnad contamination).
  - `GateIsnadIntegrity` (non-empty ordered narrator chains).
- [ ] Step 3: Run `pytest tests/e2e/test_e2e_riwaq_gate.py`.
- [ ] Step 4: Assert artifact written to `test-artifacts/riwaq_preflight_pass.json`.
- [ ] Step 5: Commit.

#### Task 4.2: Riwaq Batch Serializer
- **Files**: `src/masar/export/riwaq_exporter.py`
- [ ] Step 1: Write test assembling 15 verified variants into a canonical `import-batch.json` payload.
- [ ] Step 2: Implement `RiwaqExporter.export_bundle(session_id: str, family_id: str) -> dict`.
- [ ] Step 3: Verify exported JSON passes `jsonschema.validate()`.
- [ ] Step 4: Commit.

#### Task 4.3: End-to-End Multi-Sectarian Takhrīj Pipeline (Solving FM-05)
- **Failure Mode / Scenario**: Takhrīj fails when bridging Sunni and Shīʿī collections due to transmission formula asymmetries.
- **Files**: `tests/e2e/test_e2e_cross_sect.py`
- [ ] Step 1: Write failing E2E test:
  1. Input seed: *Hadith al-Thaqalayn* / *Hadith al-Ghadir*.
  2. Search cross-sectarian scope (`scope=all`).
  3. Retrieve parallels from Sahih Muslim, Sunan al-Tirmidhi, and al-Kāfī.
  4. Perform boundary curation on 1 Shīʿī record and 1 Sunni record.
  5. Run preflight gates; verify 100% pass.
  6. Export batch; verify valid `schema_version: 1` output.
- [ ] Step 2: Run `pytest tests/e2e/test_e2e_cross_sect.py`.
- [ ] Step 3: Assert artifact written to `test-artifacts/cross_sectarian_family.json`.
- [ ] Step 4: Commit.

---

### Phase 5: Verification Workbench Web UI & API Service
*Objective: Deliver the human-in-the-loop and web interface for visual boundary adjustments.*

#### Task 5.1: FastAPI REST Service
- **Files**: `src/masar/api/app.py`, `src/masar/api/routes.py`
- [ ] Step 1: Write integration tests for API routes (`/api/search`, `/api/hadith/{id}`, `/api/split`, `/api/export`).
- [ ] Step 2: Implement FastAPI app with CORS and OpenAPI docs.
- [ ] Step 3: Verify all endpoints pass with valid JSON responses.
- [ ] Step 4: Commit.

#### Task 5.2: Verification Workbench Web Application
- **Files**: `src/web/src/App.tsx`, `src/web/src/components/*`
- [ ] Step 1: Build `QueryBar` with Arabic input and Sunni/Shīʿī toggles.
- [ ] Step 2: Build `CandidateList` displaying explainability badges and confidence scores.
- [ ] Step 3: Build `SplitEditor` allowing 1-click boundary repositioning.
- [ ] Step 4: Build `ManualEntryModal` allowing direct pasting of Arabic text, citation metadata entry, and heuristic split preview.
- [ ] Step 5: Build `ExportModal` with one-click "Download Riwaq JSON" and "Copy Batch" actions.
- [ ] Step 6: Test in browser / headless test and verify smooth interaction.

---

## 6. Preflight Gates & Acceptance Criteria

Before claiming completion of any phase or shipping the system, the following criteria MUST be met:
- [ ] All 7 Failure-Mode E2E tests in `tests/e2e/` pass with green output.
- [ ] Every E2E test has produced a verified, inspectable artifact in `test-artifacts/`.
- [ ] The `masar` CLI is fully functional and supports `--compact` agent-lens views, `masar add` manual entry, and `masar ingest`.
- [ ] Generated batch JSON files validate 100% against `schemas/riwaq-import-batch.json` (`schema_version: 1`).
- [ ] Codebase passes cyclomatic complexity checks (no function > 10 complexity; flat control flow).
- [ ] Zero tautological or change-detector tests.
