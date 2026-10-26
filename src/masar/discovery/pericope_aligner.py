"""Pericope sliding-window alignment for detecting fragmented hadiths / Taqṭīʿ (FM-04)."""

from pydantic import BaseModel
from masar.core.normalizer import tokenize_arabic


class PericopeMatch(BaseModel):
    """Result of sliding-window pericope alignment."""

    max_jaccard: float
    global_jaccard: float
    start_token_idx: int
    end_token_idx: int
    matched_snippet: str


def _compute_jaccard(tokens_a: set[str], tokens_b: set[str]) -> float:
    """Compute Jaccard similarity index between two token sets."""
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union if union > 0 else 0.0


def _find_best_window(
    seed_set: set[str],
    seed_len: int,
    target_tokens: list[str],
    window_step: int,
) -> tuple[float, int, int]:
    """Slide window over target tokens and find maximal Jaccard span."""
    best_jaccard = 0.0
    best_start = 0
    best_end = len(target_tokens)

    # Test window lengths around seed_len
    min_w = max(1, seed_len - 2)
    max_w = min(len(target_tokens), seed_len + 3)

    for w in range(min_w, max_w + 1):
        for i in range(0, len(target_tokens) - w + 1, window_step):
            win_set = set(target_tokens[i : i + w])
            score = _compute_jaccard(seed_set, win_set)
            if score > best_jaccard:
                best_jaccard = score
                best_start = i
                best_end = i + w

    return best_jaccard, best_start, best_end


class PericopeAligner:
    """Sliding-window aligner matching fragmented matns against longer traditions."""

    def align(
        self,
        seed_text: str,
        target_text: str,
        window_step: int = 1,
    ) -> PericopeMatch:
        """Align seed excerpt against target text and return maximal local match."""
        seed_tokens = tokenize_arabic(seed_text)
        target_tokens = tokenize_arabic(target_text)

        if not seed_tokens or not target_tokens:
            return PericopeMatch(
                max_jaccard=0.0,
                global_jaccard=0.0,
                start_token_idx=0,
                end_token_idx=0,
                matched_snippet="",
            )

        seed_set = set(seed_tokens)
        target_set = set(target_tokens)
        global_score = round(_compute_jaccard(seed_set, target_set), 4)

        if len(target_tokens) <= len(seed_tokens):
            return PericopeMatch(
                max_jaccard=global_score,
                global_jaccard=global_score,
                start_token_idx=0,
                end_token_idx=len(target_tokens),
                matched_snippet=" ".join(target_tokens),
            )

        best_score, start_idx, end_idx = _find_best_window(
            seed_set, len(seed_tokens), target_tokens, window_step
        )

        matched_snippet = " ".join(target_tokens[start_idx:end_idx])

        return PericopeMatch(
            max_jaccard=round(best_score, 4),
            global_jaccard=global_score,
            start_token_idx=start_idx,
            end_token_idx=end_idx,
            matched_snippet=matched_snippet,
        )
