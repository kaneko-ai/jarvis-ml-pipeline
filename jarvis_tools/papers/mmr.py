"""MMR - Maximal Marginal Relevance.

Per RP-14, provides diversity-aware reranking.
"""
from __future__ import annotations

from typing import List, Tuple


def jaccard_similarity(tokens1: set, tokens2: set) -> float:
    """Compute Jaccard similarity."""
    if not tokens1 or not tokens2:
        return 0.0
    return len(tokens1 & tokens2) / len(tokens1 | tokens2)


def mmr_rerank(
    query_tokens: set,
    candidates: List[Tuple[int, float, set]],  # (idx, score, tokens)
    lambda_param: float = 0.5,
    top_k: int = 10,
) -> List[Tuple[int, float]]:
    """Rerank candidates using MMR.

    Args:
        query_tokens: Query tokens.
        candidates: List of (idx, score, tokens).
        lambda_param: Balance between relevance (1.0) and diversity (0.0).
        top_k: Number to return.

    Returns:
        Reranked (idx, score) list.
    """
    if not candidates:
        return []

    selected: List[Tuple[int, float, set]] = []
    remaining = list(candidates)

    while remaining and len(selected) < top_k:
        best_idx = -1
        best_score = float("-inf")

        for i, (idx, orig_score, tokens) in enumerate(remaining):
            # Relevance to query
            relevance = orig_score

            # Diversity from selected
            if selected:
                max_sim = max(jaccard_similarity(tokens, s[2]) for s in selected)
            else:
                max_sim = 0.0

            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = i

        if best_idx >= 0:
            selected.append(remaining.pop(best_idx))

    return [(idx, score) for idx, score, _ in selected]
