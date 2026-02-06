"""Evidence mapper shim."""

from __future__ import annotations

from typing import Any


def map_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    """Return evidence dict unchanged.

    Args:
        evidence: Evidence dictionary.

    Returns:
        Same dictionary for compatibility.
    """
    return dict(evidence)
