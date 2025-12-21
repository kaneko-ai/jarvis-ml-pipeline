"""Teaching / Level Translation Engine.

Per RP36, this translates knowledge to different education levels.
"""
from __future__ import annotations

from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def translate_for_level(
    paper: "PaperVector",
    level: Literal["highschool", "undergrad", "grad"],
) -> str:
    """Translate paper content for different education levels.

    Args:
        paper: The PaperVector to translate.
        level: Target education level.

    Returns:
        Translated explanation.
    """
    # Get top concepts
    top_concepts = paper.concept.top_concepts(3)
    concept_names = [c[0] for c in top_concepts]

    # Get biological position
    bio = paper.biological_axis

    if level == "highschool":
        return _highschool_translation(concept_names, bio)
    elif level == "undergrad":
        return _undergrad_translation(concept_names, bio, paper)
    else:  # grad
        return _grad_translation(paper)


def _highschool_translation(concepts: list, bio) -> str:
    """High school level explanation."""
    lines = [
        "【高校生向け説明】",
        "",
        "この研究は、体の中で働く「免疫」について調べています。",
        "",
    ]

    if concepts:
        lines.append(f"キーワード: {', '.join(concepts)}")
        lines.append("")

    if bio.immune_activation > 0:
        lines.append("→ 免疫を「活性化」する方向の研究です。")
    else:
        lines.append("→ 免疫を「抑える」方向の研究です。")

    if bio.tumor_context > 0.3:
        lines.append("→ がん治療に関係しています。")

    lines.append("")
    lines.append("ポイント: 免疫は体を守る仕組みですが、がんに対しても重要です。")

    return "\n".join(lines)


def _undergrad_translation(concepts: list, bio, paper: "PaperVector") -> str:
    """Undergraduate level explanation."""
    lines = [
        "【学部生向け説明】",
        "",
        "## 研究背景",
        "本研究は免疫学と腫瘍学の境界領域に位置します。",
        "",
        "## 主要概念",
    ]

    for concept in concepts:
        lines.append(f"- {concept}")

    lines.append("")
    lines.append("## 研究の位置づけ")

    if bio.immune_activation > 0.3:
        lines.append("- 免疫活性化メカニズムに焦点")
    elif bio.immune_activation < -0.3:
        lines.append("- 免疫抑制・制御機構に焦点")

    if bio.tumor_context > 0.3:
        lines.append("- 腫瘍微小環境（TME）における現象を解析")

    lines.append("")
    lines.append("## 使用手法")
    if paper.method.methods:
        for method in list(paper.method.methods.keys())[:3]:
            lines.append(f"- {method}")

    return "\n".join(lines)


def _grad_translation(paper: "PaperVector") -> str:
    """Graduate level explanation."""
    lines = [
        "【大学院生向け説明】",
        "",
        "## 研究概要",
        f"Source: {paper.source_locator}",
        "",
        "## 概念空間での位置",
    ]

    top = paper.concept.top_concepts(5)
    for c, score in top:
        lines.append(f"- {c}: {score:.2f}")

    lines.append("")
    lines.append("## 生物学的軸")
    lines.append(f"- Immune axis: {paper.biological_axis.immune_activation:.2f}")
    lines.append(f"- Metabolism axis: {paper.biological_axis.metabolism_signal:.2f}")
    lines.append(f"- Tumor context: {paper.biological_axis.tumor_context:.2f}")

    lines.append("")
    lines.append("## 時間的評価")
    lines.append(f"- Novelty: {paper.temporal.novelty:.2f}")
    lines.append(f"- Paradigm shift: {paper.temporal.paradigm_shift:.2f}")

    lines.append("")
    lines.append("## 批判的評価ポイント")
    lines.append("- 実験デザインの妥当性")
    lines.append("- 統計解析の適切性")
    lines.append("- 先行研究との差別化")
    lines.append("- 再現性の担保")

    return "\n".join(lines)
