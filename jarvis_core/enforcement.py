"""Enforcement policy helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EnforcementResult:
    """Result of an enforcement check."""

    allowed: bool = True
    reason: str = ""


def enforce(action: str) -> EnforcementResult:
    """Enforce an action.

    Args:
        action: Action name.

    Returns:
        EnforcementResult.
    """
    _ = action
    return EnforcementResult(allowed=True, reason="")


__all__ = ["EnforcementResult", "enforce"]
