"""Submission validation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Result of submission validation."""

    is_valid: bool = True
    issues: list[str] = field(default_factory=list)


class SubmissionValidator:
    """Minimal submission validator."""

    def validate(self, submission: dict) -> ValidationResult:
        """Validate a submission payload.

        Args:
            submission: Submission data.

        Returns:
            ValidationResult.
        """
        _ = submission
        return ValidationResult()


__all__ = ["SubmissionValidator", "ValidationResult"]
