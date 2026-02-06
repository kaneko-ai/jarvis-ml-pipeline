"""Review generator pipeline shim."""

from __future__ import annotations


def generate_review() -> dict[str, str]:
    """Return an empty review payload."""
    return {"status": "noop"}
