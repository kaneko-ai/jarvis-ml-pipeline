"""Presentation Rehearsal Mode.

Per RP35, this generates anticipated questions for presentations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def generate_rehearsal(vectors: list[PaperVector]) -> dict:
    """Generate presentation rehearsal with anticipated questions.

    Args:
        vectors: PaperVectors representing the research.

    Returns:
        Rehearsal dict with questions and guidance.
    """
    if not vectors:
        return {
            "questions": [],
            "tough_questions": [],
            "model_answers": [],
        }

    # Aggregate attributes
    all_concepts = set()
    all_methods = set()
    years = []

    for v in vectors:
        all_concepts.update(v.concept.concepts.keys())
        all_methods.update(v.method.methods.keys())
        if v.metadata.year:
            years.append(v.metadata.year)

    # Basic questions
    questions = [
        "この研究の新規性は何ですか？",
        "先行研究との違いは？",
        "臨床応用の可能性は？",
    ]

    # Concept-based questions
    for concept in list(all_concepts)[:3]:
        questions.append(f"{concept}の役割を説明してください")

    # Method-based questions
    for method in list(all_methods)[:2]:
        questions.append(f"なぜ{method}を選択しましたか？")

    # Tough questions (critical)
    tough_questions = [
        "この結果の再現性は担保されていますか？",
        "対照群の設定は適切ですか？",
        "サンプルサイズの根拠は？",
        "バイアスの可能性はありますか？",
    ]

    # Check for specific weaknesses
    avg_novelty = sum(v.temporal.novelty for v in vectors) / len(vectors)
    if avg_novelty < 0.5:
        tough_questions.append("新規性が低いのでは？既報との差別化は？")

    # Model answers (guidance)
    model_answers = [
        {
            "for": "この研究の新規性は何ですか？",
            "guidance": "1) 先行研究の限界を述べる 2) 本研究の独自アプローチ 3) 得られた新知見",
        },
        {
            "for": "臨床応用の可能性は？",
            "guidance": "1) 現在の臨床課題 2) 本研究の示唆 3) 今後の検証ステップ",
        },
    ]

    return {
        "questions": questions,
        "tough_questions": tough_questions,
        "model_answers": model_answers,
        "total_papers_reviewed": len(vectors),
        "concepts_covered": list(all_concepts),
    }
