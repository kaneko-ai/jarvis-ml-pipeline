"""Failure prediction helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FailurePrediction:
    """Prediction result."""

    risk: float = 0.0


def predict_failure(signal: float) -> FailurePrediction:
    """Predict failure risk from a signal.

    Args:
        signal: Input signal.

    Returns:
        FailurePrediction with bounded risk.
    """
    risk = max(0.0, min(1.0, signal))
    return FailurePrediction(risk=risk)


__all__ = ["FailurePrediction", "predict_failure"]
