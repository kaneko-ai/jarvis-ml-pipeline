"""Journal checker helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class JournalCheckResult:
    """Result of a journal check."""

    is_compatible: bool = True
    issues: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class JournalChecker:
    """Minimal journal checker."""

    def check(self, journal: str) -> JournalCheckResult:
        """Check journal compatibility.

        Args:
            journal: Journal identifier.

        Returns:
            JournalCheckResult.
        """
        _ = journal
        return JournalCheckResult()


__all__ = ["JournalCheckResult", "JournalChecker"]
