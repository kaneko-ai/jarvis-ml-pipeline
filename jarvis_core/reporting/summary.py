"""Reporting summary helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SummaryItem:
    """Single summary item."""

    title: str
    data: dict[str, Any]


def summarize_report(report: dict[str, Any]) -> list[SummaryItem]:
    """Summarize a report.

    Args:
        report: Report dictionary.

    Returns:
        List of SummaryItem entries.
    """
    if not report:
        return []
    return [SummaryItem(title="summary", data=dict(report))]


__all__ = ["SummaryItem", "summarize_report"]
