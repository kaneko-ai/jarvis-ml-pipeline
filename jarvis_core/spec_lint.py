"""Spec lint helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SpecLintResult:
    """Result of spec linting."""

    issues: list[str]


def lint_spec(text: str) -> SpecLintResult:
    """Lint a spec text.

    Args:
        text: Spec text.

    Returns:
        SpecLintResult.
    """
    _ = text
    return SpecLintResult(issues=[])


__all__ = ["SpecLintResult", "lint_spec"]
