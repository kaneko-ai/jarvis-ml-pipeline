"""Simple optimization solver for P10."""

from __future__ import annotations

from dataclasses import dataclass

from jarvis_core.finance.scenarios import ScenarioResult
from jarvis_core.finance.schema import MonthlyCashflow
from jarvis_core.optimization.constraints import ConstraintReport, evaluate_constraints
from jarvis_core.time.schema import TimeSchema


@dataclass
class ScenarioEvaluation:
    scenario: str
    status: str
    expected_balance_end: float
    bankruptcy_risk: float
    research_hours_avg: float
    overwork_risk: float
    minimum_balance: float
    constraint_report: ConstraintReport
    recommendation: str


def _bankruptcy_risk(cashflows: list[MonthlyCashflow]) -> float:
    if not cashflows:
        return 0.0
    risky_months = sum(1 for m in cashflows if m.downside_balance_end() < 0)
    return risky_months / len(cashflows)


def _minimum_balance(cashflows: list[MonthlyCashflow]) -> float:
    if not cashflows:
        return 0.0
    return min(m.expected_balance_end() for m in cashflows)


def _overwork_risk(time_schema: TimeSchema) -> float:
    working = time_schema.working_hours()
    return max((working - 60) / 40, 0.0)


def _recommendation(time_schema: TimeSchema) -> str:
    ra_ta = time_schema.variable.get("ra_ta")
    if ra_ta and ra_ta.target > 8:
        return "RA/TA時間を週8hに抑えると破綻確率が下がる可能性があります（推測です）"
    return "生活リズムを維持しながら研究時間を確保できる配分です（推測です）"


def evaluate_scenario(
    scenario: ScenarioResult,
    time_schema: TimeSchema,
    research_required: float | None = None,
    delay_cost: float = 0.0,
) -> ScenarioEvaluation:
    cashflows = scenario.cashflows
    final_balance = cashflows[-1].expected_balance_end() if cashflows else 0.0
    if delay_cost:
        final_balance -= delay_cost
    bankruptcy_risk = _bankruptcy_risk(cashflows)
    min_balance = _minimum_balance(cashflows) - delay_cost
    overwork_risk = _overwork_risk(time_schema)
    research_hours = time_schema.variable.get("research")
    research_avg = research_hours.target if research_hours else 0.0
    constraint_report = evaluate_constraints(
        cashflows=cashflows,
        time_schema=time_schema,
        initial_savings=cashflows[0].savings_start if cashflows else 0.0,
        research_required=research_required,
    )
    status = constraint_report.status()
    return ScenarioEvaluation(
        scenario=scenario.scenario_id,
        status=status,
        expected_balance_end=final_balance,
        bankruptcy_risk=bankruptcy_risk,
        research_hours_avg=research_avg,
        overwork_risk=overwork_risk,
        minimum_balance=min_balance,
        constraint_report=constraint_report,
        recommendation=_recommendation(time_schema),
    )


def optimize(
    scenarios: dict[str, ScenarioResult],
    time_schema: TimeSchema,
    research_required: float | None = None,
    delay_cost: float = 0.0,
) -> dict[str, ScenarioEvaluation]:
    evaluations = {
        scenario_id: evaluate_scenario(result, time_schema, research_required, delay_cost)
        for scenario_id, result in scenarios.items()
    }
    return evaluations


def choose_best(evaluations: dict[str, ScenarioEvaluation]) -> ScenarioEvaluation:
    """Pick a scenario with lowest risk and highest balance."""
    candidates = sorted(
        evaluations.values(),
        key=lambda ev: (
            0 if ev.status == "feasible" else 1 if ev.status == "risky" else 2,
            ev.bankruptcy_risk,
            -ev.expected_balance_end,
        ),
    )
    return candidates[0]
