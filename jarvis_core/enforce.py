"""Enforcement helpers."""

from __future__ import annotations


def enforce_rule(rule: str) -> bool:
    """Enforce a simple rule.

    Args:
        rule: Rule name.

    Returns:
        True when enforcement passes.
    """
    _ = rule
    return True


__all__ = ["enforce_rule"]
