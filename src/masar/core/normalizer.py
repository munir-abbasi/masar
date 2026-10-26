"""Arabic orthography normalization and tokenization substrate.

Provides high-precision normalization for lexical search (BM25) and
pericope alignment (Jaccard sliding window).
"""

import re
import unicodedata

# Unicode ranges for Arabic diacritics / tashkeel and Quranic annotations
TASHKEEL_REGEX = re.compile(
    r"[\u064B-\u0652\u0653-\u065F\u0670\u06D6-\u06ED]"
)

# Tatweel / Kashida
TATWEEL_REGEX = re.compile(r"\u0640")

# Alif variants: أ, إ, آ, ٱ -> ا
ALIF_REGEX = re.compile(r"[\u0622\u0623\u0625\u0671]")

# Punctuation and non-word separators (Arabic and Latin)
PUNCT_REGEX = re.compile(r"[،؛؟«»!\"#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~]")

# Honorific ligatures
LIGATURE_MAP = {
    "\ufdfa": "",  # ﷺ
    "\ufdfb": "",  # ﷻ
}


def strip_tashkeel(text: str) -> str:
    """Remove Arabic diacritics (harakat, tanween, shaddah, sukun, dagger alif)."""
    if not text:
        return ""
    return TASHKEEL_REGEX.sub("", text)


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text to a canonical form for matching.

    - Strips tashkeel and tatweel
    - Replaces ligatures
    - Normalizes alif forms (أ, إ, آ, ٱ) -> ا
    - Normalizes alif maqsura (ى) -> ي
    - Normalizes ta marbuta (ة) -> ه
    - Normalizes hamza on ya (ئ) -> ي
    """
    if not text:
        return ""

    # 1. Normalize unicode NFKC
    res = unicodedata.normalize("NFKC", text)

    # 2. Strip diacritics and tatweel
    res = strip_tashkeel(res)
    res = TATWEEL_REGEX.sub("", res)

    # 3. Replace ligatures
    for lig, replacement in LIGATURE_MAP.items():
        res = res.replace(lig, replacement)

    # 4. Normalize letter variants
    res = ALIF_REGEX.sub("ا", res)
    res = res.replace("ى", "ي")
    res = res.replace("ة", "ه")
    res = res.replace("ئ", "ي")

    return res.strip()


def tokenize_arabic(text: str) -> list[str]:
    """Normalize and tokenize Arabic text into discrete word tokens."""
    if not text:
        return []

    cleaned = PUNCT_REGEX.sub(" ", text)
    normalized = normalize_arabic(cleaned)
    tokens = [tok for tok in normalized.split() if tok]
    return tokens
