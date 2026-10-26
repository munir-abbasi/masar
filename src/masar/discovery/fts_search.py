"""SQLite FTS5 Lexical Search Engine for fast BM25 hadith text retrieval."""

import sqlite3
from typing import Union
from masar.core.normalizer import normalize_arabic, tokenize_arabic


class FtsSearchEngine:
    """Full-Text Search (FTS5) engine over normalized Arabic matn texts."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def ensure_index(self):
        """Create and populate FTS5 virtual table if it does not exist."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS hadiths_fts USING fts5(
                record_id UNINDEXED,
                normalized_matn,
                collection,
                sect
            )
            """
        )

        # Check if index has rows
        cursor.execute("SELECT count(*) FROM hadiths_fts")
        if cursor.fetchone()[0] == 0:
            cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='hadiths'")
            if cursor.fetchone()[0] > 0:
                cursor.execute("SELECT id, matn, collection, sect FROM hadiths")
                rows = cursor.fetchall()
                for rid, matn, coll, sect in rows:
                    norm = normalize_arabic(matn)
                    cursor.execute(
                        "INSERT INTO hadiths_fts(record_id, normalized_matn, collection, sect) VALUES (?, ?, ?, ?)",
                        (str(rid), norm, coll, sect),
                    )
                self.conn.commit()

    def index_record(
        self,
        record_id: Union[str, int],
        matn: str,
        collection: str,
        sect: str,
    ):
        """Index or update a single hadith record into FTS5 table."""
        normalized = normalize_arabic(matn)
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO hadiths_fts(record_id, normalized_matn, collection, sect)
            VALUES (?, ?, ?, ?)
            """,
            (str(record_id), normalized, collection, sect),
        )
        self.conn.commit()

    def search(
        self,
        query_text: str,
        scope: str = "all",
        limit: int = 50,
    ) -> list[tuple[str, float]]:
        """Search records via BM25 matching and return (record_id, normalized_bm25_score)."""
        tokens = tokenize_arabic(query_text)
        if not tokens:
            return []

        # Construct boolean match query: match terms
        match_query = " OR ".join(tokens)

        clauses = ["hadiths_fts MATCH ?"]
        params: list[Union[str, int]] = [match_query]

        if scope in ("sunni", "shia"):
            clauses.append("sect = ?")
            params.append(scope)

        where_sql = f"WHERE {' AND '.join(clauses)}"
        sql = f"""
            SELECT record_id, bm25(hadiths_fts) as rank, normalized_matn
            FROM hadiths_fts
            {where_sql}
            ORDER BY rank
            LIMIT ?
        """
        params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        results: list[tuple[str, float]] = []
        query_set = set(tokens)

        for rid, rank, matn in rows:
            # SQLite FTS5 bm25 returns negative score (lower/more negative = better)
            raw_bm25 = abs(float(rank))
            bm25_score = raw_bm25 / (1.0 + raw_bm25) if raw_bm25 > 0.01 else 0.0

            # Complement with token overlap ratio to resist small-corpus IDF skew
            doc_tokens = set(tokenize_arabic(matn))
            overlap_ratio = len(query_set & doc_tokens) / len(query_set) if query_set else 0.0

            score = max(bm25_score, overlap_ratio)
            results.append((str(rid), round(score, 4)))

        return results
