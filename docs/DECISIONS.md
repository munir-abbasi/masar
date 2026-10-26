# Masar Architecture Decisions (ADR Ledger)

This document is the permanent architectural ledger for Masar (مسار). It records durable decisions, trade-offs, and invariants to prevent architectural drift.

---

### D001: Two-Stage "Discovery vs. Canonical" Architecture
- **Status**: Accepted
- **Context**: `riwayat-corpus` (~925K records) was aggregated from uncollated digital scrapes with significant OCR errors, and 214,000 Tier-C hadiths were segmented using an automated CRF model with only 68%–88% whole-chain accuracy. Treating this data as canonical ground truth would corrupt Riwaq's downstream ICMA stemma generation.
- **Decision**: Architect Masar into two distinct stages:
  1. *Stage 1 (Discovery Engine)*: Low-stakes, high-recall search index over the 925K corpus.
  2. *Stage 2 (Verification Layer)*: High-precision, human/agent-in-the-loop curation workbench where boundaries and variants are verified before canonical bundling.
- **Consequences**: Downstream Riwaq never ingests unverified CRF boundaries.

---

### D002: Dual SQLite Storage (Corpus Index vs. Curated Accretion)
- **Status**: Accepted
- **Context**: We need blazing fast search over 925K records while maintaining durable storage for user sessions and curated boundary corrections, with zero DevOps overhead (no PostgreSQL, Redis, or Elasticsearch clusters required).
- **Decision**: Split persistence into two SQLite databases:
  1. `corpus_index.db`: Read-only connection to `riwayat-corpus` (`hadith_master.db`), augmented with an SQLite FTS5 virtual table.
  2. `masar-curated.db`: Read-write SQLite store holding persistent boundary overrides, narrator corrections, and the event-sourced session journal.
- **Consequences**: Runs locally on developer laptops and headless agent containers with zero configuration. Curated boundary corrections survive session restarts and compound over time.

---

### D003: Multi-Signal Ensemble & Explainability Receipts
- **Status**: Accepted
- **Context**: Classical hadith transmission involves both lexical exactness, synonym substitutions (*riwāyah bi-l-maʿnā*), partial quotations (*taqṭīʿ*), and transmission chains. Single-signal search (BM25 alone or dense embeddings alone) fails: BM25 misses synonyms, while dense embeddings conflate different hadiths on the same topic.
- **Decision**: Combine 4 orthogonal signals into a composite score:
  $$\text{Score} = w_{lex} \cdot S_{BM25} + w_{peric} \cdot S_{jaccard} + w_{sem} \cdot S_{cosine} + w_{isnad} \cdot S_{hub}$$
  Every candidate match must return an immutable `ExplainabilityReceipt` documenting all 4 sub-scores.
- **Consequences**: Agents and researchers can immediately see *why* a report was retrieved.

---

### D004: Event-Sourced Session Journal & Reversible Execution
- **Status**: Accepted
- **Context**: Autonomous agents and researchers iteratively refine tradition bundles. A destructive error (e.g. accidental pruning or bad split) should never require restarting the session from scratch.
- **Decision**: Implement an append-only event-sourced journal for all session mutations (`ADD_VARIANT`, `EXCLUDE_VARIANT`, `ADJUST_SPLIT`). Support single-hop `masar session undo` and rollback.
- **Consequences**: Zero risk of unrecoverable session states. Complete audit trail of who/what changed a boundary.

---

### D005: Deterministic Preflight Gates for Riwaq Interop
- **Status**: Accepted
- **Context**: Riwaq requires strict adherence to `schema_version: 1` (`import-batch.json`). Downstream analysis breaks if a batch has inconsistent `family_id`s, empty narrator chains, or narrator formulas inside `matn_raw`.
- **Decision**: Implement 4 hard preflight gates (`GateSchema`, `GateFamilyConsistency`, `GateBoundaryHygiene`, `GateIsnadIntegrity`). Export is blocked until all 4 gates return 100% pass.
- **Consequences**: Zero invalid JSON or malformed batches reach Riwaq.

---

### D006: Agent-First CLI with Token-Thrifty Tiered Projections
- **Status**: Accepted
- **Context**: Outputting 50 raw hadiths in chat context wastes 25,000+ tokens and causes context dilution for the driving agent.
- **Decision**: The `masar` CLI must provide tiered outputs:
  - Triage queries with `--compact` return a high-density ASCII table under 300 tokens.
  - Deep-dive text and diff matrices are progressive disclosures on explicit `--id <hadith_id>` requests only.
- **Consequences**: Dramatic reduction in agent token expenditure and near-instant reasoning cycles.

---

### D007: ONNX / FastEmbed Local CPU Embedding Architecture
- **Status**: Accepted
- **Context**: Large PyTorch/CUDA embedding models introduce massive installation footprints (>2GB), slow cold starts, and hardware dependencies.
- **Decision**: Use ONNX Runtime or FastEmbed (`paraphrase-multilingual-MiniLM-L12-v2` or Arabic-specialized ONNX models) for local, quantization-friendly CPU embeddings with local vector caching.
- **Consequences**: Zero GPU required; sub-80ms batch embedding inference on standard CPU.

---

### D008: Sliding-Window Pericope Alignment for Taqṭīʿ
- **Status**: Accepted
- **Context**: Classical compilers frequently quote only a 1- or 2-line legal excerpt of a 20-line tradition (*taqṭīʿ*). Standard whole-string Jaccard or Levenshtein distance collapses to near zero (< 0.10).
- **Decision**: Implement a sliding-window token alignment algorithm that scans candidate texts and finds the maximal local sub-sequence Jaccard overlap against the seed text.
- **Consequences**: Successfully discovers short legal snippets embedded within long narrative hadiths.

---

### D009: Orthogonal Topical False-Positive Quarantine
- **Status**: Accepted
- **Context**: Hadiths on common topics (e.g., *Niyyah*, *Wudūʾ*, *Ṣalāt*) produce deceptively high cosine similarity in dense vector spaces even when they are completely distinct historical traditions.
- **Decision**: If a candidate has high semantic cosine similarity ($> 0.80$) but low pericope overlap ($S_{jaccard} < 0.25$) and zero isnad hub overlap, quarantine it as `TOPICAL_FALSE_POSITIVE` and flag it in the triage view.
- **Consequences**: Prevents thematic drift and keeps tradition bundles historically cohesive.


---

### D010: Pluggable Corpus Backend & First-Class Manual Ingestion
- **Status**: Accepted
- **Context**: While `riwayat-corpus` (~925K records) is an extraordinary pre-indexed baseline, scholars and agents frequently need to work with unindexed compendia, rare manuscripts, custom regional collections (e.g. Zaydī or Ibāḍī compendia, Musannaf Ibn Abī Shaybah editions), or simply paste an excerpt directly from a book or PDF. Tightly coupling Masar to `riwayat-corpus` SQLite schema would cripple research on unindexed sources.
- **Decision**: 
  1. Define a generic `CorpusAdapter` interface requiring only basic record extraction (`id`, `raw_text`, optional `isnad_span`, `matn_span`, and `source_ref`).
  2. Implement a `RiwayatCorpusAdapter` for the pre-indexed 925K dataset, a `CustomFileCorpusAdapter` for user-supplied JSON/CSV/SQLite/text files, and an `InMemoryScratchpadAdapter` for ad-hoc manual entries.
  3. Treat **Manual Entry** as a first-class citizen: an agent or user can paste raw text via CLI (`masar add`) or UI, trigger an automated boundary heuristic split, edit/confirm it, attach citation provenance, and seamlessly bundle it alongside corpus-retrieved variants.
- **Consequences**: Masar operates seamlessly with or without `riwayat-corpus`. Any raw text can be ingested, aligned, verified, and exported to Riwaq.


---

### D011: Read-Through Overlay Architecture for Accretive Storage
- **Status**: Accepted
- **Context**: Raw scraped corpora (`riwayat-corpus`, Shamela dumps) must remain immutable, read-only baselines. However, when an agent or scholar repairs a boundary split or disambiguates a narrator, that correction must permanently shadow the unverified baseline across all future searches without rewriting raw corpus files.
- **Decision**: Implement a **Read-Through Overlay Architecture**:
  1. `L0 Base Layer`: Read-only `CorpusAdapter` querying original database/files.
  2. `L3 Overlay Layer`: `AccretiveStore` (`masar-curated.db`) storing delta records keyed by `(corpus_id, record_id)` containing verified `matn_start`, `matn_end`, narrator chain corrections, verification timestamp, and editor provenance.
  3. All read requests transparently resolve `Overlay.get() or Base.get()`.
- **Consequences**: Zero mutation of immutable corpus assets; 100% persistent accretion of verified scholarly ground truth.

---

### D012: Dual Anchor-Offset Boundary Split Contract
- **Status**: Accepted
- **Context**: In Arabic text, character offsets (`[start:end]`) are notoriously fragile: a single diacritic, zero-width joiner, or orthographic normalization shifts offsets by $\pm 1$ or $\pm 2$ characters, leading to boundary drift.
- **Decision**: Represent every boundary split with dual contracts:
  1. *Character Offsets*: Absolute `(matn_start, matn_end)` in the raw string.
  2. *Token Anchors*: Pivot token context `(pre_matn_token, post_isnad_token)` with surrounding window verification.
  If character offsets drift due to normalization or formatting, the engine uses token anchors to re-align the split deterministically.
- **Consequences**: Immune to diacritic/whitespace boundary drift; highly legible and robust for LLM agents.

---

### D013: Unified Multi-Modal Takhrīj Query Contract
- **Status**: Accepted
- **Context**: In real-world scholarly research, queries are rarely limited to single text snippets. Scholars and agents frequently query by Companion authority, transmitter Common Link hub, or ask to enrich an existing bundle with cross-sectarian parallels.
- **Decision**: Define `TakhrijQuery` as a multi-modal request:
  - `text`: optional search string (lexical & semantic)
  - `authority`: optional Companion or transmitter name/ID
  - `hub`: optional 2nd-century Common Link anchor
  - `collection_scope`: `all` | `sunni` | `shia` | explicit list
  - `enrich_family_id`: optional target family to enrich
  - `min_confidence`: float threshold (default 0.60)
- **Consequences**: A single unified search interface serves keyword search, transmitter search, topical search, and bundle enrichment.


---

### D014: Native Model Context Protocol (MCP) Stdio Server & Agent Tooling
- **Status**: Accepted
- **Context**: In modern AI coding and research workflows, agents (Claude, Gemini, Antigravity, Cursor, OpenCode) interact with complex engines via the Model Context Protocol (MCP). Relying solely on shell command execution or terminal scraping introduces parsing fragility, token inefficiency, and lack of typed JSON-RPC contracts.
- **Decision**: 
  1. Implement a native MCP stdio server in Python (`src/masar/mcp_server.py`) executable via `masar mcp`.
  2. Expose the core Takhrīj capabilities as first-class MCP tools: `masar_search`, `masar_inspect`, `masar_adjust_split`, `masar_add_manual`, `masar_stage_variant`, `masar_preflight_validate`, `masar_export_riwaq`, and `masar_diagnose`.
  3. Export a standard agent skill manifest (`skills/masar-takhrij/SKILL.md`) so that local agent tooling (e.g. `skillctl`, OpenCode, Antigravity) can seamlessly discover and load Masar into any active session.
- **Consequences**: Autonomous AI agents can drive and verify the entire takhrīj lifecycle via structured JSON-RPC tool calls with zero terminal scraping.

---

### D015: AI Proposal Staging Buffer for Non-Destructive Agent Interventions
- **Status**: Accepted
- **Context**: When an AI agent performs extraction, proposes narrator merges, or shifts isnad/matn boundaries, hallucinated or inaccurate boundaries could contaminate the persistent `masar-curated.db` store.
- **Decision**: Implement an **AI Proposal Staging Buffer** (`ProposalStore`):
  1. All agent-suggested boundary adjustments, variant groupings, and narrator merges enter the staging buffer as pending proposals with SHA-256 operation receipts.
  2. Proposals must pass the 4 deterministic preflight gates before being committed to `masar-curated.db`.
  3. A human researcher or reviewer can inspect, approve, or reject staged proposals in a single click in the Workbench UI or via `masar proposal approve <id>`.
- **Consequences**: Complete immunity against AI hallucination pollution in the accretive ground truth store; full scholarly audit trail for every machine intervention.
