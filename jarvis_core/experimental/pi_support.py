"""PI-Level Decision Support Mode.

Per Issue Ω-10, this supports PI-level research decisions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def evaluate_research_themes(
    theme_vectors: dict[str, list[PaperVector]],
) -> list[dict]:
    """Evaluate multiple research themes for continue/stop decision.

    Args:
        theme_vectors: Dict mapping theme names to their PaperVectors.

    Returns:
        List of theme evaluations with recommendations.
    """
    evaluations = []

    for theme, vectors in theme_vectors.items():
        eval_result = _evaluate_single_theme(theme, vectors)
        evaluations.append(eval_result)

    # Sort by overall score
    evaluations.sort(key=lambda x: x["overall_score"], reverse=True)

    return evaluations


def _evaluate_single_theme(theme: str, vectors: list[PaperVector]) -> dict:
    """Evaluate a single research theme."""
    if not vectors:
        return {
            "theme": theme,
            "overall_score": 0.0,
            "recommendation": "stop",
            "reason": "データ不足",
            "estimated": True,
        }

    # Calculate metrics
    avg_novelty = sum(v.temporal.novelty for v in vectors) / len(vectors)
    avg_impact = sum(v.impact.future_potential for v in vectors) / len(vectors)

    # Recent progress (papers in last 2 years)
    recent = [v for v in vectors if (v.metadata.year or 0) >= 2022]
    momentum = len(recent) / len(vectors)

    # Resource efficiency (method overlap)
    all_methods = set()
    for v in vectors:
        all_methods.update(v.method.methods.keys())
    efficiency = 1 / (1 + len(all_methods) / 10)  # More methods = less efficient

    # Overall score
    overall = 0.3 * avg_novelty + 0.3 * avg_impact + 0.2 * momentum + 0.2 * efficiency
    overall = round(min(1.0, overall), 3)

    # Recommendation
    if overall >= 0.6:
        recommendation = "continue"
        reason = "高いポテンシャルと進捗"
    elif overall >= 0.4:
        recommendation = "review"
        reason = "方向性の見直しを推奨"
    else:
        recommendation = "stop"
        reason = "リソース再配分を検討"

    return {
        "theme": theme,
        "overall_score": overall,
        "metrics": {
            "novelty": round(avg_novelty, 2),
            "impact": round(avg_impact, 2),
            "momentum": round(momentum, 2),
            "efficiency": round(efficiency, 2),
        },
        "recommendation": recommendation,
        "reason": reason,
        "paper_count": len(vectors),
        "estimated": True,
    }


def generate_pi_summary(evaluations: list[dict]) -> str:
    """Generate PI-level summary of all themes."""
    lines = ["# 研究テーマ評価サマリー", ""]

    continue_themes = [e for e in evaluations if e["recommendation"] == "continue"]
    review_themes = [e for e in evaluations if e["recommendation"] == "review"]
    stop_themes = [e for e in evaluations if e["recommendation"] == "stop"]

    lines.append(f"## 継続推奨 ({len(continue_themes)}テーマ)")
    for e in continue_themes:
        lines.append(f"- {e['theme']}: スコア {e['overall_score']}")
    lines.append("")

    lines.append(f"## 見直し推奨 ({len(review_themes)}テーマ)")
    for e in review_themes:
        lines.append(f"- {e['theme']}: {e['reason']}")
    lines.append("")

    lines.append(f"## 中止検討 ({len(stop_themes)}テーマ)")
    for e in stop_themes:
        lines.append(f"- {e['theme']}: {e['reason']}")

    return "\n".join(lines)
