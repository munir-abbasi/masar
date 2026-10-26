"""Data contracts, explainability receipts, and Riwaq schema models.

Implements Pydantic V2 contracts for discovery, explainability receipts,
boundary editing, and Riwaq export serialization.
"""

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class TakhrijQuery(BaseModel):
    """Multi-modal query specification (ADR D013)."""

    seed_text: Optional[str] = Field(
        default=None,
        description="Seed matn or text snippet to find variants for.",
    )
    hadith_id: Optional[str] = Field(
        default=None,
        description="Optional corpus hadith identifier to use as seed.",
    )
    family_id: Optional[str] = Field(
        default=None,
        description="Optional family ID when enriching an existing tradition bundle.",
    )
    companion_id: Optional[str] = Field(
        default=None,
        description="Ultimate transmitter / Companion anchor identifier.",
    )
    hub_narrator_ids: list[str] = Field(
        default_factory=list,
        description="Key 2nd-century Common Link / authority narrator IDs to anchor search.",
    )
    scope: Literal["all", "sunni", "shia"] = Field(
        default="all",
        description="Sectarian corpus scoping: all collections, Sunni only, or Shīʿī only.",
    )
    min_pericope_threshold: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Minimum sliding-window Jaccard score for taqṭīʿ alignment.",
    )
    semantic_top_k: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Number of candidate records to rank using dense embeddings.",
    )


class SplitBoundary(BaseModel):
    """Dual anchor-offset boundary representation (ADR D012)."""

    matn_start: int = Field(
        ge=0,
        description="Zero-based character start index of matn in full_text.",
    )
    matn_end: int = Field(
        ge=0,
        description="Zero-based character end index of matn in full_text.",
    )
    pre_matn_token: Optional[str] = Field(
        default=None,
        description="Leading token anchor immediately preceding matn.",
    )
    post_isnad_token: Optional[str] = Field(
        default=None,
        description="Trailing token anchor immediately following isnad.",
    )
    anchor_window: Optional[str] = Field(
        default=None,
        description="Small text snippet bridging the isnad-matn boundary.",
    )

    @field_validator("matn_end")
    @classmethod
    def validate_boundary_span(cls, v: int, info) -> int:
        start = info.data.get("matn_start")
        if start is not None and v <= start:
            raise ValueError(f"matn_end ({v}) must be strictly greater than matn_start ({start})")
        return v


class SignalScores(BaseModel):
    """Orthogonal 4-signal decomposition of takhrīj matching confidence."""

    bm25_lexical: float = Field(
        ge=0.0,
        description="Normalized lexical match score (0.0 - 1.0).",
    )
    pericope_jaccard: float = Field(
        ge=0.0,
        le=1.0,
        description="Sliding-window Jaccard score for taqṭīʿ (0.0 - 1.0).",
    )
    semantic_cosine: float = Field(
        ge=-1.0,
        le=1.0,
        description="Dense embedding cosine similarity for riwāyah bi-l-maʿnā (-1.0 to 1.0).",
    )
    isnad_overlap: float = Field(
        ge=0.0,
        le=1.0,
        description="Jaccard or graph path overlap of transmitter chains (0.0 - 1.0).",
    )


class ExplainabilityReceipt(BaseModel):
    """Immutable audit receipt explaining why a candidate was ranked or quarantined."""

    candidate_id: str = Field(description="Unique candidate record ID.")
    ensemble_score: float = Field(description="Weighted multi-signal score (0.0 - 1.0).")
    signal_scores: SignalScores = Field(description="Decomposed 4 signal scores.")
    is_topical_false_positive: bool = Field(
        default=False,
        description="True if quarantined due to high semantic similarity without lexical/isnad support.",
    )
    quarantine_reason: Optional[str] = Field(
        default=None,
        description="Explanation for quarantine if flagged as topical false positive.",
    )
    pericope_spans: Optional[list[tuple[int, int]]] = Field(
        default=None,
        description="Aligned character spans (start, end) within candidate text.",
    )


class CandidateRecord(BaseModel):
    """A hadith candidate retrieved during takhrīj discovery."""

    id: str = Field(description="Unique hadith ID.")
    collection: str = Field(description="Collection name (e.g. Sahih al-Bukhari).")
    book_number: Optional[int] = Field(default=None)
    hadith_number: str = Field(description="Hadith number within collection.")
    sect: Literal["sunni", "shia"] = Field(description="Sectarian attribution.")
    full_text: Optional[str] = Field(default=None)
    matn: str = Field(description="Matn text.")
    isnad_raw: Optional[str] = Field(default=None)
    narrator_ids: list[str] = Field(default_factory=list)
    receipt: Optional[ExplainabilityReceipt] = Field(default=None)


# ---------------------------------------------------------------------------
# Riwaq Interop Models (Target schema_version: 1)
# ---------------------------------------------------------------------------

class SourceRef(BaseModel):
    """Structured provenance for a hadith record conforming to Riwaq schema."""

    collection: str = Field(min_length=1)
    source_type: Literal["url", "print", "manuscript", "oral_report"]
    source_locator: str = Field(min_length=1)
    ingested_at: str
    external_record_id: Optional[str] = None
    provenance_note: Optional[str] = None
    transcription_standard: Optional[str] = None
    parser_version: Optional[str] = None
    checksum: Optional[str] = None


class IsnadVariant(BaseModel):
    """Variant chain representation conforming to Riwaq schema."""

    variant_id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$", min_length=1, max_length=128)
    isnad_chain: list[str] = Field(min_length=1)
    isnad_raw: Optional[str] = None
    matn_raw: Optional[str] = None
    collector_note: Optional[str] = None
    provenance: Optional[dict[str, Any]] = None
    status: Optional[Literal["primary", "variant", "fragment", "defective"]] = None
    matn_offset: Optional[dict[str, int]] = None


class HadithRecord(BaseModel):
    """Canonical HadithRecord conforming to Riwaq schema_version: 1."""

    hadith_id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$", min_length=1, max_length=128)
    family_id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$", min_length=1, max_length=128)
    title: Optional[str] = None
    source_ref: SourceRef
    variants: list[IsnadVariant] = Field(min_length=1)
    matn_raw: Optional[str] = None
    reliability_evidence: list[dict[str, Any]] = Field(default_factory=list)


class ImportBatch(BaseModel):
    """Top-level Riwaq ImportBatch payload conforming to import-batch.json."""

    schema_version: Literal[1] = 1
    imported_at: str
    import_id: Optional[str] = Field(default=None, max_length=64)
    source_batch_ref: Optional[str] = Field(default=None, max_length=512)
    records: list[HadithRecord] = Field(min_length=1)
    narrators: list[dict[str, Any]] = Field(default_factory=list)
