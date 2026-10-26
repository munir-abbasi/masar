"""Transmitter chain overlap and Common Link / authority anchoring."""

from typing import Optional


class IsnadAnchorFilter:
    """Filters and scores candidate isnad chains based on transmitter overlap and anchor hubs."""

    def score_chain_overlap(self, chain_a: list[str], chain_b: list[str]) -> float:
        """Calculate Jaccard overlap between two isnad transmitter chains."""
        if not chain_a or not chain_b:
            return 0.0
        set_a = set(chain_a)
        set_b = set(chain_b)
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return round(intersection / union, 4) if union > 0 else 0.0

    def matches_hub(self, candidate_chain: list[str], hub_narrator_ids: list[str]) -> bool:
        """Check if candidate chain passes through any designated Common Link hub."""
        if not candidate_chain or not hub_narrator_ids:
            return False
        return bool(set(candidate_chain) & set(hub_narrator_ids))

    def matches_companion(self, candidate_chain: list[str], companion_id: str) -> bool:
        """Check if candidate chain terminates at the specified ultimate authority / Companion."""
        if not candidate_chain or not companion_id:
            return False
        return companion_id in candidate_chain

    def score_anchors(
        self,
        candidate_chain: list[str],
        seed_chain: Optional[list[str]] = None,
        hub_narrator_ids: Optional[list[str]] = None,
        companion_id: Optional[str] = None,
    ) -> float:
        """Compute composite isnad confidence score combining overlap and anchor matches."""
        overlap = self.score_chain_overlap(seed_chain, candidate_chain) if seed_chain else 0.0
        hub_bonus = 0.25 if hub_narrator_ids and self.matches_hub(candidate_chain, hub_narrator_ids) else 0.0
        comp_bonus = 0.25 if companion_id and self.matches_companion(candidate_chain, companion_id) else 0.0

        total = overlap + hub_bonus + comp_bonus
        return round(min(1.0, max(0.0, total)), 4)
