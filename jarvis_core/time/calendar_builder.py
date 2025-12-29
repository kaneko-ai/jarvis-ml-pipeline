"""Calendar builder utilities for weekly/monthly planning."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List


def build_months(start_month: str, months: int) -> List[str]:
    """Build a list of YYYY-MM labels starting from start_month."""
    start = datetime.strptime(start_month, "%Y-%m")
    results: List[str] = []
    year = start.year
    month = start.month
    for _ in range(months):
        results.append(f"{year:04d}-{month:02d}")
        month += 1
        if month > 12:
            month = 1
            year += 1
    return results


def build_weeks(start_date: str, weeks: int) -> List[str]:
    """Build week labels starting from a date string YYYY-MM-DD."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    results: List[str] = []
    for offset in range(weeks):
        week_start = start + timedelta(days=offset * 7)
        results.append(week_start.strftime("%Y-%m-%d"))
    return results
