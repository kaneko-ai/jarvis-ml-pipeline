"""Quality gate helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QualityGateResult:
    """Result of quality gate evaluation."""

    passed: bool = True
    reason: str = ""


def evaluate_quality(score: float) -> QualityGateResult:
    """Evaluate quality score.

    Args:
        score: Quality score.

    Returns:
        QualityGateResult.
    """
    passed = score >= 0.5
    return QualityGateResult(passed=passed, reason="")


__all__ = ["QualityGateResult", "evaluate_quality"]
