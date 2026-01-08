"""Finance schemas for P10 resource optimization."""

from __future__ import annotations

from dataclasses import dataclass, field

ASSUMPTION_NOTE = "（推測です）"


@dataclass
class IncomeItem:
    """Monthly income entry."""

    type: str
    amount: float
    note: str = ASSUMPTION_NOTE
    prob: float | None = None
    hours: float | None = None

    def expected_amount(self) -> float:
        if self.prob is None:
            return self.amount
        return self.amount * self.prob

    def downside_amount(self) -> float:
        if self.prob is None:
            return self.amount
        return 0.0


@dataclass
class ExpenseItem:
    """Monthly expense entry."""

    type: str
    amount: float
    note: str = ASSUMPTION_NOTE


@dataclass
class MonthlyCashflow:
    """Monthly cashflow projection."""

    month: str
    income: list[IncomeItem] = field(default_factory=list)
    expenses: list[ExpenseItem] = field(default_factory=list)
    savings_start: float = 0.0

    def expected_income(self) -> float:
        return sum(item.expected_amount() for item in self.income)

    def downside_income(self) -> float:
        return sum(item.downside_amount() for item in self.income)

    def total_expenses(self) -> float:
        return sum(item.amount for item in self.expenses)

    def expected_balance_end(self) -> float:
        return self.savings_start + self.expected_income() - self.total_expenses()

    def downside_balance_end(self) -> float:
        return self.savings_start + self.downside_income() - self.total_expenses()


def ensure_notes(cashflows: list[MonthlyCashflow]) -> None:
    """Ensure all entries have notes (assumptions)."""
    for month in cashflows:
        for income in month.income:
            if not income.note:
                income.note = ASSUMPTION_NOTE
        for expense in month.expenses:
            if not expense.note:
                expense.note = ASSUMPTION_NOTE
