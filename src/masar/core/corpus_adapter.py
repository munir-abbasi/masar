"""Corpus Adapter interface for pluggable hadith storage backends (ADR D010)."""

import csv
import json
from pathlib import Path
from typing import Any, Iterator, Optional, Protocol, runtime_checkable
from masar.core.models import CandidateRecord, TakhrijQuery


@runtime_checkable
class CorpusAdapter(Protocol):
    """Protocol defining the interface for all corpus database adapters."""

    def get_record(self, record_id: str) -> Optional[CandidateRecord]:
        """Retrieve a single hadith record by unique ID."""
        ...

    def query_candidates(
        self,
        query: TakhrijQuery,
        limit: int = 100,
    ) -> Iterator[CandidateRecord]:
        """Stream candidate hadith records matching query criteria and sectarian scope."""
        ...

    def list_collections(self) -> list[str]:
        """Return list of distinct collection identifiers present in corpus."""
        ...

    def get_narrators(self, record_id: str) -> list[str]:
        """Return canonical narrator IDs associated with a record."""
        ...


class CustomFileCorpusAdapter:
    """Adapter for custom hadith datasets loaded from JSON or CSV files."""

    def __init__(self, records: list[CandidateRecord]):
        self._records = records
        self._id_index = {r.id: r for r in records}

    @classmethod
    def from_file(cls, file_path: str | Path) -> "CustomFileCorpusAdapter":
        """Load and parse records from a JSON or CSV dataset file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Corpus file not found: {path}")

        if path.suffix.lower() == ".json":
            return cls._from_json(path)
        if path.suffix.lower() == ".csv":
            return cls._from_csv(path)
        raise ValueError(f"Unsupported file format: {path.suffix}")

    @classmethod
    def _from_json(cls, path: Path) -> "CustomFileCorpusAdapter":
        """Parse JSON list of hadith records."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        records = [cls._dict_to_record(item) for item in data]
        return cls(records)

    @classmethod
    def _from_csv(cls, path: Path) -> "CustomFileCorpusAdapter":
        """Parse CSV rows into candidate records."""
        records = []
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(cls._dict_to_record(row))
        return cls(records)

    @staticmethod
    def _dict_to_record(d: dict[str, Any]) -> CandidateRecord:
        """Convert a dictionary to a CandidateRecord."""
        narrators = d.get("primary_narrators") or []
        if isinstance(narrators, str):
            try:
                narrators = json.loads(narrators)
            except Exception:
                narrators = [n.strip() for n in narrators.split(",") if n.strip()]

        return CandidateRecord(
            id=str(d.get("id")),
            collection=str(d.get("collection", "custom")),
            book_number=d.get("book_number"),
            hadith_number=str(d.get("hadith_number", "1")),
            sect=d.get("sect", "sunni"),
            full_text=d.get("full_text"),
            matn=str(d.get("matn", "")),
            isnad_raw=d.get("isnad_raw"),
            narrator_ids=narrators,
        )

    def get_record(self, record_id: str) -> Optional[CandidateRecord]:
        """Retrieve a single hadith record by unique ID."""
        return self._id_index.get(str(record_id))

    def query_candidates(
        self,
        query: TakhrijQuery,
        limit: int = 100,
    ) -> Iterator[CandidateRecord]:
        """Stream candidate records matching query and sectarian scope."""
        count = 0
        for r in self._records:
            if count >= limit:
                break
            if query.scope in ("sunni", "shia") and r.sect != query.scope:
                continue
            yield r
            count += 1

    def list_collections(self) -> list[str]:
        """Return distinct collection identifiers in corpus."""
        return sorted({r.collection for r in self._records})

    def get_narrators(self, record_id: str) -> list[str]:
        """Return narrator IDs associated with record."""
        rec = self.get_record(record_id)
        return rec.narrator_ids if rec else []
