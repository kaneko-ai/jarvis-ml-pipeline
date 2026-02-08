"""Compatibility evaluator module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Evaluator:
    """Minimal evaluator used by legacy deep-import tests."""

    name: str = "default"

    def evaluate(self, rows: list[dict[str, Any]] | None = None) -> dict[str, float]:
        rows = rows or []
        if not rows:
            return {"count": 0, "score": 0.0}
        return {"count": float(len(rows)), "score": 1.0}
