"""Lab-to-Startup Translation Engine.

Per Ψ-4, this translates research to business hypotheses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def translate_to_startup(
    vectors: list[PaperVector],
    technology_focus: str = "",
) -> dict:
    """Translate research findings to startup hypothesis.

    Args:
        vectors: PaperVectors representing research.
        technology_focus: Optional technology focus.

    Returns:
        Startup translation analysis.
    """
    if not vectors:
        return {
            "startup_hypothesis": "",
            "moat_reason": "",
            "estimated": True,
        }

    # Analyze uniqueness
    all_concepts = {}
    all_methods = set()
    for v in vectors:
        for c, score in v.concept.concepts.items():
            all_concepts[c] = all_concepts.get(c, 0) + score
        all_methods.update(v.method.methods.keys())

    top_concept = max(all_concepts.items(), key=lambda x: x[1])[0] if all_concepts else "technology"

    # Generate startup hypothesis
    startup_hypothesis = f"{top_concept}を活用した診断/治療ソリューション"

    # Identify moat
    moat_reasons = []
    avg_novelty = sum(v.temporal.novelty for v in vectors) / len(vectors)

    if avg_novelty > 0.7:
        moat_reasons.append("高い技術新規性")
    if len(all_methods) >= 3:
        moat_reasons.append("複合技術による参入障壁")
    if len(vectors) >= 5:
        moat_reasons.append("豊富な研究実績")

    moat_reason = "、".join(moat_reasons) if moat_reasons else "更なる差別化が必要"

    # IP potential
    ip_potential = "high" if avg_novelty > 0.6 else "medium"

    return {
        "startup_hypothesis": startup_hypothesis,
        "moat_reason": moat_reason,
        "core_technology": top_concept,
        "ip_potential": ip_potential,
        "technical_methods": list(all_methods)[:5],
        "estimated": True,
    }