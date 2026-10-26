# Masar Agent Operating Model

This document is the control-plane view of Masar (مسار). It describes the system in the form most useful to an AI agent that must understand current state, choose the correct intervention point, preserve scholarly and textual ground truth, and execute with minimal context consumption, zero ambiguity, and maximum precision.

---

## 1. The System as a Tower of Linked Abstractions

Masar is an ordered sequence of semantic commitments. Each layer consumes a lower primitive layer and derives higher analytical meaning, but must never silently rewrite or destroy the integrity of its inputs.

| Layer | Meaning | Canonical Owner | Rebuildable? | Critical Invariant |
| :--- | :--- | :--- | :--- | :--- |
| **L0 Substrate** | Raw corpus text (`riwayat-corpus`, custom JSON/CSV/SQLite files, or manual text entries), character indices, provenance metadata | `corpus_adapter.py`, `corpus_db.py`, `manual_entry.py` | No | Immutable; never mutate raw corpus files |
| **L1 Signals** | Normalized Arabic tokens, BM25 indices, sliding pericope alignments, dense embeddings, isnad hub graphs | `discovery/*` | Yes from L0 | Orthogonal metrics; explainability receipts must record all 4 signals |
| **L2 Hypothesis** | Candidate parallel traditions, similarity rank, false-positive quarantine | `hybrid_engine.py` | Yes from L1 | Topical similarity without pericope or isnad overlap is quarantined |
| **L3 Curation** | Isnad/matn boundary split states, persistent corrections, session event log | `verification/*`, `accretive_store.py` | Overrides are durable | Human/agent verified boundaries override noisy CRF model defaults permanently |
| **L4 Control** | Single-hop CLI commands, compact token-thrifty projections, explainability receipts, session undo | `cli.py`, `models.py` | Yes | Triage queries output < 300 tokens; every action is atomic and reversible |
| **L5 Interop** | Canonical Riwaq `import-batch.json` (`schema_version: 1`), preflight gates | `export/*`, `preflight_gates.py` | Yes from L3 | Zero schema defects; identical `family_id` across all records in a batch |

The web workbench is an interaction projection across L2–L4. It is not a separate truth source.

---

## 2. The Three Agent Dimensions

### 2.1 Agent Legibility (Intuitive Mental Model)
- **Unidirectional Abstraction Flow**: Meaning flows strictly from $L_0 \to L_5$. Downstream layers never silently back-patch upstream primitives.
- **Strict Authority Lattice**: Conflicts are resolved by:
  1. *Owning source code + closest behavioral tests*
  2. *Local contract documentation (`docs/ARCHITECTURE.md`)*
  3. *Cross-layer operating model (`docs/AGENT-OPERATING-MODEL.md`)*
  4. *Active project status (`docs/STATUS.md`)*
  5. *Durable architectural decisions (`docs/DECISIONS.md`)*
  6. *Context & background (`context.md`)*
- **Typed Control Semantics (§4)**: Signals are explicitly categorized as *observations*, *blocking preconditions*, *candidate hypotheses*, *curated ground truth*, or *publication gates*.

### 2.2 Agent Ergonomics (Optimal Control & Minimal Token Spend)
- **Token-Thrifty Projections (`--compact`)**: Triage output presents tabular results with essential metrics only, consuming under 300 tokens instead of exhausting context with tens of thousands of raw Arabic words.
- **Single-Hop Machine Control**: An agent inspects, filters, adjusts boundaries, stages bundles, and ingests manual or custom data via deterministic CLI commands (`masar search`, `masar inspect`, `masar split`, `masar bundle`, `masar add`, `masar ingest`).
- **Explainability Receipts**: Every ranked result includes an immutable mathematical decomposition ($S_{lex}, S_{peric}, S_{sem}, S_{isnad}$), allowing the agent to instantly diagnose false positives without multi-turn archaeology.
- **Minimal-Read Envelope (§6)**: Context budgeting rules dictate reading only the owning file plus at most one upstream dependency and one test fixture.

### 2.3 Agent Accretion (Compounding Knowledge & Persistent Flywheel)
- **The Accretive Store (`masar-curated.db`)**: Every split boundary correction performed by an agent or researcher is permanently indexed. Future queries automatically consult this store, continuously elevating the quality of the 925K corpus.
- **Reversible Event-Sourced Journal**: All session operations (`ADD_VARIANT`, `EXCLUDE_VARIANT`, `ADJUST_SPLIT`) append to an immutable log with SHA-256 proofs, supporting atomic undo/redo.
- **Zero Knowledge Drift**: `docs/DECISIONS.md` records all durable constraints; `docs/STATUS.md` records real-time verified capabilities.

---

## 3. Three Independent State Axes

Agents must never conflate these three independent state dimensions:

1. **Retrieval Consensus State**: `high_confidence_parallel`, `fragment_match` (Taqṭīʿ), `synonym_variant` (Riwāyah bi-l-Maʿnā), or `quarantined_topic` (Topic Trap).
2. **Boundary Curation State**: `unverified_crf` (noisy default), `bleed_detected` (heuristic warning), `agent_verified`, or `human_verified`.
3. **Preflight Gate State**: `gate_pass` (ready for Riwaq export) or `gate_blocked` (fails schema, family, hygiene, or isnad checks).

A variant can have a high semantic retrieval score while remaining in `bleed_detected` status. A curated variant can belong to a bundle that is blocked at the preflight gate due to a missing companion anchor.

---

## 4. Control-Semantics Taxonomy

Every signal in the system is strictly typed:

| Signal Type | Answers | Examples | May Block Export? |
| :--- | :--- | :--- | :--- |
| **Observation** | What did the engine measure? | BM25 score, cosine similarity, Jaccard overlap, token count | No |
| **Warning** | What potential defect was detected? | `bleed_detected`, `ambiguous_homonym`, `low_isnad_overlap` | No (requires review) |
| **Hypothesis** | What historical relationship is inferred? | `parallel_branch`, `taqtic_fragment`, `topical_false_positive` | No |
| **Curated Fact** | What ground-truth decision was committed? | `matn_start: 142`, `isnad_chain: [102, 45, 12]` | No |
| **Blocking Precondition**| May this operation execute? | Valid SQLite connection, valid search query | Yes, for that operation |
| **Publication Gate** | May this bundle be exported to Riwaq? | `PreflightValidator.validate()` | Yes, blocks export |

---

## 5. Canonical Data Flow

```text
1. Seed Input (Text, ID, or Companion Anchor)
      │
      ▼
2. Multi-Signal Retrieval (L1)
   ├── FTS5 BM25 (Lexical)
   ├── Sliding Pericope Window (Taqṭīʿ)
   ├── Dense Embedding Cosine (Riwāyah bi-l-Maʿnā)
   └── Isnad Hub Graph Traversal
      │
      ▼
3. Candidate Scoring & Explainability Receipts (L2)
   ├── Calculate composite consensus score
   ├── Quarantine topical false positives
   └── Output compact Agent Lens table (< 300 tokens)
      │
      ▼
4. Boundary Verification & Accretion (L3)
   ├── Heuristic Boundary Guard checks for isnad bleed
   ├── Agent/User adjusts character offsets (SplitEditor)
   ├── Correction saved to persistent `masar-curated.db`
   └── Action recorded in event-sourced session journal
      │
      ▼
5. Bundle Assembly & Preflight Validation (L4-L5)
   ├── Assign uniform `family_id`
   ├── Execute 4 Preflight Gates (Schema, Family, Hygiene, Isnad)
   └── Emit Riwaq `import-batch.json` (`schema_version: 1`)
```

---

## 6. Minimal-Read Envelope for Agents

To minimize context consumption and prevent cognitive overload, follow these minimal-read boundaries:

| Task Class | Read Set (Only read these files) |
| :--- | :--- |
| **Normalization / Tokenization** | `src/masar/core/normalizer.py`, `tests/unit/test_normalizer.py` |
| **Corpus Adapters & Manual Entry** | `src/masar/core/corpus_adapter.py`, `src/masar/core/manual_entry.py`, `tests/e2e/test_e2e_manual_entry.py` |
| **Database & Corpus Queries** | `src/masar/core/corpus_db.py`, `tests/unit/test_corpus_db.py` |
| **Lexical Search (FTS5)** | `src/masar/discovery/fts_search.py`, `tests/unit/test_fts_search.py` |
| **Pericope Alignment (Taqṭīʿ)** | `src/masar/discovery/pericope_aligner.py`, `tests/e2e/test_e2e_taqtic.py` |
| **Semantic Matching** | `src/masar/discovery/semantic_search.py`, `tests/unit/test_semantic_search.py` |
| **Hybrid Ranking & Triage** | `src/masar/discovery/hybrid_engine.py`, `tests/e2e/test_e2e_topic_trap.py` |
| **Boundary Split & Bleed Guard**| `src/masar/verification/split_editor.py`, `tests/e2e/test_e2e_bleed_repair.py` |
| **Accretive Ground Truth** | `src/masar/verification/accretive_store.py`, `tests/unit/test_accretive_store.py` |
| **Agent CLI** | `src/masar/cli.py`, `tests/unit/test_cli.py` |
| **Riwaq Preflight Gates** | `src/masar/export/preflight_gates.py`, `tests/e2e/test_e2e_riwaq_gate.py`, `schemas/riwaq-import-batch.json` |

---

## 7. Diagnostic Routing: Question → Artifact

| Question | Owning Artifact / Command |
| :--- | :--- |
| "Why was this hadith ranked #1?" | `masar inspect --id <hadith_id> --receipt` (Explainability Receipt) |
| "Why was candidate X excluded?" | `test-artifacts/topical_quarantine_report.json` or `masar inspect --id <id> --status` |
| "Does this record contain isnad bleed?"| `SplitEditor.check_bleed()` or `masar inspect --id <id> --field bleed` |
| "What was the previous session state?"| `masar session history` |
| "Is this bundle ready for Riwaq?" | `masar bundle validate --family-id <family_id>` (Preflight Gates) |
| "How do I ingest custom data or a manual text?" | `masar ingest --source <path>` or `masar add --text <arabic_text>` |
| "What are the active failure modes?" | `docs/ARCHITECTURE.md` §3 (Failure-Mode First Matrix) |
