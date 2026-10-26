# Masar (مسار)

**High-Precision, Agent-Ergonomic Hadith Takhrīj & Variant Bundling Engine**

Masar bridges unbundled hadith corpora (such as [**riwayat-corpus**](https://github.com/abdullahansara/riwayat-corpus) with ~925,000 records, custom JSON/CSV collections, and raw manuscript transcriptions) into verified, gate-checked `family_id` bundles. While Masar functions as a fully autonomous, standalone takhrīj workbench and variant discovery engine, it also serves as the native upstream feeder for [**Riwaq**](https://github.com/munir-abbasi/riwaq) (the Isnad-cum-Matn Analysis and stemma engine), guaranteeing 100% schema compliance (`schema_version: 1`) and protecting downstream ICMA analysis against boundary bleed, homonym traps, and topical false positives.

---

## Key Features

- **Orthogonal 4-Signal Takhrīj Discovery**: Decomposes candidate matching confidence into 4 independent signals—Lexical BM25, Sliding-Window Pericope Jaccard (*Taqṭīʿ*), Dense Semantic Cosine (*Riwāyah bi-l-Maʿnā*), and Isnad Authority Overlap.
- **Explainability Receipts**: Every candidate hadith emitted during discovery carries an immutable `ExplainabilityReceipt` documenting raw and normalized signal scores and alignment spans.
- **Topical False Positive Quarantine (Topic Trap Guard)**: Candidates with high semantic similarity discussing the same topic without pericope overlap or isnad convergence are quarantined automatically as `TOPICAL_FALSE_POSITIVE`.
- **Accretive Read-Through Overlay (`masar-curated.db`)**: Ground-truth boundary split repairs and narrator corrections persist in an accretive SQLite store. Base scraped corpora (such as [**riwayat-corpus**](https://github.com/abdullahansara/riwayat-corpus)) remain 100% immutable while queries automatically inherit verified boundaries.
- **Reversible Agent Workspace Journal**: Every action (`ADD`, `PRUNE`, `SPLIT`, `STAGE`) is recorded in an append-only, event-sourced journal supporting single-step rollback (`masar session undo`).
- **Corpus Agnosticism & First-Class Manual Entry**: Ingest raw manuscript snippets or printed texts using heuristic isnad/matn split detection, ingest external datasets via `CustomFileCorpusAdapter`, or query standard SQLite archives like [**riwayat-corpus**](https://github.com/abdullahansara/riwayat-corpus).
- **AI Proposal Staging Buffer & Drift Guard**: Agent-generated boundary splits and variant groupings pass through a typed staging buffer (`ProposalStore`) with SHA-256 operation receipts before committing to curated ground truth.
- **Four Deterministic Preflight Gates**: Pre-export validation enforcing `GateSchema`, `GateFamilyConsistency`, `GateBoundaryHygiene`, and `GateIsnadIntegrity` before generating Riwaq `import-batch.json` bundles.
- **Multi-Modal Agent Interfaces**: Token-thrifty machine CLI (`masar --compact` < 300 tokens), native Model Context Protocol (MCP) JSON-RPC stdio server (`masar mcp`), headless REST API, and Vite + React interactive workbench.

---

## Tech Stack

- **Runtime & Language**: Python 3.11+
- **Database & Search**: SQLite3 with FTS5 virtual tables and JSON1 extensions
- **Data Validation & Contracts**: Pydantic V2 & JSON Schema (Draft-07)
- **Agent CLI**: Typer & Rich
- **Agent Protocol**: Model Context Protocol (MCP) JSON-RPC 2.0 stdio server
- **REST Backend**: FastAPI & Uvicorn
- **Verification Workbench**: React 18, TypeScript, Vite
- **Downstream Target (Optional)**: Riwaq `schema_version: 1` (`import-batch.json` & `hadith-record.json`)

---

## Prerequisites

- **Python**: Version 3.11, 3.12, or 3.13 (or [`uv`](https://github.com/astral-sh/uv))
- **Node.js**: Version 18+ and npm (only needed for the verification workbench web UI)

---

## Getting Started

### 1. Clone & Set Up Python Environment

```bash
git clone https://github.com/your-org/masar.git
cd masar

# Using uv (recommended)
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Or using standard pip
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Verify Test Suite & Artifacts

Run the exhaustive test suite verifying all 8 failure-mode scenarios:

```bash
pytest -v
```

All 55 tests should pass in < 2 seconds, producing repeatable verification artifacts in `test-artifacts/`.

---

## Usage Guide

### 1. Agent CLI (`masar`)

The `masar` CLI is optimized for both human researchers and autonomous agents:

```bash
# Token-thrifty search triage (< 300 tokens for LLM context efficiency)
masar search --db corpus.db --seed "إنما الأعمال بالنيات" --compact

# Multi-modal search returning structured JSON with Explainability Receipts
masar search --db corpus.db --seed "إنما الأعمال بالنيات" --format json --receipts

# Inspect hadith text, isnad chain, and boundary status
masar inspect --db corpus.db --id 1

# Repair an isnad/matn split and persist to accretive overlay (masar-curated.db)
masar split --db corpus.db --id 4 --start 149 --end 187

# Ingest an ad-hoc manuscript excerpt with heuristic boundary splitting
masar add --text "حدثنا يحيى قال قال رسول الله صلى الله عليه وسلم إنما الأعمال بالنيات" \
          --collection "Berlin MS 402" \
          --ref "Folio 12b" \
          --family "fam_niyyah_ms"

# Revert the last operation in the workspace
masar session undo
```

### 2. Model Context Protocol (MCP) Server

Masar provides a native stdio MCP server for agent harnesses (Antigravity, Claude Desktop, Cursor, OpenCode, Hermes):

```bash
masar mcp --db corpus.db
```

#### Available MCP Tools

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `masar_search` | `seed` (str), `scope` (`all`\|`sunni`\|`shia`), `limit` (int) | Multi-signal takhrīj search emitting Explainability Receipts. |
| `masar_inspect` | `hadith_id` (str) | Detailed text, parsed isnad chain, and boundary status. |
| `masar_adjust_split` | `hadith_id` (str), `start` (int), `end` (int) | Adjusts split and persists override to `masar-curated.db`. |
| `masar_add_manual` | `text` (str), `collection` (str), `ref` (str), `family_id` (str) | Stages unsegmented text with heuristic split detection. |
| `masar_diagnose` | *(none)* | Cross-layer system health and database statistics. |

### 3. REST API Service

Launch the headless FastAPI backend:

```bash
uvicorn masar.api.app:create_app --factory --port 8000 --reload
```

- Interactive OpenAPI Swagger documentation: `http://localhost:8000/docs`
- Key endpoints:
  - `POST /api/search` — Query candidates across Sunni/Shīʿī corpora.
  - `GET /api/hadith/{id}` — Fetch resolved hadith record via accretive overlay.
  - `POST /api/split` — Submit boundary split correction.
  - `POST /api/export` — Assemble and preflight-verify Riwaq `import-batch.json`.
  - `GET /api/diagnose` — Machine health triage.

### 4. Verification Workbench Web Application

Launch the Vite + React verification workbench:

```bash
cd src/web
npm install
npm run dev
```

Open `http://localhost:5173` to visually inspect candidates, adjust isnad/matn split sliders with real-time text slices, quarantine false positives, and export bundles directly to Riwaq.

---

## System Architecture

```text
       +------------------------------------------------------------------+
       |               Layer 5: Presentation & Interop Interfaces         |
       |     CLI (`masar`)  |  MCP Server  |  FastAPI  |  Vite + React    |
       +---------------------------------+--------------------------------+
                                         |
       +---------------------------------v--------------------------------+
       |               Layer 4: Export Engine & Preflight Gates           |
       |  GateSchema | GateFamilyConsistency | GateBoundary | GateIsnad   |
       +---------------------------------+--------------------------------+
                                         |
       +---------------------------------v--------------------------------+
       |               Layer 3: Verification & Accretive Knowledge        |
       |  AccretiveStore (masar-curated.db)  |  SessionJournal (undo)     |
       |  SplitEditor (Dual Anchors)         |  ProposalStore (AI Staging)|
       +---------------------------------+--------------------------------+
                                         |
       +---------------------------------v--------------------------------+
       |               Layer 2: Multi-Signal Discovery Engine             |
       |  BM25 FTS5  |  Pericope Jaccard  |  Dense Cosine | Isnad Anchors|
       |                 --> Explainability Receipts <--                  |
       +---------------------------------+--------------------------------+
                                         |
       +---------------------------------v--------------------------------+
       |               Layer 1: Corpus Ingestion & Adapters               |
       |   RiwayatCorpusAdapter  |  CustomFileCorpusAdapter  |  Manual    |
       +---------------------------------+--------------------------------+
                                         |
       +---------------------------------v--------------------------------+
       |               Layer 0: Arabic Text Normalization                 |
       |       Tashkeel Stripping  |  Alif/Ta Normalization | Tokenizer   |
       +------------------------------------------------------------------+
```

### The Read-Through Overlay Pattern

```text
Corpus Query (ID: 4)
       │
       ▼
AccretiveStore Check ─────────[Found in masar-curated.db?]
       │                                     │
       │ YES (Overridden)                    │ NO (Clean)
       ▼                                     ▼
Apply Curated Boundary Slice          Read Raw Base Corpus
(Clean Matn & Trimmed Isnad)          (Immutable SQLite Archive)
       │                                     │
       └──────────────────┬──────────────────┘
                          │
                          ▼
            Resolved Candidate Record
```

*The underlying base corpus (e.g. [**riwayat-corpus**](https://github.com/abdullahansara/riwayat-corpus)) remains strictly read-only; all human and agent boundary repairs shadow it accretively via `masar-curated.db`.*

---

## Tested Failure Modes & Enforcement Matrix

Masar is engineered failure-mode first. Every critical risk is guarded by automated integration and E2E tests:

| Failure Mode ID | Scenario Name | Guard Mechanism | Test Suite | Verified Artifact |
| :--- | :--- | :--- | :--- | :--- |
| **FM-01** | Boundary Bleed Repair | Dual token anchors & `HeuristicBoundaryGuard` | `tests/e2e/test_e2e_bleed_repair.py` | `test-artifacts/bleed_repair_diff.json` |
| **FM-02** | Homonym Trap | Prosopographical student-teacher edge verification | `tests/e2e/test_e2e_homonym_disambig.py` | `test-artifacts/homonym_audit_log.json` |
| **FM-03** | Topical False Positive | Automatic quarantine for high semantic / low isnad matches | `tests/e2e/test_e2e_topic_trap.py` | `test-artifacts/topical_quarantine_report.json` |
| **FM-04** | Taqṭīʿ Alignment | Sliding-window pericope Jaccard matcher | `tests/e2e/test_e2e_taqtic.py` | `test-artifacts/taqtic_alignment_dump.json` |
| **FM-05** | Cross-Sectarian Parity | Symmetric Sunni & Shīʿī multi-signal scoring | `tests/e2e/test_e2e_cross_sect.py` | `test-artifacts/cross_sectarian_family.json` |
| **FM-06** | Riwaq Gate Rejection | 4 deterministic preflight gates | `tests/e2e/test_e2e_riwaq_gate.py` | `test-artifacts/riwaq_preflight_pass.json` |
| **FM-07** | Manual Entry Ingestion | Heuristic isnad/matn transition detection | `tests/e2e/test_e2e_manual_entry.py` | `test-artifacts/manual_entry_verified.json` |
| **FM-08** | AI Proposal Drift | Isolated staging buffer with SHA-256 receipts | `tests/e2e/test_e2e_ai_staging.py` | `test-artifacts/ai_proposal_staged.json` |

---

## Repository Structure

```text
masar/
├── pyproject.toml                     # Python dependencies, scripts, and build configuration
├── README.md                          # Comprehensive technical and developer documentation
├── AGENTS.md                          # Agent operating guide, system invariants, and read paths
├── context.md                         # Domain background on hadith takhrīj & riwayat-corpus
├── docs/
│   ├── ARCHITECTURE.md                # System architecture, abstraction tower, and failure modes
│   ├── DECISIONS.md                   # Permanent Architecture Decision Record (ADR) ledger (D001-D015)
│   ├── STATUS.md                      # Live capability triage and tested failure mode matrix
│   └── plans/                         # Phased implementation master plans
├── schemas/
│   ├── riwaq-import-batch.json        # Synced Riwaq schema_version: 1 contract
│   └── riwaq-hadith-record.json       # Synced Riwaq HadithRecord schema
├── skills/
│   └── masar-takhrij/
│       └── SKILL.md                   # Reusable agent skill specification
├── src/
│   ├── masar/
│   │   ├── cli.py                     # Typer CLI (`masar search`, `inspect`, `split`, `undo`, `mcp`)
│   │   ├── mcp_server.py              # Native Model Context Protocol stdio server
│   │   ├── agent_control.py           # Machine projections (manifest, snapshot, diagnose)
│   │   ├── core/
│   │   │   ├── normalizer.py          # Arabic orthography and diacritic normalization
│   │   │   ├── models.py              # Pydantic V2 models & explainability receipts
│   │   │   ├── corpus_adapter.py      # Pluggable CorpusAdapter & CustomFileCorpusAdapter
│   │   │   ├── corpus_db.py           # SQLite adapter for riwayat-corpus
│   │   │   └── manual_entry.py        # Heuristic isnad/matn split detector and ingestion
│   │   ├── discovery/
│   │   │   ├── fts_search.py          # SQLite FTS5 BM25 lexical engine
│   │   │   ├── pericope_aligner.py    # Sliding-window Jaccard aligner (taqṭīʿ)
│   │   │   ├── semantic_search.py     # Dense vector similarity matcher (riwāyah bi-l-maʿnā)
│   │   │   ├── isnad_filter.py        # Isnad chain overlap & homonym disambiguation
│   │   │   └── hybrid_engine.py       # Multi-signal ensemble & Topic Trap quarantine
│   │   ├── verification/
│   │   │   ├── split_editor.py        # Dual anchor-offset split editor & bleed guard
│   │   │   ├── accretive_store.py     # Curated overlay store (masar-curated.db)
│   │   │   ├── session_store.py       # Event-sourced session journal with rollback
│   │   │   └── proposal_store.py      # AI proposal staging buffer & drift guard
│   │   ├── export/
│   │   │   ├── preflight_gates.py     # 4 Deterministic validation gates
│   │   │   └── riwaq_exporter.py      # Riwaq ImportBatch serializer
│   │   └── api/
│   │       ├── app.py                 # FastAPI application factory
│   │       └── routes.py              # REST endpoints for search, split, and export
│   └── web/                           # Vite + React Verification Workbench
│       ├── package.json
│       ├── vite.config.ts
│       ├── index.html
│       └── src/
│           ├── App.tsx                # Workbench main view
│           ├── api/client.ts          # REST client communicating with FastAPI
│           └── components/            # QueryBar, CandidateList, SplitEditor, ExportModal
├── test-artifacts/                    # Generated E2E verification receipts (FM-01 through FM-08)
└── tests/
    ├── conftest.py                    # Multi-sectarian SQLite test database fixture
    ├── e2e/                           # High-value E2E failure mode test suites
    └── unit/                          # Targeted pure-logic unit test suites
```

---

## Downstream Ecosystem Integration: Riwaq (Optional)

> [!NOTE]
> **Masar is fully autonomous and does not require Riwaq to function.** All multi-signal discovery, pericope alignment (*taqṭīʿ*), accretive boundary split editing, false positive quarantining, manual text ingestion, CLI operations, and the interactive verification workbench operate 100% locally and standalone. Riwaq is strictly an optional downstream consumer for researchers who wish to conduct automated Isnad-cum-Matn Analysis (ICMA) and stemma tree generation on verified bundles.

When paired with [**Riwaq**](https://github.com/munir-abbasi/riwaq) (Isnad-cum-Matn Analysis & Stemma Engine), the workflow functions as follows:

1. **Discovery & Verification (Masar — Standalone)**: Discovers, verifies, and bundles candidate variants across Sunni and Shīʿī collections into a unified family bundle.
2. **Preflight Gating (Masar — Standalone)**: Validates boundary hygiene, family consistency, and schema compliance.
3. **ICMA Analysis (Riwaq — Downstream Consumer)**: Ingests the exported `import-batch.json`, maps transmitter networks into a Directed Acyclic Graph (DAG), computes Common Links (CL) and Partial Common Links (PCL), and generates formal academic ICMA reports.

---

## License

MIT License.
