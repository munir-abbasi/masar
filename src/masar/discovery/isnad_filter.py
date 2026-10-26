"""Transmitter chain overlap, Common Link anchoring, and Homonym Disambiguation (FM-02)."""

from typing import Optional


def _resolve_sufyan(student: Optional[str], teacher: Optional[str]) -> tuple[str, Optional[str]]:
    """Disambiguate 'sufyan' based on student or teacher edges."""
    uyaynah_students = {"al_humaydi", "al_shafii", "ali_b_al_madini", "musaddad"}
    thawri_students = {"waki", "yahya_al_qattan", "abd_al_rahman_b_mahdi", "abu_nuaym"}

    if student in uyaynah_students:
        return "sufyan_b_uyaynah", None
    if student in thawri_students:
        return "sufyan_al_thawri", None

    warning = "Ambiguous transmitter 'sufyan': could be Sufyan al-Thawri or Sufyan b. Uyaynah"
    return "sufyan", warning


def _resolve_hammad(student: Optional[str], teacher: Optional[str]) -> tuple[str, Optional[str]]:
    """Disambiguate 'hammad' based on student or teacher edges."""
    salamah_teachers = {"thabit", "anas", "qatadah"}
    zaid_teachers = {"amr_b_dinar", "ayyoub"}

    if teacher in salamah_teachers:
        return "hammad_b_salamah", None
    if teacher in zaid_teachers:
        return "hammad_b_zaid", None

    warning = "Ambiguous transmitter 'hammad': could be Hammad b. Salamah or Hammad b. Zayd"
    return "hammad", warning


class HomonymDisambiguator:
    """Disambiguates shared classical transmitter names via prosopographical graph edges."""

    def disambiguate_chain(self, chain: list[str]) -> tuple[list[str], list[str]]:
        """Resolve ambiguous names in isnad chain using adjacent student/teacher context."""
        resolved: list[str] = []
        warnings: list[str] = []

        for i, narrator in enumerate(chain):
            student = chain[i - 1] if i > 0 else None
            teacher = chain[i + 1] if i + 1 < len(chain) else None

            if narrator == "sufyan":
                canon_id, warn = _resolve_sufyan(student, teacher)
            elif narrator == "hammad":
                canon_id, warn = _resolve_hammad(student, teacher)
            else:
                canon_id, warn = narrator, None

            resolved.append(canon_id)
            if warn:
                warnings.append(warn)

        return resolved, warnings


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
