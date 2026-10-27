"""Unit tests for Pydantic models, explainability receipts, and Riwaq schema compliance."""

import json
from pathlib import Path
import pytest
import jsonschema

from masar.core.models import (
    TakhrijQuery,
    SplitBoundary,
    SignalScores,
    ExplainabilityReceipt,
    CandidateRecord,
    SourceRef,
    IsnadVariant,
    HadithRecord,
    ImportBatch,
)

SCHEMAS_DIR = Path(__file__).resolve().parent.parent.parent / "schemas"


@pytest.fixture
def riwaq_batch_schema():
    with open(SCHEMAS_DIR / "riwaq-import-batch.json", encoding="utf-8") as f:
        return json.load(f)


def test_takhrij_query_defaults():
    """Verify TakhrijQuery multi-modal initialization and defaults."""
    query = TakhrijQuery(seed_text="إنما الأعمال بالنيات")
    assert query.seed_text == "إنما الأعمال بالنيات"
    assert query.scope == "all"
    assert query.min_pericope_threshold == 0.35
    assert query.semantic_top_k == 50
    assert query.hub_narrator_ids == []


def test_split_boundary_dual_anchors():
    """Verify SplitBoundary supports character offsets and token anchors."""
    boundary = SplitBoundary(
        matn_start=150,
        matn_end=320,
        pre_matn_token="قال",
        post_isnad_token="رسول",
        anchor_window="قال رسول الله صلى الله عليه وسلم إنما",
    )
    assert boundary.matn_start == 150
    assert boundary.matn_end == 320
    assert boundary.pre_matn_token == "قال"
    assert boundary.post_isnad_token == "رسول"


def test_split_boundary_validation_error():
    """Verify SplitBoundary rejects invalid ranges where matn_start >= matn_end."""
    with pytest.raises(ValueError):
        SplitBoundary(matn_start=200, matn_end=100)


def test_explainability_receipt_and_quarantine():
    """Verify ExplainabilityReceipt tracks signal decomposition and topical false positives."""
    receipt = ExplainabilityReceipt(
        candidate_id="bukhari_1",
        ensemble_score=0.92,
        signal_scores=SignalScores(
            bm25_lexical=0.95,
            pericope_jaccard=0.88,
            semantic_cosine=0.94,
            isnad_overlap=1.0,
        ),
        is_topical_false_positive=False,
    )
    assert receipt.ensemble_score == 0.92
    assert receipt.is_topical_false_positive is False
    assert receipt.quarantine_reason is None

    # Quarantined receipt
    quarantined = ExplainabilityReceipt(
        candidate_id="ahmad_21840",
        ensemble_score=0.25,
        signal_scores=SignalScores(
            bm25_lexical=0.15,
            pericope_jaccard=0.10,
            semantic_cosine=0.85,
            isnad_overlap=0.0,
        ),
        is_topical_false_positive=True,
        quarantine_reason="High semantic similarity without lexical or isnad convergence (Topic Trap)",
    )
    assert quarantined.is_topical_false_positive is True
    assert quarantined.quarantine_reason is not None


def test_riwaq_import_batch_json_schema(riwaq_batch_schema):
    """Verify that ImportBatch output validates strictly against schemas/riwaq-import-batch.json."""
    record = HadithRecord(
        hadith_id="bukhari_1",
        family_id="fam_niyyah_001",
        title="Hadith of Intentions",
        source_ref=SourceRef(
            collection="Sahih al-Bukhari",
            source_type="print",
            source_locator="Book 1, Hadith 1",
            ingested_at="2026-10-26T12:00:00Z",
        ),
        variants=[
            IsnadVariant(
                variant_id="var_01",
                isnad_chain=["al_humaydi", "sufyan", "yahya_b_said", "umar_b_al_khattab"],
                matn_offset={"start": 235, "end": 371},
                status="primary",
            )
        ],
        matn_raw="إنما الأعمال بالنيات",
    )

    batch = ImportBatch(
        schema_version=1,
        imported_at="2026-10-26T12:00:00Z",
        import_id="imp_test_001",
        records=[record],
    )

    batch_dict = batch.model_dump(mode="json")
    
    # Resolving schema refs locally using preloaded store
    with open(SCHEMAS_DIR / "riwaq-hadith-record.json", encoding="utf-8") as f:
        hadith_record_schema = json.load(f)

    store = {
        "https://raw.githubusercontent.com/munir-abbasi/riwaq/main/schemas/import-batch.json": riwaq_batch_schema,
        "https://raw.githubusercontent.com/munir-abbasi/riwaq/main/schemas/hadith-record.json": hadith_record_schema,
        "hadith-record.json": hadith_record_schema,
    }
    schema_path = (SCHEMAS_DIR / "riwaq-import-batch.json").as_uri()
    resolver = jsonschema.RefResolver(base_uri=schema_path, referrer=riwaq_batch_schema, store=store)
    jsonschema.validate(instance=batch_dict, schema=riwaq_batch_schema, resolver=resolver)
