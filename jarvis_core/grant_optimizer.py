"""Grant / Fellowship Optimizer.

Per Issue Ω-2, this estimates grant success probability.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def optimize_grant_proposal(
    research_vectors: list[PaperVector],
    grant_keywords: list[str],
    grant_type: str = "general",
) -> dict:
    """Estimate grant/fellowship success probability.

    Args:
        research_vectors: PaperVectors representing the research.
        grant_keywords: Keywords from grant call.
        grant_type: Type of grant (general, exploratory, etc).

    Returns:
        Optimization result with score and recommendations.
    """
    if not research_vectors:
        return {
            "score": 0.0,
            "reason": "研究実績なし",
            "risks": ["実績不足"],
            "estimated": True,
        }

    # Calculate alignment score
    alignment = 0.0
    matched_concepts = []

    for kw in grant_keywords:
        kw_lower = kw.lower()
        for v in research_vectors:
            for c in v.concept.concepts:
                if kw_lower in c.lower():
                    alignment += v.concept.concepts[c]
                    matched_concepts.append(c)
                    break

    alignment = min(1.0, alignment / max(len(grant_keywords), 1))

    # Calculate novelty bonus
    avg_novelty = sum(v.temporal.novelty for v in research_vectors) / len(research_vectors)

    # Calculate impact potential
    avg_impact = sum(v.impact.future_potential for v in research_vectors) / len(research_vectors)

    # Final score
    score = 0.4 * alignment + 0.3 * avg_novelty + 0.3 * avg_impact
    score = round(min(1.0, score), 3)

    # Generate reasons
    reasons = []
    if alignment > 0.6:
        reasons.append("募集要項との高い整合性")
    if avg_novelty > 0.6:
        reasons.append("高い新規性")
    if avg_impact > 0.6:
        reasons.append("高いインパクトポテンシャル")

    # Identify risks
    risks = []
    if alignment < 0.4:
        risks.append("募集要項とのミスマッチ")
    if avg_novelty < 0.4:
        risks.append("新規性の訴求不足")
    if len(research_vectors) < 3:
        risks.append("予備データ不足")

    return {
        "score": score,
        "reason": "、".join(reasons) if reasons else "標準的な適合度",
        "risks": risks,
        "alignment": round(alignment, 3),
        "novelty": round(avg_novelty, 3),
        "impact": round(avg_impact, 3),
        "matched_concepts": list(set(matched_concepts)),
        "estimated": True,
    }


def suggest_grant_improvements(result: dict) -> list[str]:
    """Suggest improvements for grant proposal."""
    suggestions = []

    if result.get("alignment", 0) < 0.5:
        suggestions.append("募集要項のキーワードを研究計画に明示的に組み込む")

    if result.get("novelty", 0) < 0.5:
        suggestions.append("独自性・差別化ポイントを強調する")

    if "予備データ不足" in result.get("risks", []):
        suggestions.append("パイロットスタディの結果を追加する")

    if not suggestions:
        suggestions.append("現状維持で競争力あり")

    return suggestions
