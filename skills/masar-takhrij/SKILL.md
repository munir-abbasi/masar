---
name: masar-takhrij
description: High-precision Hadith Takhrīj (variant discovery and bundling) engine serving as upstream feeder for Riwaq ICMA stemma analysis. Use when discovering hadith variants, repairing CRF boundary bleed, resolving transmitter homonyms, and exporting verified family bundles.
---

# Masar Takhrīj Agent Skill

Masar (مسار) is a high-precision, agent-ergonomic Hadith Takhrīj engine. It bridges unbundled corpora (`riwayat-corpus` ~925K records, custom datasets, and raw manuscript entries) into verified `family_id` bundles conforming to Riwaq `schema_version: 1` (`import-batch.json`).

## When to Use

- Discover parallel traditions (*takhrīj*) across Sunni (Kutub al-Sittah, Musannafs) and Shīʿī (al-Kutub al-Arbaʿah) collections.
- Detect and align fragmented hadith quotations (*Taqṭīʿ*) using sliding-window pericope matching.
- Identify semantic variants (*Riwāyah bi-l-Maʿnā*) without lexical overlap.
- Repair noisy automated parser boundaries (CRF isnad/matn boundary bleed).
- Export verified, gate-passed family bundles into Riwaq for stemma DAG and Common Link analysis.

## Agent Control Interfaces

### 1. Model Context Protocol (MCP) Tools

When connected via MCP (`masar mcp`), the following typed tools are available:
- `masar_search(seed, scope, limit)`: Runs 4-signal discovery with Explainability Receipts.
- `masar_inspect(hadith_id)`: Fetches full text, isnad chain, and boundary status.
- `masar_adjust_split(hadith_id, start, end)`: Persists boundary override to `masar-curated.db`.
- `masar_add_manual(text, collection, ref, family_id)`: Ingests raw text with heuristic split.
- `masar_diagnose()`: Cross-layer system health and database statistics.

### 2. Single-Hop Machine CLI (`masar`)

```bash
# Token-thrifty candidate triage (< 300 tokens)
masar search --seed "إنما الأعمال بالنيات" --scope all --compact

# Machine JSON projection with Explainability Receipts
masar search --seed "إنما الأعمال بالنيات" --format json --receipts

# Inspect hadith text and isnad chain
masar inspect --id 4

# Adjust noisy CRF boundary slice and record to curated overlay
masar split --id 4 --start 149 --end 187

# Add manual manuscript transcription with heuristic split
masar add --text "حدثنا يحيى قال قال رسول الله..." --collection "Berlin MS 402" --ref "Folio 12b"

# Single-step reversible action undo
masar session undo
```

## System Invariants & Guardrails

1. **Discovery ≠ Canonical Truth**: Automated CRF parser boundaries are noisy. Never export uninspected records with isnad connectors bleeding into the matn.
2. **Topical False Positive Quarantine**: High semantic similarity without pericope overlap or isnad convergence is automatically quarantined as `TOPICAL_FALSE_POSITIVE`. Never un-quarantine without explicit textual evidence.
3. **Accretive Knowledge**: All boundary adjustments save to `masar-curated.db` via read-through overlay. The raw base corpus remains 100% immutable.
4. **Deterministic Preflight Gate**: Every candidate export must pass all 4 gates (`GateSchema`, `GateFamilyConsistency`, `GateBoundaryHygiene`, `GateIsnadIntegrity`).
