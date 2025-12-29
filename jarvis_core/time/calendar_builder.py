"""Calendar builder for weekly/monthly summaries."""
from __future__ import annotations

from datetime import datetime
from typing import List, Dict

from .schema import WeekAllocation, DEFAULT_NOTE


def build_weekly_calendar(start_month: str, months: int, allocation: WeekAllocation) -> List[Dict[str, object]]:
    """Build a weekly calendar summary for each month.

    Uses a simplified 4-week assumption per month (推測です).
    """
    start = datetime.strptime(start_month, "%Y-%m")
    current_year = start.year
    current_month = start.month
    calendar: List[Dict[str, object]] = []
    for _ in range(months):
        month_label = f"{current_year:04d}-{current_month:02d}"
        for week_index in range(1, 5):
            calendar.append(
                {
                    "month": month_label,
                    "week": week_index,
                    "hours": {
                        "fixed": allocation.fixed_total(),
                        "variable_target": allocation.variable_target_total(),
                        "available": allocation.available_hours(),
                    },
                    "note": DEFAULT_NOTE,
                }
            )
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1
    return calendar
