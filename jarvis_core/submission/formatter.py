"""Submission formatter shim."""

from __future__ import annotations


def format_submission(payload: dict[str, str]) -> dict[str, str]:
    """Return payload unchanged."""
    return dict(payload)
