"""E2E Test: Custom corpus ingestion (JSON / CSV) via CustomFileCorpusAdapter (FM-07)."""

import json
from pathlib import Path
import pytest
from masar.core.corpus_adapter import CustomFileCorpusAdapter, CorpusAdapter
from masar.core.models import TakhrijQuery


def test_custom_json_corpus_ingestion(tmp_path: Path, test_artifacts_dir: Path):
    """Verify loading custom JSON file with regional hadiths into searchable adapter."""
    custom_records = [
        {
            "id": "zayd_101",
            "collection": "musnad_zaid",
            "hadith_number": "101",
            "sect": "shia",
            "full_text": "حدثنا زيد بن علي عن أبيه عن جده عن علي قال قال رسول الله إنما الأعمال بالنيات",
            "matn": "إنما الأعمال بالنيات",
            "isnad_raw": "حدثنا زيد بن علي عن أبيه عن جده عن علي قال قال رسول الله",
            "primary_narrators": ["zaid_b_ali", "ali_b_husayn", "al_husayn_b_ali", "ali_b_abi_talib"],
        },
        {
            "id": "ibadi_202",
            "collection": "tartib_al_musnad",
            "hadith_number": "202",
            "sect": "sunni",
            "full_text": "روى الربيع بن حبيب عن أبي عبيدة عن جابر بن زيد عن ابن عباس عن النبي قال النية أبلغ من العمل",
            "matn": "النية أبلغ من العمل",
            "isnad_raw": "روى الربيع بن حبيب عن أبي عبيدة عن جابر بن زيد عن ابن عباس عن النبي قال",
            "primary_narrators": ["al_rabi", "abu_ubaida", "jabir_b_zaid", "ibn_abbas"],
        },
    ]

    json_path = tmp_path / "custom_hadiths.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(custom_records, f, ensure_ascii=False, indent=2)

    adapter = CustomFileCorpusAdapter.from_file(json_path)
    assert isinstance(adapter, CorpusAdapter)

    # Verify retrieval
    rec = adapter.get_record("zayd_101")
    assert rec is not None
    assert rec.collection == "musnad_zaid"
    assert rec.sect == "shia"
    assert "إنما الأعمال بالنيات" in rec.matn

    # Query with sectarian filter
    q_all = TakhrijQuery(seed_text="النيات", scope="all")
    results = list(adapter.query_candidates(q_all))
    assert len(results) == 2

    q_shia = TakhrijQuery(seed_text="النيات", scope="shia")
    results_shia = list(adapter.query_candidates(q_shia))
    assert len(results_shia) == 1
    assert results_shia[0].id == "zayd_101"

    # Verifiable artifact
    artifact_path = test_artifacts_dir / "custom_corpus_ingested.json"
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "file_type": "json",
                "record_count": len(custom_records),
                "collections": adapter.list_collections(),
                "records_sample": [r.model_dump() for r in results],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    assert artifact_path.exists()
