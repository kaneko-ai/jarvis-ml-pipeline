"""Active learning engine implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .config import ALConfig, ALState
from .stopping import StoppingCriterion, StoppingState
from .strategies import QueryStrategy, UncertaintySampling


@dataclass
class ALStats:
    """Active learning statistics snapshot."""

    total_instances: int
    labeled_instances: int
    relevant_found: int
    iterations: int
    estimated_recall: float

    def to_dict(self) -> dict[str, int | float]:
        """Serialize stats to a dictionary."""
        return {
            "total_instances": self.total_instances,
            "labeled_instances": self.labeled_instances,
            "relevant_found": self.relevant_found,
            "iterations": self.iterations,
            "estimated_recall": self.estimated_recall,
        }


class ActiveLearningEngine:
    """Simple active learning engine."""

    def __init__(
        self,
        config: ALConfig | None = None,
        strategy: QueryStrategy | None = None,
        stopping: StoppingCriterion | None = None,
    ) -> None:
        self._config = config or ALConfig()
        self._strategy = strategy or UncertaintySampling()
        self._stopping = stopping
        self._instances: dict[str, Sequence[float]] = {}
        self._labels: dict[str, int] = {}
        self._iterations = 0
        self._state = ALState.IDLE

    @property
    def state(self) -> ALState:
        """Return the current engine state."""
        return self._state

    def initialize(self, instances: dict[str, Sequence[float]]) -> None:
        """Load instances into the engine.

        Args:
            instances: Feature vectors keyed by identifier.
        """
        self._instances = dict(instances)
        self._labels = {}
        self._iterations = 0
        self._state = ALState.IDLE

    def get_next_query(self, n: int | None = None) -> list[str]:
        """Return the next batch of candidate ids.

        Args:
            n: Override for batch size. Defaults to config settings.

        Returns:
            Selected identifiers.
        """
        if not self._instances:
            return []
        unlabeled_ids = [key for key in self._instances if key not in self._labels]
        if not unlabeled_ids:
            self._state = ALState.STOPPED
            return []
        if n is None:
            if self._iterations == 0 and not self._labels:
                n = self._config.initial_samples
            else:
                n = self._config.batch_size
        predictions = {item_id: 0.5 for item_id in unlabeled_ids}
        selected = self._strategy.select(unlabeled_ids, self._instances, predictions, n)
        self._state = ALState.QUERYING
        self._iterations += 1
        return selected

    def update(self, instance_id: str, label: int) -> None:
        """Update the engine with a single label.

        Args:
            instance_id: Identifier to update.
            label: Label value (1 = relevant, 0 = not relevant).
        """
        self._labels[instance_id] = int(label)
        self._state = ALState.TRAINING

    def update_batch(self, labels: dict[str, int]) -> None:
        """Update the engine with a batch of labels.

        Args:
            labels: Mapping of identifier to label.
        """
        for key, value in labels.items():
            self._labels[key] = int(value)
        self._state = ALState.TRAINING

    def get_stats(self) -> ALStats:
        """Return the current engine statistics."""
        total_instances = len(self._instances)
        labeled_instances = len(self._labels)
        relevant_found = sum(1 for value in self._labels.values() if value == 1)
        estimated_recall = relevant_found / total_instances if total_instances > 0 else 0.0
        return ALStats(
            total_instances=total_instances,
            labeled_instances=labeled_instances,
            relevant_found=relevant_found,
            iterations=self._iterations,
            estimated_recall=estimated_recall,
        )

    def should_stop(self) -> bool:
        """Evaluate stopping criteria if configured."""
        if self._stopping is None:
            return False
        stats = self.get_stats()
        state = StoppingState(
            total_instances=stats.total_instances,
            labeled_instances=stats.labeled_instances,
            relevant_found=stats.relevant_found,
            iterations=stats.iterations,
            estimated_recall=stats.estimated_recall,
            predictions=[],
        )
        return self._stopping.should_stop(state)
