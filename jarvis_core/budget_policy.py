"""Budget policy helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BudgetDecision:
    """Decision for budget usage."""

    allowed: bool = True
    remaining: float = 0.0


class BudgetPolicy:
    """Simple budget policy."""

    def decide(self, remaining: float) -> BudgetDecision:
        """Decide whether budget allows work.

        Args:
            remaining: Remaining budget.

        Returns:
            BudgetDecision.
        """
        return BudgetDecision(allowed=remaining > 0, remaining=remaining)


__all__ = ["BudgetDecision", "BudgetPolicy"]
