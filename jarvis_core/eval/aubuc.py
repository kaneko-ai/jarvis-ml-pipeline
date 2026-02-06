"""AUBUC-style evaluation helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AubucScore:
    """Lightweight score container for AUBUC metrics."""

    score: float = 0.0


class AubucEvaluator:
    """Minimal evaluator for AUBUC metrics."""

    def evaluate(self) -> AubucScore:
        """Return a default AUBUC score."""
        return AubucScore()
