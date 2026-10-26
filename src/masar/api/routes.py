"""FastAPI route handlers for Masar Takhrīj discovery, split curation, and export."""

import sqlite3
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from masar.agent_control import AgentControlPlane
from masar.core.corpus_db import RiwayatCorpusAdapter
from masar.core.models import CandidateRecord, ImportBatch, TakhrijQuery
from masar.discovery.hybrid_engine import HybridTakhrijEngine
from masar.export.riwaq_exporter import PreflightGateError, RiwaqExporter
from masar.verification.accretive_store import AccretiveStore
from masar.verification.split_editor import SplitEditor

router = APIRouter(prefix="/api")


class SplitRequest(BaseModel):
    hadith_id: str
    matn_start: int
    matn_end: int


class ExportRequest(BaseModel):
    record_ids: list[str]
    family_id: str
    import_id: Optional[str] = None


@router.get("/diagnose")
def get_diagnostics(request: Request) -> dict[str, Any]:
    control: AgentControlPlane = request.app.state.control
    return control.diagnose()


@router.post("/search", response_model=list[CandidateRecord])
def search_hadiths(query: TakhrijQuery, request: Request):
    db_path = request.app.state.db_path
    conn = sqlite3.connect(db_path)
    engine = HybridTakhrijEngine(conn)
    engine.ensure_index()
    candidates = engine.discover(query, limit=query.semantic_top_k)
    return candidates


@router.get("/hadith/{hadith_id}", response_model=CandidateRecord)
def get_hadith(hadith_id: str, request: Request):
    db_path = request.app.state.db_path
    curated_store: AccretiveStore = request.app.state.curated_store
    adapter = RiwayatCorpusAdapter(db_path)
    record = curated_store.resolve_record(hadith_id, adapter)
    if not record:
        raise HTTPException(status_code=404, detail=f"Hadith '{hadith_id}' not found.")
    return record


@router.post("/split")
def adjust_split(payload: SplitRequest, request: Request):
    db_path = request.app.state.db_path
    curated_store: AccretiveStore = request.app.state.curated_store
    adapter = RiwayatCorpusAdapter(db_path)
    record = adapter.get_record(payload.hadith_id)
    if not record or not record.full_text:
        raise HTTPException(status_code=404, detail=f"Hadith '{payload.hadith_id}' not found.")

    editor = SplitEditor()
    new_boundary = editor.adjust_split(record.full_text, payload.matn_start, payload.matn_end)
    curated_store.save_boundary_override(payload.hadith_id, new_boundary, curator="web_api")

    return {"status": "SUCCESS", "boundary": new_boundary.model_dump()}


@router.post("/export", response_model=ImportBatch)
def export_batch(payload: ExportRequest, request: Request):
    db_path = request.app.state.db_path
    curated_store: AccretiveStore = request.app.state.curated_store
    adapter = RiwayatCorpusAdapter(db_path)
    exporter = RiwaqExporter(adapter, curated_store)

    try:
        batch = exporter.build_batch(
            record_ids=payload.record_ids,
            family_id=payload.family_id,
            import_id=payload.import_id,
        )
        return batch
    except PreflightGateError as e:
        raise HTTPException(status_code=422, detail=str(e))
