"""Decision planner connecting research plan to finance/time constraints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from jarvis_core.time.schema import WeekAllocation, DEFAULT_NOTE


@dataclass
class PlanAlignment:
    """Alignment result between plan hours and available time."""

    planned_research_hours: int
    available_research_target: int
    shortfall: int
    aligned: bool
    note: str = DEFAULT_NOTE


def evaluate_plan_alignment(
    planned_research_hours: int,
    allocation: WeekAllocation,
) -> PlanAlignment:
    """Check if planned research hours fit within time allocation."""
    available_target = allocation.variable.research.target
    shortfall = max(0, planned_research_hours - available_target)
    aligned = shortfall == 0
    return PlanAlignment(
        planned_research_hours=planned_research_hours,
        available_research_target=available_target,
        shortfall=shortfall,
        aligned=aligned,
    )


def estimate_delay_cost(monthly_rent: int, delay_months: int) -> Dict[str, object]:
    """Estimate cost impact of research delay."""
    return {
        "delay_months": delay_months,
        "cost": monthly_rent * delay_months,
        "note": DEFAULT_NOTE,
    }
