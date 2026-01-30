"""Uncertainty label determination utilities."""

from __future__ import annotations


def determine_uncertainty_label(strength: float) -> str:
    """Determine uncertainty label from evidence strength.

    Args:
        strength: Evidence strength between 0.0 and 1.0.

    Returns:
        Japanese label describing confidence.
    """
    if strength >= 0.95:
        return "確定"
    if strength >= 0.80:
        return "高信頼"
    if strength >= 0.60:
        return "要注意"
    return "推測"