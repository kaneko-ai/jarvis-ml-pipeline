"""Experiment Feasibility Scorer.

Per RP45, this scores experimental feasibility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def score_feasibility(
    hypothesis: str,
    vectors: list[PaperVector],
) -> dict:
    """Score experimental feasibility for a hypothesis.

    Scores:
    - difficulty: 0 (easy) to 1 (hard)
    - cost: 0 (cheap) to 1 (expensive)
    - reproducibility: 0 (low) to 1 (high)

    Args:
        hypothesis: The hypothesis to test.
        vectors: PaperVectors for context.

    Returns:
        Feasibility score dict.
    """
    if not hypothesis:
        return {
            "difficulty": 0.5,
            "cost": 0.5,
            "reproducibility": 0.5,
            "overall": 0.5,
            "reason": "仮説が不明",
        }

    # Find related papers
    hypothesis_lower = hypothesis.lower()
    related = []
    for v in vectors:
        for c in v.concept.concepts:
            if c.lower() in hypothesis_lower or hypothesis_lower in c.lower():
                related.append(v)
                break

    # Base scores
    difficulty = 0.7
    cost = 0.5
    reproducibility = 0.3

    # Adjust based on related papers
    if related:
        # More related papers = easier (precedent exists)
        difficulty = max(0.2, 0.7 - 0.1 * min(len(related), 5))

        # Check methods used
        method_counts = {}
        for v in related:
            for m in v.method.methods:
                method_counts[m] = method_counts.get(m, 0) + 1

        # Common methods = higher reproducibility
        if method_counts:
            max_count = max(method_counts.values())
            reproducibility = min(1.0, 0.3 + 0.1 * max_count)

        # Expensive methods increase cost
        expensive_methods = ["scRNA-seq", "mass spectrometry", "CRISPR"]
        for m in method_counts:
            if m in expensive_methods:
                cost = min(1.0, cost + 0.15)

    # Overall score (lower is better for difficulty/cost, higher for reproducibility)
    overall = (1 - difficulty) * 0.3 + (1 - cost) * 0.3 + reproducibility * 0.4
    overall = max(0, min(1, overall))

    # Generate reason
    reason_parts = []
    if difficulty < 0.4:
        reason_parts.append("先行研究が充実")
    elif difficulty > 0.6:
        reason_parts.append("技術的難度が高い")

    if cost > 0.7:
        reason_parts.append("高コスト手法が必要")
    if reproducibility > 0.6:
        reason_parts.append("再現性が期待できる")

    reason = "、".join(reason_parts) if reason_parts else "標準的な実験難度"

    return {
        "difficulty": round(difficulty, 3),
        "cost": round(cost, 3),
        "reproducibility": round(reproducibility, 3),
        "overall": round(overall, 3),
        "reason": reason,
        "related_papers": len(related),
    }
