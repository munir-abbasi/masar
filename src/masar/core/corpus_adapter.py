"""Corpus Adapter interface for pluggable hadith storage backends (ADR D010)."""

from typing import Iterator, Optional, Protocol, runtime_checkable
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
