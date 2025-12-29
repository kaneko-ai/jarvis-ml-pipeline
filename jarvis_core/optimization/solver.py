"""Heuristic solver for finance/time optimization."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from jarvis_core.finance.scenarios import FinanceScenario
from jarvis_core.optimization.constraints import evaluate_constraints
from jarvis_core.time.schema import WeekAllocation


@dataclass
class OptimizationResult:
    scenario: str
    status: str
    expected_balance_end: int
    bankruptcy_risk: float
    research_hours_avg: float
    overwork_risk: float
    recommendation: str
    details: Dict[str, object]


def _simulate_balance(cashflows, use_expected: bool) -> int:
    balance = cashflows[0].savings_start if cashflows else 0
    for flow in cashflows:
        income = flow.expected_income() if use_expected else flow.downside_income()
        balance += income - flow.total_expenses()
    return int(balance)


def _bankruptcy_risk(cashflows) -> float:
    balance = cashflows[0].savings_start if cashflows else 0
    risk_months = 0
    for flow in cashflows:
        balance += flow.downside_income() - flow.total_expenses()
        if balance < 0:
            risk_months += 1
    if not cashflows:
        return 0.0
    return round(risk_months / len(cashflows), 2)


def _min_balance(cashflows, use_expected: bool) -> int:
    balance = cashflows[0].savings_start if cashflows else 0
    minimum = balance
    for flow in cashflows:
        income = flow.expected_income() if use_expected else flow.downside_income()
        balance += income - flow.total_expenses()
        minimum = min(minimum, balance)
    return int(minimum)


def _deficit_probability(cashflows) -> float:
    if not cashflows:
        return 0.0
    balance = cashflows[0].savings_start
    deficit_months = 0
    for flow in cashflows:
        balance += flow.downside_income() - flow.total_expenses()
        if balance < 0:
            deficit_months += 1
    return round(deficit_months / len(cashflows), 2)


def optimize_scenarios(
    scenarios: Dict[str, FinanceScenario],
    allocation: WeekAllocation,
    planned_research_hours: int,
) -> List[OptimizationResult]:
    """Return optimization results per scenario."""
    results: List[OptimizationResult] = []
    for scenario_id, scenario in scenarios.items():
        constraints = evaluate_constraints(
            scenario.cashflows,
            allocation,
            planned_research_hours,
        )
        expected_end = _simulate_balance(scenario.cashflows, use_expected=True)
        bankruptcy_risk = _bankruptcy_risk(scenario.cashflows)
        deficit_probability = _deficit_probability(scenario.cashflows)
        min_balance = _min_balance(scenario.cashflows, use_expected=True)
        overwork_risk = 1.0 if constraints["overwork"] else 0.18
        research_avg = allocation.variable.research.target
        attainment_rate = round(
            min(1.0, research_avg / planned_research_hours) if planned_research_hours else 1.0,
            2,
        )

        if constraints["hard_violations"]:
            status = "infeasible"
        elif constraints["soft_penalties"] or bankruptcy_risk >= 0.2:
            status = "risky"
        else:
            status = "feasible"

        recommendation_parts = []
        if constraints["overwork"]:
            recommendation_parts.append("RA/TA時間を週8hに抑えると過労リスクが下がる（推測です）")
        if constraints["research_shortfall"]:
            recommendation_parts.append("研究時間のtargetを増やすと計画遅延が緩和される（推測です）")
        if not recommendation_parts:
            recommendation_parts.append("現状の配分を維持しつつ定期的に見直す（推測です）")

        results.append(
            OptimizationResult(
                scenario=scenario_id,
                status=status,
                expected_balance_end=expected_end,
                bankruptcy_risk=bankruptcy_risk,
                research_hours_avg=research_avg,
                overwork_risk=overwork_risk,
                recommendation=" / ".join(recommendation_parts),
                details={
                    "constraints": constraints,
                    "expected_balance_end": expected_end,
                    "minimum_balance": min_balance,
                    "deficit_probability": deficit_probability,
                    "research_attainment_rate": attainment_rate,
                    "note": "（推測です）",
                },
            )
        )
    return results
