"""Unit tests for Arabic orthography normalization and tokenization substrate."""

import pytest
from masar.core.normalizer import normalize_arabic, tokenize_arabic, strip_tashkeel


def test_strip_tashkeel():
    """Verify that all Arabic harakat, shaddah, and tanween are stripped."""
    text_with_diacritics = "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَىٰ"
    expected = "إنما الأعمال بالنيات، وإنما لكل امرئ ما نوى"
    assert strip_tashkeel(text_with_diacritics) == expected


def test_normalize_alifs_and_hamza():
    """Verify that all alif variants (أ، إ، آ، ٱ) normalize to bare alif (ا)."""
    text = "أَكَلَ إِبْرَاهِيمُ آخِرَ ٱلتَّمْرِ"
    normalized = normalize_arabic(text)
    assert "اكل" in normalized
    assert "ابراهيم" in normalized
    assert "اخر" in normalized
    assert "التمر" in normalized


def test_normalize_ta_marbuta_and_ha():
    """Verify ta marbuta (ة) maps to ha (ه) for robust lexical matching."""
    text = "هجرته إلى دنيا يصيبها أو امرأة ينكحها"
    normalized = normalize_arabic(text)
    assert "امراه" in normalized
    assert "هجرته" in normalized


def test_normalize_alif_maqsura_and_ya():
    """Verify alif maqsura (ى) maps to ya (ي)."""
    text = "ما نوى فمن غزا ابتغاء ما عند الله"
    normalized = normalize_arabic(text)
    assert "نوي" in normalized


def test_strip_tatweel_and_ligatures():
    """Verify kashida/tatweel and unicode honorific ligatures are cleaned."""
    text = "قالَ النَّبِيُّ ﷺ: كَتَبَـنَا ذَلِكَ"
    normalized = normalize_arabic(text)
    # Kashida removed
    assert "كتبنا" in normalized
    # Ligature ﷺ handled (either stripped or normalized)
    assert "ﷺ" not in normalized


def test_tokenize_arabic():
    """Verify tokenization splits words, strips punctuation, and normalizes."""
    raw_hadith = "إنما الأعمالُ بالنياتِ! وإنما لكلِّ امرئٍ ما نوى."
    tokens = tokenize_arabic(raw_hadith)
    expected_tokens = ["انما", "الاعمال", "بالنيات", "وانما", "لكل", "امري", "ما", "نوي"]
    assert tokens == expected_tokens
