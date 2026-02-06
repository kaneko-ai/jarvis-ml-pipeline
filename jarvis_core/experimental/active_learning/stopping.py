"""Stopping criteria for active learning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class StoppingState:
    """State snapshot passed to stopping criteria.

    Args:
        total_instances: Total number of instances in the pool.
        labeled_instances: Labeled instance count.
        relevant_found: Count of relevant instances found.
        iterations: Completed iterations.
        estimated_recall: Estimated recall.
        predictions: Optional prediction scores.
    """

    total_instances: int
    labeled_instances: int
    relevant_found: int
    iterations: int
    estimated_recall: float
    predictions: list[float]


class StoppingCriterion:
    """Base class for stopping criteria."""

    def should_stop(self, state: StoppingState) -> bool:
        """Return True if the process should stop."""
        raise NotImplementedError


class RecallStoppingCriterion(StoppingCriterion):
    """Stop when estimated recall reaches the target."""

    def __init__(self, target_recall: float, min_iterations: int = 1) -> None:
        self._target = target_recall
        self._min_iterations = min_iterations

    def should_stop(self, state: StoppingState) -> bool:
        """Return True when recall exceeds the target and iterations are sufficient."""
        return state.iterations >= self._min_iterations and state.estimated_recall >= self._target


class BudgetStoppingCriterion(StoppingCriterion):
    """Stop when labeling budget is reached."""

    def __init__(self, budget_ratio: float) -> None:
        self._budget_ratio = budget_ratio

    def should_stop(self, state: StoppingState) -> bool:
        """Return True when labeled fraction meets the budget ratio."""
        if state.total_instances <= 0:
            return False
        return (state.labeled_instances / state.total_instances) >= self._budget_ratio


class CompositeStoppingCriterion(StoppingCriterion):
    """Combine multiple stopping criteria."""

    def __init__(self, criteria: Iterable[StoppingCriterion], require_all: bool = True) -> None:
        self._criteria = list(criteria)
        self._require_all = require_all

    def should_stop(self, state: StoppingState) -> bool:
        """Evaluate composite stopping criteria."""
        if not self._criteria:
            return False
        results = [criterion.should_stop(state) for criterion in self._criteria]
        if self._require_all:
            return all(results)
        return any(results)
