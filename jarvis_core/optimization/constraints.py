"""Constraint evaluation for finance/time optimization."""
from __future__ import annotations

from typing import Dict, List

from jarvis_core.finance.schema import MonthlyCashFlow
from jarvis_core.time.schema import WeekAllocation


def evaluate_constraints(
    cashflows: List[MonthlyCashFlow],
    allocation: WeekAllocation,
    planned_research_hours: int,
) -> Dict[str, object]:
    """Evaluate hard/soft constraints and return flags."""
    balance = cashflows[0].savings_start if cashflows else 0
    deficit_months = []
    for flow in cashflows:
        balance += flow.downside_income() - flow.total_expenses()
        if balance < 0:
            deficit_months.append(flow.month)

    sleep_shortfall = allocation.sleep_hours_per_day() < 6
    overwork = allocation.work_hours_max() > 80
    research_shortfall = allocation.variable.research.target < planned_research_hours
    focus_overflow = allocation.work_hours_target() > allocation.available_hours()

    hard_violations = []
    if deficit_months:
        hard_violations.append("月末残高が赤字")
    if overwork:
        hard_violations.append("週労働時間が80h超過")
    if sleep_shortfall:
        hard_violations.append("睡眠が6h/日未満")

    soft_penalties = []
    if research_shortfall:
        soft_penalties.append("研究時間がtarget未満")
    if focus_overflow:
        soft_penalties.append("研究+RA/TA+バイトが可処分時間超過")
    if allocation.variable.rest.target < allocation.variable.rest.min:
        soft_penalties.append("余暇がmin未満")
    if cashflows and cashflows[0].savings_start < 0:
        soft_penalties.append("貯蓄が初期値を下回る")

    return {
        "deficit_months": deficit_months,
        "hard_violations": hard_violations,
        "soft_penalties": soft_penalties,
        "research_shortfall": research_shortfall,
        "overwork": overwork,
        "sleep_shortfall": sleep_shortfall,
    }
