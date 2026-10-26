"""First-class manual entry pipeline and heuristic isnad/matn split detector (FM-07)."""

from datetime import datetime, timezone
import hashlib
import re
from typing import Literal, Optional
from pydantic import BaseModel, Field

from masar.core.models import HadithRecord, IsnadVariant, SourceRef, SplitBoundary

# Standard Arabic transmission transition markers
ISNAD_TRANSITION_PATTERNS = [
    re.compile(r"(?:قال|يقول|سمعت)?\s*(?:قال\s+)?رسول\s+الله\s*(?:صلى\s+الله\s+عليه\s+(?:وآله\s+)?وسلم)?\s*(?:قال|يقول)?\s*[:\s]"),
    re.compile(r"(?:عن\s+)?(?:النبي|رسول\s+الله)\s*(?:صلى\s+الله\s+عليه\s+(?:وآله\s+)?وسلم)?\s*(?:قال|يقول)\s*[:\s]"),
    re.compile(r"أبي\s+عبد\s+الله\s*(?:عليه\s+السلام)?\s*قال\s*[:\s]"),
    re.compile(r"(?:قال|سمعت)\s+(?:عمر|علي|ابن\s+عباس|عائشة|أبو\s+هريرة)\s*(?:رضي\s+الله\s+عنه)?\s*(?:يقول|قال)\s*[:\s]"),
]


class ManualEntryRequest(BaseModel):
    """Payload for manually staging a hadith text into the workspace."""

    raw_text: str = Field(min_length=10, description="Full Arabic text (isnad + matn).")
    collection: str = Field(min_length=1, description="Collection or manuscript title.")
    source_type: Literal["url", "print", "manuscript", "oral_report"] = "print"
    source_locator: str = Field(min_length=1, description="Page, folio, or hadith reference.")
    hadith_number: str = Field(min_length=1, description="Sequential or manuscript report ID.")
    sect: Literal["sunni", "shia"] = "sunni"
    family_id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$", min_length=1)
    split_boundary: Optional[SplitBoundary] = None
    collector_note: Optional[str] = None


class ManualEntryPipeline:
    """Heuristic split detector and provenance builder for ad-hoc hadith texts."""

    def propose_split(self, raw_text: str) -> SplitBoundary:
        """Analyze raw Arabic text and propose initial isnad/matn boundary."""
        best_end = -1

        for pattern in ISNAD_TRANSITION_PATTERNS:
            match = pattern.search(raw_text)
            if match and match.end() > best_end:
                best_end = match.end()

        # Fallback if no explicit prophetic speech formula found
        if best_end <= 0 or best_end >= len(raw_text):
            best_end = int(len(raw_text) * 0.4)

        matn_start = best_end
        matn_end = len(raw_text)

        # Extract anchor tokens
        pre_text = raw_text[:matn_start].strip()
        pre_token = pre_text.split()[-1] if pre_text.split() else ""

        post_text = raw_text[matn_start:].strip()
        post_token = post_text.split()[0] if post_text.split() else ""

        window_start = max(0, matn_start - 20)
        window_end = min(len(raw_text), matn_start + 20)
        anchor_window = raw_text[window_start:window_end]

        return SplitBoundary(
            matn_start=matn_start,
            matn_end=matn_end,
            pre_matn_token=pre_token,
            post_isnad_token=post_token,
            anchor_window=anchor_window,
        )

    def create_record(self, req: ManualEntryRequest) -> HadithRecord:
        """Create a validated HadithRecord with full provenance and split boundary."""
        boundary = req.split_boundary or self.propose_split(req.raw_text)

        raw_isnad = req.raw_text[: boundary.matn_start].strip()
        raw_matn = req.raw_text[boundary.matn_start : boundary.matn_end].strip()

        # Generate stable, unique identifier for manual record
        text_hash = hashlib.sha256(req.raw_text.encode("utf-8")).hexdigest()[:10]
        hadith_id = f"manual_{text_hash}"

        now_iso = datetime.now(timezone.utc).isoformat()

        source_ref = SourceRef(
            collection=req.collection,
            source_type=req.source_type,
            source_locator=req.source_locator,
            ingested_at=now_iso,
            provenance_note=req.collector_note,
        )

        variant = IsnadVariant(
            variant_id=f"var_{text_hash[:6]}",
            isnad_chain=["manual_transmitter"],
            isnad_raw=raw_isnad,
            matn_raw=raw_matn,
            collector_note=req.collector_note,
            status="primary",
            matn_offset={"start": boundary.matn_start, "end": boundary.matn_end},
        )

        return HadithRecord(
            hadith_id=hadith_id,
            family_id=req.family_id,
            title=f"{req.collection} - {req.hadith_number}",
            source_ref=source_ref,
            variants=[variant],
            matn_raw=raw_matn,
        )
