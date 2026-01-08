"""Scenario templates for finance planning."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from jarvis_core.finance.schema import (
    ASSUMPTION_NOTE,
    ExpenseItem,
    IncomeItem,
    MonthlyCashflow,
    ensure_notes,
)
from jarvis_core.time.calendar_builder import build_months


@dataclass
class ScenarioResult:
    scenario_id: str
    name: str
    cashflows: list[MonthlyCashflow]


def _base_expenses() -> list[ExpenseItem]:
    return [
        ExpenseItem(type="rent", amount=70000, note=ASSUMPTION_NOTE),
        ExpenseItem(type="food", amount=40000, note=ASSUMPTION_NOTE),
        ExpenseItem(type="utilities", amount=15000, note=ASSUMPTION_NOTE),
        ExpenseItem(type="insurance", amount=10000, note=ASSUMPTION_NOTE),
        ExpenseItem(type="misc", amount=20000, note=ASSUMPTION_NOTE),
    ]


def _scenario_income(scenario_id: str) -> list[IncomeItem]:
    if scenario_id == "S1":
        return [
            IncomeItem(type="DC1", amount=200000, prob=0.75, note=ASSUMPTION_NOTE),
        ]
    if scenario_id == "S2":
        return [
            IncomeItem(type="DC1", amount=200000, prob=0.25, note=ASSUMPTION_NOTE),
            IncomeItem(type="RA", amount=50000, hours=10, note=ASSUMPTION_NOTE),
            IncomeItem(type="TA", amount=30000, hours=5, note=ASSUMPTION_NOTE),
        ]
    if scenario_id == "S3":
        return [
            IncomeItem(type="scholarship", amount=120000, prob=0.6, note=ASSUMPTION_NOTE),
            IncomeItem(type="part_time", amount=60000, hours=12, note=ASSUMPTION_NOTE),
        ]
    return [
        IncomeItem(type="unstable", amount=80000, prob=0.4, note=ASSUMPTION_NOTE),
    ]


def build_scenarios(
    months: int = 36,
    start_month: str | None = None,
    savings_start: float = 300000,
) -> dict[str, ScenarioResult]:
    start = start_month or date.today().strftime("%Y-%m")
    month_labels = build_months(start, months)
    scenarios: dict[str, ScenarioResult] = {}
    for scenario_id, name in [
        ("S1", "DC1採択（RAなし）"),
        ("S2", "DC1不採択＋RA/TA"),
        ("S3", "奨学金＋バイト併用"),
        ("S4", "最悪ケース（奨学金なし、収入不安定）"),
    ]:
        cashflows: list[MonthlyCashflow] = []
        current_savings = savings_start
        for month in month_labels:
            income = _scenario_income(scenario_id)
            expenses = _base_expenses()
            cashflow = MonthlyCashflow(
                month=month,
                income=income,
                expenses=expenses,
                savings_start=current_savings,
            )
            current_savings = cashflow.expected_balance_end()
            cashflows.append(cashflow)
        ensure_notes(cashflows)
        scenarios[scenario_id] = ScenarioResult(
            scenario_id=scenario_id,
            name=name,
            cashflows=cashflows,
        )
    return scenarios
