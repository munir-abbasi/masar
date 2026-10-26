"""SQLite adapter for riwayat-corpus format hadith databases."""

import json
from pathlib import Path
import sqlite3
from typing import Iterator, Optional
from masar.core.models import CandidateRecord, TakhrijQuery


def _parse_narrator_ids(raw_val: Optional[str]) -> list[str]:
    """Safely parse narrator IDs from JSON array or comma-delimited string."""
    if not raw_val:
        return []
    try:
        data = json.loads(raw_val)
        if isinstance(data, list):
            return [str(x) for x in data]
    except (json.JSONDecodeError, TypeError):
        pass
    return [p.strip() for p in raw_val.split(",") if p.strip()]


class RiwayatCorpusAdapter:
    """SQLite corpus adapter for riwayat-corpus schema."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)

    def _get_connection(self) -> sqlite3.Connection:
        """Create a connection with row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_record(self, record_id: str) -> Optional[CandidateRecord]:
        """Retrieve a single hadith record by unique ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, collection, book_number, hadith_number, sect,
                       full_text, matn, isnad_raw, primary_narrators
                FROM hadiths WHERE id = ?
                """,
                (record_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_record(row)

    def query_candidates(
        self,
        query: TakhrijQuery,
        limit: int = 100,
    ) -> Iterator[CandidateRecord]:
        """Stream candidate records matching query and sectarian scope."""
        clauses = []
        params = []

        if query.scope in ("sunni", "shia"):
            clauses.append("sect = ?")
            params.append(query.scope)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT id, collection, book_number, hadith_number, sect,
                   full_text, matn, isnad_raw, primary_narrators
            FROM hadiths
            {where_sql}
            LIMIT ?
        """
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            while True:
                rows = cursor.fetchmany(50)
                if not rows:
                    break
                for row in rows:
                    yield self._row_to_record(row)

    def list_collections(self) -> list[str]:
        """Return distinct collection identifiers in corpus."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT collection FROM hadiths ORDER BY collection")
            return [row["collection"] for row in cursor.fetchall()]

    def get_narrators(self, record_id: str) -> list[str]:
        """Return narrator IDs associated with record."""
        record = self.get_record(record_id)
        return record.narrator_ids if record else []

    def _row_to_record(self, row: sqlite3.Row) -> CandidateRecord:
        """Convert a SQLite row to CandidateRecord."""
        narrator_ids = _parse_narrator_ids(row["primary_narrators"])
        return CandidateRecord(
            id=str(row["id"]),
            collection=row["collection"],
            book_number=row["book_number"],
            hadith_number=row["hadith_number"],
            sect=row["sect"],
            full_text=row["full_text"],
            matn=row["matn"],
            isnad_raw=row["isnad_raw"],
            narrator_ids=narrator_ids,
        )
