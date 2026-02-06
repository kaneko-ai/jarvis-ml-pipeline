"""Funding cliff helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FundingCliff:
    """Funding cliff status."""

    remaining_days: int = 0


def estimate_cliff(remaining_days: int) -> FundingCliff:
    """Estimate funding cliff.

    Args:
        remaining_days: Remaining days of funding.

    Returns:
        FundingCliff.
    """
    return FundingCliff(remaining_days=max(0, remaining_days))


__all__ = ["FundingCliff", "estimate_cliff"]
