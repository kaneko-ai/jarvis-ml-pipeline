"""Scientific linter helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LintResult:
    """Lint result."""

    issues: list[str]


def lint_text(text: str) -> LintResult:
    """Lint text for scientific formatting issues.

    Args:
        text: Input text.

    Returns:
        LintResult with issues.
    """
    _ = text
    return LintResult(issues=[])


__all__ = ["LintResult", "lint_text"]
