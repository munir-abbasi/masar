"""Unit tests for Isnad & Authority Hub Anchoring."""

import pytest
from masar.discovery.isnad_filter import IsnadAnchorFilter


def test_score_chain_overlap():
    """Verify Jaccard chain overlap between two isnads."""
    chain_bukhari_1 = ["al_humaydi", "sufyan", "yahya_b_said", "muhammad_b_ibrahim", "alqama_b_waqqas", "umar_b_al_khattab"]
    chain_muslim_1907 = ["ibn_qanab", "malik", "yahya_b_said", "muhammad_b_ibrahim", "alqama_b_waqqas", "umar_b_al_khattab"]

    filter_engine = IsnadAnchorFilter()
    score = filter_engine.score_chain_overlap(chain_bukhari_1, chain_muslim_1907)

    # 4 common narrators out of 8 unique -> 4/8 = 0.50
    assert score == 0.50


def test_hub_and_companion_matching():
    """Verify hub transmitter and ultimate authority companion matching."""
    chain = ["ibn_qanab", "malik", "yahya_b_said", "muhammad_b_ibrahim", "alqama_b_waqqas", "umar_b_al_khattab"]
    filter_engine = IsnadAnchorFilter()

    # Matches Yahya b. Sa'id as Common Link hub
    assert filter_engine.matches_hub(chain, ["yahya_b_said", "al_zuhri"]) is True
    assert filter_engine.matches_hub(chain, ["al_zuhri"]) is False

    # Matches Umar b. al-Khattab as Companion anchor
    assert filter_engine.matches_companion(chain, "umar_b_al_khattab") is True
    assert filter_engine.matches_companion(chain, "abu_hurairah") is False


def test_composite_anchor_score():
    """Verify composite isnad score combining overlap and anchor bonuses."""
    chain_seed = ["al_humaydi", "sufyan", "yahya_b_said", "muhammad_b_ibrahim", "alqama_b_waqqas", "umar_b_al_khattab"]
    chain_candidate = ["ibn_qanab", "malik", "yahya_b_said", "muhammad_b_ibrahim", "alqama_b_waqqas", "umar_b_al_khattab"]

    filter_engine = IsnadAnchorFilter()
    composite_score = filter_engine.score_anchors(
        candidate_chain=chain_candidate,
        seed_chain=chain_seed,
        hub_narrator_ids=["yahya_b_said"],
        companion_id="umar_b_al_khattab",
    )

    # Score should be high (overlap + hub + companion)
    assert composite_score >= 0.80
    assert composite_score <= 1.0
