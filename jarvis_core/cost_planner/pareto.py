"""Pareto Planner.

Per V4.2 Sprint 3, this selects optimal cost-quality tradeoffs.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ParetoChoice:
    """A choice in the pareto frontier."""

    choice_id: str
    name: str
    estimated_cost: float
    estimated_quality: float
    settings: dict[str, any] = field(default_factory=dict)

    def is_dominated_by(self, other: ParetoChoice) -> bool:
        """Check if this choice is dominated by another."""
        # Dominated if other is better or equal in both dimensions
        return (
            other.estimated_cost <= self.estimated_cost and
            other.estimated_quality >= self.estimated_quality and
            (other.estimated_cost < self.estimated_cost or
             other.estimated_quality > self.estimated_quality)
        )


class ParetoPlanner:
    """Plans execution to maximize quality within budget."""

    def __init__(
        self,
        budget_limit: float = 1.0,
        min_quality: float = 0.6,
    ):
        self.budget_limit = budget_limit
        self.min_quality = min_quality

    def generate_choices(
        self,
        available_methods: list[str] = None,
    ) -> list[ParetoChoice]:
        """Generate possible execution choices.

        Args:
            available_methods: Available retrieval methods.

        Returns:
            List of choices.
        """
        from .quality_gain import estimate_quality

        available_methods = available_methods or ["bm25_only", "hybrid", "hybrid_rerank"]

        choices = []

        # Quick mode choices
        choices.append(ParetoChoice(
            choice_id="quick_bm25",
            name="Quick BM25",
            estimated_cost=0.1,
            estimated_quality=estimate_quality("bm25_only", 50, 3, False, "quick"),
            settings={"method": "bm25_only", "depth": "quick", "rerank": False},
        ))

        choices.append(ParetoChoice(
            choice_id="quick_hybrid",
            name="Quick Hybrid",
            estimated_cost=0.3,
            estimated_quality=estimate_quality("hybrid", 100, 5, False, "quick"),
            settings={"method": "hybrid", "depth": "quick", "rerank": False},
        ))

        # Deep mode choices
        choices.append(ParetoChoice(
            choice_id="deep_hybrid",
            name="Deep Hybrid",
            estimated_cost=0.6,
            estimated_quality=estimate_quality("hybrid", 100, 8, False, "deep"),
            settings={"method": "hybrid", "depth": "deep", "rerank": False},
        ))

        choices.append(ParetoChoice(
            choice_id="deep_hybrid_rerank",
            name="Deep Hybrid + Rerank",
            estimated_cost=1.0,
            estimated_quality=estimate_quality("hybrid", 200, 10, True, "deep"),
            settings={"method": "hybrid", "depth": "deep", "rerank": True},
        ))

        return choices

    def find_pareto_frontier(
        self,
        choices: list[ParetoChoice],
    ) -> list[ParetoChoice]:
        """Find non-dominated choices (Pareto frontier)."""
        frontier = []

        for choice in choices:
            dominated = False
            for other in choices:
                if choice != other and choice.is_dominated_by(other):
                    dominated = True
                    break

            if not dominated:
                frontier.append(choice)

        # Sort by cost
        frontier.sort(key=lambda c: c.estimated_cost)
        return frontier

    def select_optimal(
        self,
        budget_remaining: float = 1.0,
    ) -> ParetoChoice:
        """Select optimal choice within budget.

        Args:
            budget_remaining: Remaining budget ratio.

        Returns:
            Optimal ParetoChoice.
        """
        actual_budget = min(budget_remaining, self.budget_limit)

        choices = self.generate_choices()
        frontier = self.find_pareto_frontier(choices)

        # Filter by budget and minimum quality
        feasible = [
            c for c in frontier
            if c.estimated_cost <= actual_budget and
               c.estimated_quality >= self.min_quality
        ]

        if not feasible:
            # Fall back to cheapest option
            return min(choices, key=lambda c: c.estimated_cost)

        # Select highest quality within budget
        return max(feasible, key=lambda c: c.estimated_quality)

    def plan(
        self,
        budget_remaining: float = 1.0,
    ) -> dict[str, any]:
        """Create execution plan.

        Args:
            budget_remaining: Remaining budget ratio.

        Returns:
            Execution settings dict.
        """
        choice = self.select_optimal(budget_remaining)

        return {
            "choice": choice.name,
            "choice_id": choice.choice_id,
            "estimated_cost": choice.estimated_cost,
            "estimated_quality": choice.estimated_quality,
            **choice.settings,
        }
