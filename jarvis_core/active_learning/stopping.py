"""Stopping Criteria for Active Learning.

Determines when to stop the active learning loop.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StoppingState:
    """State information for stopping criteria."""

    total_instances: int
    labeled_instances: int
    relevant_found: int
    iterations: int
    estimated_recall: float
    predictions: list[float]  # Predicted probabilities for unlabeled


class StoppingCriterion(ABC):
    """Base class for stopping criteria."""

    @abstractmethod
    def should_stop(self, state: StoppingState) -> bool:
        """Check if stopping criterion is met.
        
        Args:
            state: Current AL state
            
        Returns:
            True if should stop
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get criterion name."""
        pass


class RecallStoppingCriterion(StoppingCriterion):
    """Stop when estimated recall reaches target."""

    def __init__(
        self,
        target_recall: float = 0.95,
        min_iterations: int = 5,
    ):
        """Initialize with target recall.
        
        Args:
            target_recall: Target recall to achieve (0-1)
            min_iterations: Minimum iterations before stopping
        """
        self._target = target_recall
        self._min_iterations = min_iterations

    def should_stop(self, state: StoppingState) -> bool:
        """Check if recall target is met."""
        if state.iterations < self._min_iterations:
            return False

        return state.estimated_recall >= self._target

    @property
    def name(self) -> str:
        return f"RecallTarget({self._target:.0%})"


class BudgetStoppingCriterion(StoppingCriterion):
    """Stop when labeling budget is exhausted."""

    def __init__(self, budget_ratio: float = 0.3):
        """Initialize with budget ratio.
        
        Args:
            budget_ratio: Maximum fraction of data to label
        """
        self._budget_ratio = budget_ratio

    def should_stop(self, state: StoppingState) -> bool:
        """Check if budget is exhausted."""
        budget = int(state.total_instances * self._budget_ratio)
        return state.labeled_instances >= budget

    @property
    def name(self) -> str:
        return f"Budget({self._budget_ratio:.0%})"


class IterationStoppingCriterion(StoppingCriterion):
    """Stop after maximum iterations."""

    def __init__(self, max_iterations: int = 100):
        """Initialize with max iterations.
        
        Args:
            max_iterations: Maximum number of iterations
        """
        self._max_iterations = max_iterations

    def should_stop(self, state: StoppingState) -> bool:
        """Check if max iterations reached."""
        return state.iterations >= self._max_iterations

    @property
    def name(self) -> str:
        return f"MaxIterations({self._max_iterations})"


class ConsecutiveNegativeStoppingCriterion(StoppingCriterion):
    """Stop after consecutive negative labels."""

    def __init__(self, consecutive_count: int = 50):
        """Initialize with consecutive count.
        
        Args:
            consecutive_count: Number of consecutive negatives to trigger stop
        """
        self._count = consecutive_count
        self._consecutive_negatives = 0
        self._last_relevant = 0

    def should_stop(self, state: StoppingState) -> bool:
        """Check if enough consecutive negatives."""
        if state.relevant_found > self._last_relevant:
            self._consecutive_negatives = 0
            self._last_relevant = state.relevant_found
        else:
            self._consecutive_negatives += 1

        return self._consecutive_negatives >= self._count

    @property
    def name(self) -> str:
        return f"ConsecutiveNegatives({self._count})"


class KneeStoppingCriterion(StoppingCriterion):
    """Stop when recall curve reaches knee point."""

    def __init__(self, window_size: int = 10, min_iterations: int = 20):
        """Initialize with window size.
        
        Args:
            window_size: Window for detecting plateau
            min_iterations: Minimum iterations before checking
        """
        self._window_size = window_size
        self._min_iterations = min_iterations
        self._recall_history: list[float] = []

    def should_stop(self, state: StoppingState) -> bool:
        """Check if at knee point."""
        self._recall_history.append(state.estimated_recall)

        if state.iterations < self._min_iterations:
            return False

        if len(self._recall_history) < self._window_size:
            return False

        # Check if recall has plateaued
        recent = self._recall_history[-self._window_size:]
        improvement = recent[-1] - recent[0]

        # Stop if improvement is minimal
        return improvement < 0.01

    @property
    def name(self) -> str:
        return "KneeDetection"


class CompositeStoppingCriterion(StoppingCriterion):
    """Combines multiple stopping criteria."""

    def __init__(
        self,
        criteria: list[StoppingCriterion],
        require_all: bool = False,
    ):
        """Initialize with multiple criteria.
        
        Args:
            criteria: List of stopping criteria
            require_all: If True, all must be met; if False, any
        """
        self._criteria = criteria
        self._require_all = require_all

    def should_stop(self, state: StoppingState) -> bool:
        """Check if criteria are met."""
        results = [c.should_stop(state) for c in self._criteria]

        if self._require_all:
            return all(results)
        else:
            return any(results)

    @property
    def name(self) -> str:
        op = "AND" if self._require_all else "OR"
        names = [c.name for c in self._criteria]
        return f"Composite({op}: {', '.join(names)})"
