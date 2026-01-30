"""P9 plan integration for time/finance constraints."""

from __future__ import annotations

from dataclasses import dataclass

from jarvis_core.time.schema import TimeSchema


@dataclass
class PlanTimeAssessment:
    required_research_hours: float
    available_research_hours: float
    delay_risk: bool
    delay_months: int
    delay_cost: float
    notes: list[str]


def build_mvp_plan(option) -> dict:
    """Build MVP plan for an option.

    Args:
        option: Option object with goal, theme, time_horizon_months

    Returns:
        Dictionary with MVP plan phases
    """
    return {
        "phase1": "initial_setup",
        "phase2": "core_development",
        "phase3": "validation",
        "timeline_months": (
            option.time_horizon_months.value
            if hasattr(option.time_horizon_months, "value")
            else option.time_horizon_months
        ),
        "goal": option.goal,
    }


def build_kill_criteria(option) -> list[str]:
    """Build kill criteria for an option.

    Args:
        option: Option object

    Returns:
        List of kill criteria strings
    """
    return [
        f"No progress after {int(option.time_horizon_months.value / 4 if hasattr(option.time_horizon_months, 'value') else option.time_horizon_months / 4)} months",
        "Critical resource unavailable",
        "Competitor publishes first",
        "Fundamental assumption invalidated",
    ]


def assess_plan_time(plan: dict[str, float], time_schema: TimeSchema) -> PlanTimeAssessment:
    """Assess plan hours against available research time.

    Expects plan to include `research_hours_week` and optional `additional_hours_week`.
    """
    required = float(plan.get("research_hours_week", 0.0)) + float(
        plan.get("additional_hours_week", 0.0)
    )
    research_block = time_schema.variable.get("research")
    available = research_block.target if research_block else 0.0
    delay_risk = required > available
    notes: list[str] = []
    if delay_risk:
        notes.append("研究計画の必要時間が可処分時間を超過しています（推測です）")
    delay_months = int(plan.get("delay_months", 0)) if delay_risk else 0
    housing_cost = float(plan.get("housing_cost_monthly", 70000))
    delay_cost = delay_months * housing_cost if delay_risk else 0.0
    if delay_cost > 0:
        notes.append("研究遅延による延長コストを加味しています（推測です）")
    return PlanTimeAssessment(
        required_research_hours=required,
        available_research_hours=available,
        delay_risk=delay_risk,
        delay_months=delay_months,
        delay_cost=delay_cost,
        notes=notes,
    )
