"""Reviewer Persona Engine.

Per Issue Ω-3, this generates virtual reviewer feedback.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def generate_reviewer_feedback(
    vectors: list[PaperVector],
    persona: Literal["strict", "innovative", "conservative"] = "strict",
) -> dict:
    """Generate virtual reviewer feedback based on persona.

    Args:
        vectors: PaperVectors representing the manuscript.
        persona: Reviewer persona type.

    Returns:
        Feedback dict with comments.
    """
    if not vectors:
        return {
            "persona": persona,
            "overall": "評価対象なし",
            "comments": [],
        }

    # Aggregate manuscript characteristics
    avg_novelty = sum(v.temporal.novelty for v in vectors) / len(vectors)
    avg_impact = sum(v.impact.future_potential for v in vectors) / len(vectors)

    all_methods = set()
    for v in vectors:
        all_methods.update(v.method.methods.keys())

    comments = []

    if persona == "strict":
        comments.append({
            "type": "major",
            "comment": "統計解析の詳細な記述が必要",
        })
        if len(all_methods) < 2:
            comments.append({
                "type": "major",
                "comment": "手法の多角的検証が不足",
            })
        if avg_novelty < 0.5:
            comments.append({
                "type": "major",
                "comment": "新規性の主張を裏付ける追加実験が必要",
            })
        comments.append({
            "type": "minor",
            "comment": "図の解像度・表記の統一を確認",
        })

    elif persona == "innovative":
        if avg_novelty > 0.6:
            comments.append({
                "type": "positive",
                "comment": "斬新なアプローチを評価",
            })
        comments.append({
            "type": "suggestion",
            "comment": "より挑戦的な解釈を加えてはどうか",
        })
        comments.append({
            "type": "suggestion",
            "comment": "他分野への波及効果を議論に追加を推奨",
        })

    elif persona == "conservative":
        if avg_novelty > 0.7:
            comments.append({
                "type": "concern",
                "comment": "主張が大胆すぎる可能性",
            })
        comments.append({
            "type": "major",
            "comment": "先行研究との比較をより詳細に",
        })
        comments.append({
            "type": "major",
            "comment": "再現性の担保について記述を強化",
        })
        comments.append({
            "type": "minor",
            "comment": "methodologyの標準手順への準拠を確認",
        })

    # Overall assessment
    if persona == "strict":
        overall = "Major revision" if len([c for c in comments if c["type"] == "major"]) >= 2 else "Minor revision"
    elif persona == "innovative":
        overall = "Accept with minor revision" if avg_novelty > 0.5 else "Minor revision"
    else:
        overall = "Major revision" if avg_novelty > 0.6 else "Minor revision"

    return {
        "persona": persona,
        "overall": overall,
        "comments": comments,
        "novelty_score": round(avg_novelty, 2),
        "impact_score": round(avg_impact, 2),
    }


def generate_all_reviewer_feedback(vectors: list[PaperVector]) -> list[dict]:
    """Generate feedback from all three reviewer personas."""
    return [
        generate_reviewer_feedback(vectors, "strict"),
        generate_reviewer_feedback(vectors, "innovative"),
        generate_reviewer_feedback(vectors, "conservative"),
    ]
