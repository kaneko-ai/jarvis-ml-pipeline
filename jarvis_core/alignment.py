"""Alignment utilities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AlignmentResult:
    """Result of an alignment operation."""

    score: float = 0.0
    summary: str = ""


def align_text(source: str, target: str) -> AlignmentResult:
    """Align two text snippets and return a simple score.

    Args:
        source: Source text.
        target: Target text.

    Returns:
        AlignmentResult with heuristic score.
    """
    if not source or not target:
        return AlignmentResult(score=0.0, summary="")
    score = float(min(len(source), len(target))) / float(max(len(source), len(target)))
    return AlignmentResult(score=score, summary="heuristic")


__all__ = ["AlignmentResult", "align_text"]
