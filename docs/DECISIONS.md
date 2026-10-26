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
