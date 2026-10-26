"""Hybrid Takhrīj multi-signal matching engine and explainability decomposition."""

import json
import sqlite3
from typing import Optional

from masar.core.models import (
    CandidateRecord,
    ExplainabilityReceipt,
    SignalScores,
    TakhrijQuery,
)
from masar.discovery.fts_search import FtsSearchEngine
from masar.discovery.isnad_filter import IsnadAnchorFilter
from masar.discovery.pericope_aligner import PericopeAligner
from masar.discovery.semantic_search import SemanticMatcher


def _parse_narrator_ids(val: Optional[str]) -> list[str]:
    """Parse narrator IDs from JSON array or comma-delimited string."""
    if not val:
        return []
    try:
        data = json.loads(val)
        if isinstance(data, list):
            return [str(x) for x in data]
    except Exception:
        pass
    return [p.strip() for p in val.split(",") if p.strip()]


def _check_topical_trap(
    semantic_cosine: float,
    pericope_jaccard: float,
    isnad_overlap: float,
    min_pericope_threshold: float,
    bm25_lexical: float = 0.0,
) -> tuple[bool, Optional[str]]:
    """Determine if a candidate is a topical false positive (FM-03)."""
    has_match = (semantic_cosine >= 0.20 or bm25_lexical >= 0.20)
    lacks_pericope = pericope_jaccard < min_pericope_threshold
    lacks_isnad = isnad_overlap < 0.20

    if has_match and lacks_pericope and lacks_isnad:
        reason = (
            f"Topical match (semantic={semantic_cosine:.2f}, bm25={bm25_lexical:.2f}) "
            f"without sufficient pericope overlap ({pericope_jaccard:.2f} < {min_pericope_threshold}) "
            f"or isnad convergence ({isnad_overlap:.2f} < 0.20) (Topic Trap)"
        )
        return True, reason
    return False, None


class HybridTakhrijEngine:
    """Ensemble engine executing multi-signal discovery with Explainability Receipts."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self.fts_engine = FtsSearchEngine(conn)
        self.pericope_aligner = PericopeAligner()
        self.semantic_matcher = SemanticMatcher()
        self.isnad_filter = IsnadAnchorFilter()

    def ensure_index(self):
        """Ensure full-text search indices are built."""
        self.fts_engine.ensure_index()

    def _load_candidate_rows(self, scope: str) -> list[sqlite3.Row]:
        """Load candidate rows respecting sectarian scope."""
        clauses = []
        params = []
        if scope in ("sunni", "shia"):
            clauses.append("sect = ?")
            params.append(scope)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT id, collection, book_number, hadith_number, sect,
                   full_text, matn, isnad_raw, primary_narrators
            FROM hadiths
            {where_sql}
        """
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

    def _evaluate_candidate(
        self,
        row: sqlite3.Row,
        query: TakhrijQuery,
        bm25_map: dict[str, float],
    ) -> CandidateRecord:
        """Score candidate across 4 signals, apply Topic Trap quarantine, and emit receipt."""
        cid = str(row["id"])
        matn = row["matn"]
        narrator_ids = _parse_narrator_ids(row["primary_narrators"])

        bm25_score = bm25_map.get(cid, 0.0)
        seed = query.seed_text or ""

        # Signal 2: Pericope sliding window
        pericope_res = self.pericope_aligner.align(seed, matn)
        pericope_score = pericope_res.max_jaccard

        # Signal 3: Dense semantic cosine
        semantic_score = self.semantic_matcher.similarity(seed, matn)

        # Signal 4: Isnad & Hub anchor overlap
        isnad_score = self.isnad_filter.score_anchors(
            candidate_chain=narrator_ids,
            hub_narrator_ids=query.hub_narrator_ids,
            companion_id=query.companion_id,
        )

        # Topic Trap Quarantine check
        is_trap, trap_reason = _check_topical_trap(
            semantic_score, pericope_score, isnad_score, query.min_pericope_threshold, bm25_score
        )

        # Calculate weighted composite ensemble
        raw_ensemble = (
            0.30 * bm25_score
            + 0.35 * pericope_score
            + 0.20 * semantic_score
            + 0.15 * isnad_score
        )
        ensemble = min(0.25, raw_ensemble) if is_trap else raw_ensemble

        receipt = ExplainabilityReceipt(
            candidate_id=cid,
            ensemble_score=round(ensemble, 4),
            signal_scores=SignalScores(
                bm25_lexical=round(bm25_score, 4),
                pericope_jaccard=round(pericope_score, 4),
                semantic_cosine=round(semantic_score, 4),
                isnad_overlap=round(isnad_score, 4),
            ),
            is_topical_false_positive=is_trap,
            quarantine_reason=trap_reason,
            pericope_spans=[(pericope_res.start_token_idx, pericope_res.end_token_idx)],
        )

        return CandidateRecord(
            id=cid,
            collection=row["collection"],
            book_number=row["book_number"],
            hadith_number=row["hadith_number"],
            sect=row["sect"],
            full_text=row["full_text"],
            matn=matn,
            isnad_raw=row["isnad_raw"],
            narrator_ids=narrator_ids,
            receipt=receipt,
        )

    def discover(self, query: TakhrijQuery, limit: int = 50) -> list[CandidateRecord]:
        """Execute multi-signal discovery, rank candidates, and quarantine false positives."""
        # Step 1: Lexical pre-filter via FTS5
        bm25_results = self.fts_engine.search(
            query.seed_text or "", scope=query.scope, limit=limit * 2
        )
        bm25_map = {rid: score for rid, score in bm25_results}

        # Step 2: Load candidate rows
        rows = self._load_candidate_rows(query.scope)

        # Step 3: Evaluate each candidate
        candidates = [self._evaluate_candidate(r, query, bm25_map) for r in rows]

        # Step 4: Sort: verified variants first by ensemble descending, then quarantined
        def _sort_key(c: CandidateRecord):
            is_trap = c.receipt.is_topical_false_positive if c.receipt else False
            score = c.receipt.ensemble_score if c.receipt else 0.0
            return (0 if not is_trap else 1, -score)

        candidates.sort(key=_sort_key)
        return candidates[:limit]
