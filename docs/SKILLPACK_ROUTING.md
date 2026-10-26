# Skill Pack & Tool Routing: Masar (مسار)

Generated: 2026-10-26
Skill Router: `cos-skillpack-router`
Primary Pack: `project-planning` (`sp-use-project-planning`)

## 1. Context & Rationale
`context.md` documents the architectural need for **Masar (مسار)**: a dedicated Takhrīj (variant gathering & assembly) application. 

In digital hadith scholarship, Riwaq (ICMA & Stemma Engine) executes Isnad-cum-Matn Analysis (CL/PCL detection, stemma DAG generation, matn variance apparatus). However, Riwaq strictly operates on pre-bundled traditions keyed by `family_id` adhering to `schema_version: 1` (`import-batch.json`). Linear corpus archives (like `riwayat-corpus` with ~925,000 texts) lack cross-collection tradition IDs and suffer from OCR/parsing noise (CRF whole-chain accuracy 68%–88%, matn boundary bleed, homonym collisions).

Masar acts as the upstream bridge:
1. **Discovery Engine (High Recall):** Multi-signal search (lexical BM25, semantic embeddings for *riwāyah bi-l-maʿnā*, and isnad anchoring) across Sunni, Shīʿī, or cross-sectarian corpora.
2. **Verification Layer (High Precision):** Human-in-the-loop side-by-side text collation and 1-click isnad/matn split editing.
3. **Riwaq Export Layer:** Emitting validated `family_id` bundles in Riwaq `schema_version: 1`.

## 2. Pack Evaluation & Verification

| Pack Name | Alias | Skills | Available | Unavailable | Materialized | Verification Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`project-planning`** | `sp-use-project-planning` | **86** | **86** | **0** | **Yes** | **Verified** |
| `prd-vibe-delivery` | `sp-use-prd-vibe-delivery` | 48 | 48 | 0 | Yes | Verified |
| `python-fastapi` | `sp-use-python-fastapi` | 69 | 69 | 0 | Yes | Verified |

## 3. Selected Skills from Canonical Tree (`$HOME/ai-tools/.unified_skills/`)

- **`writing-plans`**: Primary workflow for writing atomic, test-driven implementation plans.
- **`architecture` & `architecture-patterns`**: Architectural decision framework, Clean Architecture / DDD, and ADRs.
- **`database-design`**: Strategy for SQLite FTS5, vector embedding indexing, and Riwaq schema mapping.
- **`blueprint`**: Phased construction milestones and adversarial review criteria.
