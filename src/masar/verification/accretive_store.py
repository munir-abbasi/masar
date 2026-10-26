"""Accretive Ground Truth Store and Read-Through Overlay Resolver (ADR D011)."""

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Optional

from masar.core.corpus_adapter import CorpusAdapter
from masar.core.models import CandidateRecord, SplitBoundary


class AccretiveStore:
    """Persistent overlay storage for verified boundaries, narrator fixes, and quarantines."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a connection with row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize accretive overlay schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS boundary_overrides (
                    hadith_id TEXT PRIMARY KEY,
                    matn_start INTEGER NOT NULL,
                    matn_end INTEGER NOT NULL,
                    pre_matn_token TEXT,
                    post_isnad_token TEXT,
                    anchor_window TEXT,
                    curated_at TEXT NOT NULL,
                    curator TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS quarantines (
                    candidate_id TEXT PRIMARY KEY,
                    reason TEXT NOT NULL,
                    quarantined_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save_boundary_override(
        self,
        hadith_id: str,
        boundary: SplitBoundary,
        curator: str = "agent",
    ):
        """Persist a curated split boundary override into the accretive store."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO boundary_overrides (
                    hadith_id, matn_start, matn_end, pre_matn_token,
                    post_isnad_token, anchor_window, curated_at, curator
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    hadith_id,
                    boundary.matn_start,
                    boundary.matn_end,
                    boundary.pre_matn_token,
                    boundary.post_isnad_token,
                    boundary.anchor_window,
                    now_iso,
                    curator,
                ),
            )
            conn.commit()

    def get_boundary_override(self, hadith_id: str) -> Optional[SplitBoundary]:
        """Retrieve a curated boundary override if one exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT matn_start, matn_end, pre_matn_token, post_isnad_token, anchor_window
                FROM boundary_overrides WHERE hadith_id = ?
                """,
                (hadith_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return SplitBoundary(
                matn_start=row["matn_start"],
                matn_end=row["matn_end"],
                pre_matn_token=row["pre_matn_token"],
                post_isnad_token=row["post_isnad_token"],
                anchor_window=row["anchor_window"],
            )

    def resolve_record(
        self,
        record_id: str,
        base_adapter: CorpusAdapter,
    ) -> Optional[CandidateRecord]:
        """Resolve record via read-through overlay: applies curated overrides over immutable base."""
        base_rec = base_adapter.get_record(record_id)
        if not base_rec:
            return None

        override = self.get_boundary_override(record_id)
        if not override:
            return base_rec

        # Apply curated slice to full_text if available
        full = base_rec.full_text or ""
        clean_matn = full[override.matn_start : override.matn_end].strip() if full else base_rec.matn
        clean_isnad = full[: override.matn_start].strip() if full else base_rec.isnad_raw

        return CandidateRecord(
            id=base_rec.id,
            collection=base_rec.collection,
            book_number=base_rec.book_number,
            hadith_number=base_rec.hadith_number,
            sect=base_rec.sect,
            full_text=base_rec.full_text,
            matn=clean_matn,
            isnad_raw=clean_isnad,
            narrator_ids=base_rec.narrator_ids,
            receipt=base_rec.receipt,
        )
