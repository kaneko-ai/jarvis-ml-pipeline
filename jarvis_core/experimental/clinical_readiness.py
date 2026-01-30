"""Clinical Translation Readiness Score.

Per Ψ-5, this evaluates clinical translation readiness.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


# Clinical translation levels
TRANSLATION_LEVELS = {
    0: "基礎研究段階",
    1: "概念実証完了",
    2: "前臨床モデルで検証中",
    3: "臨床試験準備中",
    4: "臨床試験中",
    5: "臨床応用段階",
}


def assess_clinical_readiness(
    vectors: list[PaperVector],
) -> dict:
    """Assess clinical translation readiness.

    Args:
        vectors: PaperVectors representing research.

    Returns:
        Clinical readiness assessment.
    """
    if not vectors:
        return {
            "readiness_level": 0,
            "level_description": TRANSLATION_LEVELS[0],
            "blockers": ["研究データ不足"],
            "estimated": True,
        }

    blockers = []

    # Check human-relevant data
    has_human = any("human" in str(v.metadata.species).lower() for v in vectors)
    if not has_human:
        blockers.append("ヒトデータなし")

    # Check model diversity
    species = set()
    for v in vectors:
        species.update(v.metadata.species)
    if len(species) < 2:
        blockers.append("モデル系の多様性不足")

    # Check method rigor
    rigorous_methods = ["clinical trial", "patient", "GMP", "FDA"]
    has_rigorous = any(
        any(rm.lower() in m.lower() for rm in rigorous_methods)
        for v in vectors
        for m in v.method.methods
    )

    # Determine level
    if has_rigorous:
        level = 4
    elif has_human:
        level = 3
    elif len(species) >= 2:
        level = 2
    elif len(vectors) >= 3:
        level = 1
    else:
        level = 0

    # Add blockers based on level
    if level < 3:
        blockers.append("臨床関連データの蓄積が必要")
    if level < 2:
        blockers.append("追加のモデル系での検証が必要")

    return {
        "readiness_level": level,
        "level_description": TRANSLATION_LEVELS[level],
        "blockers": blockers,
        "has_human_data": has_human,
        "model_count": len(species),
        "estimated": True,
    }
