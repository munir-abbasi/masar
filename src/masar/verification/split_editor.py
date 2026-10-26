"""Boundary adjustment, heuristic bleed guard, and dual anchor-offset editor (FM-01, ADR D012)."""

import re
from typing import Optional
from pydantic import BaseModel
from masar.core.models import SplitBoundary

# Regex patterns for common isnad transmission formulas mistakenly captured in matn
BLEED_PREFIX_PATTERNS = [
    re.compile(r"^(?:قال\s+)*قال\s+رسول\s+الله\s*(?:صلى\s+الله\s+عليه\s+(?:وآله\s+)?وسلم)?\s*(?:يقول|قال)?\s*[:\s]*"),
    re.compile(r"^(?:عن\s+)?(?:النبي|رسول\s+الله)\s*(?:صلى\s+الله\s+عليه\s+(?:وآله\s+)?وسلم)?\s*(?:قال|يقول)\s*[:\s]*"),
    re.compile(r"^سمعت\s+[\w\s]+?(?:يقول|قال)\s*[:\s]*"),
    re.compile(r"^(?:حدثنا|أخبرنا|أنبأنا)\s+[\w\s]+?(?:قال|عن)\s*[:\s]*"),
]


class BleedDiagnostic(BaseModel):
    """Diagnostic report indicating presence of boundary bleed in matn."""

    has_bleed: bool
    detected_prefix: Optional[str] = None
    bleed_length: int = 0
    reason: Optional[str] = None


class HeuristicBoundaryGuard:
    """Detects when isnad transmission formulas have bled into the matn."""

    def detect_bleed(self, matn_text: str) -> BleedDiagnostic:
        """Inspect the leading tokens of a matn for isnad connectors."""
        stripped = matn_text.strip()
        for pattern in BLEED_PREFIX_PATTERNS:
            match = pattern.match(stripped)
            if match:
                prefix = match.group(0)
                # Compute length in original matn (accounting for leading whitespace)
                leading_spaces = len(matn_text) - len(matn_text.lstrip())
                total_len = leading_spaces + len(prefix)
                return BleedDiagnostic(
                    has_bleed=True,
                    detected_prefix=prefix.strip(),
                    bleed_length=total_len,
                    reason=f"Isnad connector formula detected at matn start: '{prefix.strip()}'",
                )

        return BleedDiagnostic(
            has_bleed=False,
            detected_prefix=None,
            bleed_length=0,
            reason=None,
        )


class SplitEditor:
    """Adjusts and repairs isnad/matn boundaries with dual token-anchor preservation."""

    def __init__(self):
        self.guard = HeuristicBoundaryGuard()

    def _extract_anchors(
        self,
        full_text: str,
        matn_start: int,
    ) -> tuple[str, str, str]:
        """Extract pre-matn token, post-isnad token, and bridging window."""
        pre_text = full_text[:matn_start].strip()
        pre_token = pre_text.split()[-1] if pre_text.split() else ""

        post_text = full_text[matn_start:].strip()
        post_token = post_text.split()[0] if post_text.split() else ""

        w_start = max(0, matn_start - 25)
        w_end = min(len(full_text), matn_start + 25)
        window = full_text[w_start:w_end]

        return pre_token, post_token, window

    def adjust_split(
        self,
        full_text: str,
        new_start: int,
        new_end: int,
    ) -> SplitBoundary:
        """Explicitly set boundaries and calculate dual token anchors."""
        pre_tok, post_tok, win = self._extract_anchors(full_text, new_start)
        return SplitBoundary(
            matn_start=new_start,
            matn_end=new_end,
            pre_matn_token=pre_tok,
            post_isnad_token=post_tok,
            anchor_window=win,
        )

    def repair_split(
        self,
        full_text: str,
        current_boundary: SplitBoundary,
    ) -> SplitBoundary:
        """Automatically detect and trim boundary bleed from the matn."""
        current_matn = full_text[current_boundary.matn_start : current_boundary.matn_end]
        diag = self.guard.detect_bleed(current_matn)

        if not diag.has_bleed:
            return current_boundary

        clean_start = current_boundary.matn_start + diag.bleed_length
        # Advance past any leftover punctuation or spaces
        while clean_start < current_boundary.matn_end and full_text[clean_start] in " :،؛":
            clean_start += 1

        return self.adjust_split(full_text, clean_start, current_boundary.matn_end)
