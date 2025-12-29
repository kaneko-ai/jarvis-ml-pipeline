"""Finance schema definitions for monthly cashflow modeling."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

DEFAULT_NOTE = "（推測です）"


@dataclass
class IncomeItem:
    """Monthly income item."""

    type: str
    amount: int
    note: str = DEFAULT_NOTE
    prob: Optional[float] = None
    hours: Optional[int] = None

    def expected_amount(self) -> float:
        """Return expected value based on probability."""
        if self.prob is None:
            return float(self.amount)
        return float(self.amount) * self.prob

    def downside_amount(self) -> float:
        """Return downside value assuming uncertain income can be lost."""
        if self.prob is None:
            return float(self.amount)
        if self.prob >= 1:
            return float(self.amount)
        return 0.0

    def with_note(self) -> "IncomeItem":
        """Ensure note is populated."""
        if not self.note:
            self.note = DEFAULT_NOTE
        return self


@dataclass
class ExpenseItem:
    """Monthly expense item."""

    type: str
    amount: int
    note: str = DEFAULT_NOTE

    def with_note(self) -> "ExpenseItem":
        """Ensure note is populated."""
        if not self.note:
            self.note = DEFAULT_NOTE
        return self


@dataclass
class MonthlyCashFlow:
    """Monthly cash flow snapshot."""

    month: str
    income: List[IncomeItem] = field(default_factory=list)
    expenses: List[ExpenseItem] = field(default_factory=list)
    savings_start: int = 0

    def expected_income(self) -> float:
        return sum(item.expected_amount() for item in self.income)

    def downside_income(self) -> float:
        return sum(item.downside_amount() for item in self.income)

    def total_expenses(self) -> float:
        return sum(item.amount for item in self.expenses)

    def normalized(self) -> "MonthlyCashFlow":
        """Ensure all notes are populated."""
        self.income = [item.with_note() for item in self.income]
        self.expenses = [item.with_note() for item in self.expenses]
        return self
