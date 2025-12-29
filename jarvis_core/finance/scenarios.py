"""Scenario definitions for finance planning."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from .schema import MonthlyCashFlow, IncomeItem, ExpenseItem, DEFAULT_NOTE


@dataclass
class FinanceScenario:
    """Finance scenario for simulation and optimization."""

    scenario_id: str
    name: str
    description: str
    cashflows: List[MonthlyCashFlow]


def _month_sequence(start_month: str, months: int) -> List[str]:
    start = datetime.strptime(start_month, "%Y-%m")
    result = []
    year = start.year
    month = start.month
    for _ in range(months):
        result.append(f"{year:04d}-{month:02d}")
        month += 1
        if month > 12:
            year += 1
            month = 1
    return result


def _base_expenses() -> List[ExpenseItem]:
    return [
        ExpenseItem(type="rent", amount=70000, note=DEFAULT_NOTE),
        ExpenseItem(type="food", amount=40000, note=DEFAULT_NOTE),
        ExpenseItem(type="utilities", amount=15000, note=DEFAULT_NOTE),
        ExpenseItem(type="insurance", amount=10000, note=DEFAULT_NOTE),
        ExpenseItem(type="misc", amount=20000, note=DEFAULT_NOTE),
    ]


def _make_cashflows(start_month: str, months: int, income_template: List[IncomeItem]) -> List[MonthlyCashFlow]:
    cashflows = []
    for idx, month in enumerate(_month_sequence(start_month, months)):
        cashflows.append(
            MonthlyCashFlow(
                month=month,
                income=[item.with_note() for item in income_template],
                expenses=[item.with_note() for item in _base_expenses()],
                savings_start=300000 if idx == 0 else 0,
            ).normalized()
        )
    return cashflows


def default_scenarios(start_month: str = "2025-04", months: int = 36) -> Dict[str, FinanceScenario]:
    """Return default finance scenarios."""
    scenarios = {
        "S1": FinanceScenario(
            scenario_id="S1",
            name="DC1採択（RAなし）",
            description="DC1が採択されたケース。（推測です）",
            cashflows=_make_cashflows(
                start_month,
                months,
                [
                    IncomeItem(type="DC1", amount=200000, prob=0.9, note=DEFAULT_NOTE),
                ],
            ),
        ),
        "S2": FinanceScenario(
            scenario_id="S2",
            name="DC1不採択＋RA/TA",
            description="RA/TAで補填するケース。（推測です）",
            cashflows=_make_cashflows(
                start_month,
                months,
                [
                    IncomeItem(type="DC1", amount=200000, prob=0.2, note=DEFAULT_NOTE),
                    IncomeItem(type="RA", amount=50000, hours=10, note=DEFAULT_NOTE),
                    IncomeItem(type="TA", amount=30000, hours=5, note=DEFAULT_NOTE),
                ],
            ),
        ),
        "S3": FinanceScenario(
            scenario_id="S3",
            name="奨学金＋バイト併用",
            description="奨学金とバイト併用。（推測です）",
            cashflows=_make_cashflows(
                start_month,
                months,
                [
                    IncomeItem(type="Scholarship", amount=120000, prob=0.6, note=DEFAULT_NOTE),
                    IncomeItem(type="Part-time", amount=60000, hours=8, note=DEFAULT_NOTE),
                ],
            ),
        ),
        "S4": FinanceScenario(
            scenario_id="S4",
            name="最悪ケース（収入不安定）",
            description="奨学金なし・収入不安定。（推測です）",
            cashflows=_make_cashflows(
                start_month,
                months,
                [
                    IncomeItem(type="Temporary", amount=80000, prob=0.4, note=DEFAULT_NOTE),
                ],
            ),
        ),
    }
    return scenarios
