"""Unit tests for dense semantic similarity search and Riwāyah bi-l-Maʿnā."""

import time
import pytest
from masar.discovery.semantic_search import SemanticMatcher


def test_semantic_similarity_synonyms():
    """Verify that synonymous Arabic sentences with zero lexical overlap achieve high cosine similarity."""
    sent_a = "ذهب المسافر مسرعا إلى داره"
    sent_b = "انطلق المرء حثيثا نحو بيته"

    matcher = SemanticMatcher()
    sim = matcher.similarity(sent_a, sent_b)

    assert sim >= 0.70, f"Expected high semantic similarity for synonyms, got {sim}"


def test_semantic_similarity_unrelated():
    """Verify that semantically unrelated sentences yield low cosine similarity."""
    sent_a = "إنما الأعمال بالنيات ولكل امرئ ما نوى"
    sent_c = "هو الطهور ماؤه الحل ميتته في صيد البحر"

    matcher = SemanticMatcher()
    sim = matcher.similarity(sent_a, sent_c)

    assert sim < 0.40, f"Expected low similarity for unrelated reports, got {sim}"


def test_batch_encoding_performance():
    """Verify sub-80ms batch encoding on CPU."""
    matcher = SemanticMatcher()
    batch = [
        "إنما الأعمال بالنيات",
        "الأعمال بالخواتيم",
        "طلب العلم فريضة",
        "لا ضرر ولا ضرار",
        "المسلم من سلم المسلمون من لسانه ويده",
    ] * 2  # 10 items

    t0 = time.perf_counter()
    vectors = matcher.encode_batch(batch)
    duration_ms = (time.perf_counter() - t0) * 1000

    assert len(vectors) == 10
    assert duration_ms < 80.0, f"Encoding batch took {duration_ms}ms, exceeding 80ms budget"
