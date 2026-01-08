"""Failure Mode Predictor.

Per RP47, this predicts potential failure modes for experiments.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


def predict_failure_modes(
    hypothesis: str,
    vectors: list[PaperVector],
) -> list[str]:
    """Predict potential failure modes for a hypothesis.

    Args:
        hypothesis: The hypothesis to test.
        vectors: PaperVectors for context.

    Returns:
        List of potential failure mode descriptions.
    """
    if not hypothesis:
        return []

    failure_modes = []

    # Find related papers
    hypothesis_lower = hypothesis.lower()
    related = []
    for v in vectors:
        for c in v.concept.concepts:
            if c.lower() in hypothesis_lower or hypothesis_lower in c.lower():
                related.append(v)
                break

    # Generic failure modes
    failure_modes.append("サンプルサイズ不足による統計的検出力の低下")

    # Concept-specific failures
    if "immune" in hypothesis_lower or "免疫" in hypothesis:
        failure_modes.append("免疫細胞のロット間変動による再現性問題")
        failure_modes.append("マウス系統による応答差")

    if "tumor" in hypothesis_lower or "腫瘍" in hypothesis:
        failure_modes.append("腫瘍不均一性による結果のばらつき")
        failure_modes.append("腫瘍生着率の低下")

    if "signal" in hypothesis_lower or "pathway" in hypothesis_lower:
        failure_modes.append("オフターゲット効果の混入")
        failure_modes.append("フィードバック補償による表現型マスキング")

    # Method-specific failures based on related papers
    all_methods = set()
    for v in related:
        all_methods.update(v.method.methods.keys())

    if "scRNA-seq" in all_methods:
        failure_modes.append("シングルセル解析時のドロップアウト")
        failure_modes.append("バッチエフェクトによるデータ汚染")

    if "CRISPR" in all_methods:
        failure_modes.append("CRISPR効率のばらつき")
        failure_modes.append("オフターゲット編集")

    if "Western blot" in all_methods or "qPCR" in all_methods:
        failure_modes.append("抗体特異性の問題")

    # Impact-based failures
    low_impact = [v for v in related if v.impact.future_potential < 0.3]
    if low_impact:
        failure_modes.append("類似研究で低インパクト結果が報告されている")

    return failure_modes[:8]  # Limit output
