# Masar (مسار) System Architecture: The Agent-Ergonomic Takhrīj Engine

## 1. Executive Philosophy: Designing for the Agent in the Driver's Seat

When an autonomous AI agent operates a research and engineering toolchain, conventional human-oriented UI/API patterns break down:
1. **The Context Explosion Trap (Vibe Tax)**: Dumps of full raw texts and 50-variant arrays exhaust the LLM's context window, degrading attention, creating amnesia, and driving up token expenditure.
2. **The Opaque State Trap**: UI state hidden in client-side component trees or uninspected database states forces the agent to guess what happened.
3. **The Fragile Action Trap**: Monolithic endpoints that perform search, clustering, and boundary parsing in a single black box prevent the agent from intervening when an error occurs.
4. **The Knowledge Evaporation Trap**: When an agent or human manually corrects a boundary split or rejects an erroneous parallel, that effort evaporates unless the system is **agent-accretive**—compounding every correction into a durable, versioned knowledge asset.

**Masar (مسار)** is architected from first principles as an **Agent-Ergonomic, Agent-Intuitive, and Agent-Accretive Synthetic System**.

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
│ • Normalized Arabic Orthography • Pluggable Corpus Adapters (Riwayat, Custom,    │
│   Manual Entry Scratchpad) • SQLite FTS5 Virtual Tables                          │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The Five Pillars of Agent-Centric Design

### Pillar 1: The "Agent Lens" & Unified Multi-Modal Querying
An agent needs to query flexibly and understand the exact state of a tradition search in seconds without consuming 20,000 tokens of raw Arabic text.
- **Unified Multi-Modal `TakhrijQuery` (D013)**:
  An agent can initiate takhrīj using any combination of signals:
  - Text search: Lexical or semantic search string (`text`).
  - Authority search: Companion or early transmitter (`authority`: e.g. "أبو هريرة").
  - Hub anchoring: 2nd-century Common Link (`hub`: e.g. "ابن شهاب الزهري").
  - Cross-sectarian bundle enrichment: Target an existing family (`enrich_family_id`) to find missing parallels across sectarian boundaries.
- **Hierarchical Summaries**: Every discovery query returns a high-density, tiered response:
  - *Tier 1 (Terse / Triage)*: 200 tokens total. A table of candidate matches containing `hadith_id`, `collection`, `sectarian_tag`, `composite_score`, `overlap_ratio`, and a 6-word pericope snippet.
  - *Tier 2 (Variant Focus)*: Full inspection available on a *single* target candidate (`hadith_id`), providing exact character offsets, parsed isnad chains, and matn text.
  - *Tier 3 (Diff Matrix)*: Visual token-level diff against the seed hadith only when explicitly requested.
- **Machine-Readable CLI & Headless API**: Every action is fully executable through a single-binary CLI (`masar`) outputting structured JSON or human-terse tables:
  ```bash
  masar search --seed "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ" --scope all --compact
  masar inspect --id bukhari-1 --field split
  masar split adjust --id bukhari-1 --matn-start 142
  masar bundle export --family-id hadith-niyyah --out bundle.json
  ```

### Pillar 2: Explainability Receipts (Transparent Scoring)
The system never returns an opaque ranking number (e.g., `score: 0.84`). Instead, every candidate carries an **Explainability Receipt** decomposing the evidence:
```json
{
  "hadith_id": "muslim-1907",
  "collection": "Sahih Muslim",
  "sect": "sunni",
  "composite_score": 0.885,
  "evidence": {
    "lexical_bm25": 14.82,
    "pericope_jaccard": 0.92,
    "semantic_cosine": 0.89,
    "isnad_hub_match": {
      "matched_hub": "Yahya ibn Sa'id al-Ansari",
      "authority": "Umar ibn al-Khattab",
      "chain_depth": 4
    }
  },
  "flags": ["high_confidence_parallel", "taqti_detected"]
}
```
This enables the agent to immediately diagnose *why* a report was surfaced and detect false positives (e.g., high semantic score but completely different isnad and companion).

### Pillar 3: Append-Only Journal & Dual Anchor-Offset Splits
Agents make mistakes, refine hypotheses, and explore alternate variant clusterings. Masar implements an **Event-Sourced Session Journal**:
- Every action (`ADD_VARIANT`, `EXCLUDE_VARIANT`, `ADJUST_SPLIT`, `TAG_NARRATOR`) appends an immutable event to the session log.
- Full time-travel and rollback: `masar session undo` or `masar session rollback --step 3`.
- **Dual Anchor-Offset Boundary Contract (D012)**:
  To prevent boundary drift caused by Arabic diacritics, tatweel, or normalization shifts, every boundary is stored with both character offsets `(start, end)` AND robust pivot token anchors `(pre_matn_token, post_isnad_token)`.

### Pillar 4: Accretive Ground Truth & Read-Through Overlay (The Flywheel)
In `riwayat-corpus`, over 214,000 texts suffer from Tier-C CRF parsing noise (matn boundary bleed, narrator names leaking into text).
- **Read-Through Overlay Architecture (D011)**:
  The raw corpus ($L_0$) remains immutable. Verified boundary adjustments and narrator corrections are stored in an overlay database (`masar-curated.db`).
- All corpus read queries pass through this overlay: if a curated override exists for `(corpus_id, record_id)`, it seamlessly shadows the unverified baseline.
- Over time, running Masar progressively cleans and elevates the raw corpus into a gold-standard academic dataset without modifying the underlying raw corpus files.

### Pillar 5: Deterministic Preflight Gates
Before any bundle is emitted to Riwaq, it must pass through an automated **Preflight Gate**:
1. `GATE_SCHEMA`: Strict compliance with Riwaq's `import-batch.json` and `hadith-record.json` (`schema_version: 1`).
2. `GATE_FAMILY_CONSISTENCY`: All records share identical `family_id`; minimum of 2 variants for meaningful ICMA.
3. `GATE_BOUNDARY_HYGIENE`: Heuristic scan ensuring no narrator introductory markers (*ḥaddathanā*, *akhbaranā*, *ʿan*) remain inside the extracted `matn_raw`.
4. `GATE_ISNAD_INTEGRITY`: Verification that each variant has a non-empty `isnad_chain` of identified transmitter IDs.

### Pillar 6: Universal Data Ingestion & First-Class Manual Entry
Masar is never bound solely to `riwayat-corpus`. It treats any input source as equal:
- **Pluggable Corpus Adapters**: Pre-indexed `riwayat-corpus`, custom JSON/CSV collections, or raw text directories.
- **First-Class Manual Entry**: An agent or scholar can paste raw Arabic text from a manuscript, printed edition, or website (`masar add` or Web Workbench), specify citation metadata (`collection`, `volume`, `page`), trigger an automated isnad/matn split proposal, adjust the boundary, and bundle the record alongside corpus-retrieved parallels.

### Pillar 7: Native Model Context Protocol (MCP) & AI Tooling (D014, D015)
To empower autonomous AI agents (Claude, Gemini, Antigravity, OpenCode) to drive takhrīj without terminal scraping:
- **Native MCP Stdio Server (`masar mcp`)**: Exposes discovery, inspection, boundary adjustment, and export as typed JSON-RPC tools (`masar_search`, `masar_inspect`, `masar_adjust_split`, `masar_add_manual`, `masar_stage_variant`, `masar_preflight_validate`, `masar_export_riwaq`).
- **AI Proposal Staging Buffer (`ProposalStore`)**: Protects the accretive store against hallucination. Agent proposals enter an isolated staging area with SHA-256 operation receipts, requiring deterministic preflight gate validation before permanent curation.
- **Agent Skill Package**: Provides a plug-and-play agent skill (`skills/masar-takhrij/SKILL.md`) discoverable by local agent tooling (`skillctl`, OpenCode, Antigravity).

---

## 3. Failure-Mode First Engineering Matrix

Following the user's strict testing rules, the entire system is built and tested against explicit **Failure Modes**:

| Failure Mode ID | Failure Scenario | Impact | System Mitigation | High-Value Test Scenario | Verifiable Artifact |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FM-01: Boundary Bleed** | CRF parser includes "حدثنا الحميدي قال حدثنا سفيان" inside the `matn_raw`. | Riwaq's matn apparatus corrupts Jaccard lexical overlap calculations ($S_5$). | `SplitEditor` + `HeuristicBoundaryGuard` detects isnad connectors in matn and highlights them for 1-click correction. | **E2E-BLEED-REPAIR**: Load noisy record from Bukhari #1, run automatic guard, execute agent split adjustment, verify clean matn. | `test-artifacts/bleed_repair_diff.json` |
| **FM-02: Homonym Trap** | Transmitters with identical names (e.g., Sufyān al-Thawrī vs Sufyān ibn ʿUyaynah) cause spurious chain merges. | Skews Common Link (CL) scoring and creates fake historical convergence. | Prosopographical disambiguation via collection date, student-teacher edge verification, and explicit warning flags. | **E2E-HOMONYM-DISAMBIG**: Candidate hadith with Sufyan compared against known student chains; assert warning emitted if ambiguous. | `test-artifacts/homonym_audit_log.json` |
| **FM-03: Topic vs Tradition Confusion** | Two different hadiths on the same topic (e.g. *Niyyah* vs *Qiyām al-Layl*) yield high semantic embedding similarity. | Pollutes the tradition bundle with unrelated historical reports. | Orthogonal evidence gate: Semantic similarity without pericope overlap ($S_{jaccard} < 0.25$) or isnad anchor consensus is tagged as `TOPICAL_FALSE_POSITIVE`. | **E2E-TOPIC-REJECTION**: Query "Actions are by intention"; inject "The believer's intention is better than his action"; verify candidate is rejected or quarantined. | `test-artifacts/topical_quarantine_report.json` |
| **FM-04: Taqṭīʿ (Fragment) Fragmentation** | A compiler cites a 1-line legal snippet of a 20-line hadith. Global Jaccard similarity is only 0.08. | Discovery engine misses critical legal variants of the tradition. | Sliding-window Pericope Aligner computes maximum local sub-sequence token alignment. | **E2E-TAQTIC-ALIGN**: Align 12-token excerpt against 150-token report; assert match detected with pericope confidence $> 0.85$. | `test-artifacts/taqtic_alignment_dump.json` |
| **FM-05: Cross-Sectarian Asymmetry** | Sunni collections use *ḥaddathanā* / *ʿan* chains; Shīʿī collections (*al-Kāfī*) use Imām-anchored chains with distinct introductory formulas. | Parser or search fails when traversing cross-sectarian boundary. | Sectarian-agnostic canonical schema with specialized transmission formula recognizers for both traditions. | **E2E-CROSS-SECT-TAKRIJ**: Run search on *Hadith al-Thaqalayn*; retrieve variants across Sahih Muslim and al-Kāfī; bundle into single valid family. | `test-artifacts/cross_sectarian_family.json` |
| **FM-06: Riwaq Ingestion Rejection** | Exported JSON has missing `source_ref.source_type` enum or inconsistent `family_id`. | Riwaq crashes on import or aborts analysis. | Deterministic `PreflightValidator` blocks export with exact line-level remediation hints. | **E2E-RIWAQ-GATE**: Generate export batch, run through strict JSON schema draft-07 validator; assert 100% pass. | `test-artifacts/riwaq_preflight_pass.json` |
| **FM-07: Unstructured Manual Entry Contamination** | Pasted manual text lacks explicit boundary offsets or required provenance metadata. | Incomplete record corrupts downstream stemma or fails Riwaq intake. | `ManualEntryPipeline` applies interactive heuristic split assistant and requires valid `source_ref` before bundle admission. | **E2E-MANUAL-ENTRY**: Paste raw manuscript excerpt, run heuristic splitter, confirm split, export to Riwaq; verify valid record. | `test-artifacts/manual_entry_verified.json` |
| **FM-08: AI Proposal Hallucination & Staging Drift** | Agent-suggested boundary split or narrator merge is inaccurate or ungrounded. | Pollutes the accretive store (`masar-curated.db`) with hallucinated ground truth. | `ProposalStore` isolates agent interventions; enforces preflight gates and SHA-256 operation receipts before permanent curation. | **E2E-AI-STAGING**: Agent submits boundary proposal, stages in ProposalStore, runs preflight gate, rejects invalid proposal; assert store remains pristine. | `test-artifacts/ai_proposal_staged.json` |

---

## 4. End-to-End System Data Flow

```text
[ Seed Input: Text / Hadith ID / Transmitters ]
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Multi-Signal Retrieval & Alignment                       │
│    • FTS5 BM25 (Lexical)                                    │
│    • Dense Embedding Cosine (Riwāyah bi-l-Maʿnā)            │
│    • Sliding Pericope Window (Taqṭīʿ)                       │
│    • Isnad Hub Traversal (Common Link Anchor)               │
└─────────────────────┬───────────────────────────────────────┘
                      │ Ranked Candidates + Explainability Receipts
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Agent / Researcher Triage (Token-Thrifty Summary)        │
│    • Displays compact candidate summary                     │
│    • Flags potential false positives (Topic Trap, Homonyms) │
│    • Flags boundary bleed warnings                          │
└─────────────────────┬───────────────────────────────────────┘
                      │ Selection + Boundary Edits
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Boundary Split Verification & Knowledge Accretion        │
│    • Exact character offset adjustment (matn_start/end)     │
│    • Correction saved to `masar-curated.db` flywheel        │
│    • Event appended to session journal                      │
└─────────────────────┬───────────────────────────────────────┘
                      │ Verified Variants
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Riwaq Preflight Gate & Export Engine                     │
│    • Validates schema_version: 1 and family_id consistency  │
│    • Emits canonical `import-batch.json`                    │
│    • End-to-end audit artifact stored for reproducibility   │
└─────────────────────────────────────────────────────────────┘
```
