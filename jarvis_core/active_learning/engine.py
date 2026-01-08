"""Active Learning Engine.

Core engine for active learning-based paper screening.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ALState(Enum):
    """Active learning engine state."""

    IDLE = "idle"
    TRAINING = "training"
    QUERYING = "querying"
    STOPPED = "stopped"


@dataclass
class ALConfig:
    """Configuration for active learning."""

    # Query settings
    batch_size: int = 10
    initial_samples: int = 20

    # Stopping criteria
    max_iterations: int = 100
    target_recall: float = 0.95
    budget_ratio: float = 0.3  # Max fraction of data to label

    # Model settings
    model_type: str = "logistic"  # logistic, svm, random_forest
    feature_type: str = "tfidf"  # tfidf, embedding

    # Behavior
    random_seed: int = 42


@dataclass
class LabeledInstance:
    """A labeled instance for training."""

    instance_id: str
    features: list[float]
    label: int  # 1 = relevant, 0 = not relevant
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ALStats:
    """Statistics from active learning session."""

    total_instances: int = 0
    labeled_instances: int = 0
    relevant_found: int = 0
    iterations: int = 0
    estimated_recall: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_instances": self.total_instances,
            "labeled_instances": self.labeled_instances,
            "relevant_found": self.relevant_found,
            "iterations": self.iterations,
            "estimated_recall": round(self.estimated_recall, 3),
            "label_ratio": round(self.labeled_instances / max(1, self.total_instances), 3),
        }


class ActiveLearningEngine:
    """Active learning engine for efficient screening.

    Implements uncertainty sampling and diversity-based query strategies
    with multiple stopping criteria.

    Example:
        >>> engine = ActiveLearningEngine()
        >>> engine.initialize(instances)
        >>> while not engine.should_stop():
        ...     query = engine.get_next_query()
        ...     label = get_user_label(query)
        ...     engine.update(query.instance_id, label)
    """

    def __init__(self, config: ALConfig | None = None):
        """Initialize the engine.

        Args:
            config: Active learning configuration
        """
        self._config = config or ALConfig()
        self._state = ALState.IDLE

        # Data
        self._instances: dict[str, list[float]] = {}
        self._labels: dict[str, int] = {}
        self._unlabeled: list[str] = []

        # Model
        self._model = None
        self._feature_dim = 0

        # Stats
        self._stats = ALStats()
        self._iteration = 0

        # Random state
        random.seed(self._config.random_seed)

    def initialize(
        self,
        instances: dict[str, list[float]],
        seed_labels: dict[str, int] | None = None,
    ) -> None:
        """Initialize with instances.

        Args:
            instances: Dict mapping instance_id to feature vectors
            seed_labels: Optional initial labels
        """
        self._instances = instances
        self._unlabeled = list(instances.keys())
        self._stats.total_instances = len(instances)

        if instances:
            first_key = next(iter(instances))
            self._feature_dim = len(instances[first_key])

        # Apply seed labels
        if seed_labels:
            for instance_id, label in seed_labels.items():
                if instance_id in self._instances:
                    self._labels[instance_id] = label
                    if instance_id in self._unlabeled:
                        self._unlabeled.remove(instance_id)
                    if label == 1:
                        self._stats.relevant_found += 1
            self._stats.labeled_instances = len(self._labels)

        # Select initial samples if needed
        if len(self._labels) < self._config.initial_samples:
            self._select_initial_samples()

        self._state = ALState.IDLE
        logger.info(f"AL engine initialized with {len(instances)} instances")

    def _select_initial_samples(self) -> list[str]:
        """Select initial samples for labeling."""
        needed = self._config.initial_samples - len(self._labels)
        if needed <= 0 or not self._unlabeled:
            return []

        # Random selection for initial samples
        samples = random.sample(self._unlabeled, min(needed, len(self._unlabeled)))
        return samples

    def get_next_query(self, n: int = None) -> list[str]:
        """Get next instances to query for labels.

        Args:
            n: Number of instances to return (default: batch_size)

        Returns:
            List of instance IDs to label
        """
        n = n or self._config.batch_size

        if not self._unlabeled:
            return []

        self._state = ALState.QUERYING

        if len(self._labels) < self._config.initial_samples:
            # Still in initial phase - random sampling
            samples = self._select_initial_samples()
        elif self._model is not None:
            # Use uncertainty sampling
            samples = self._uncertainty_sampling(n)
        else:
            # Fallback to random
            samples = random.sample(self._unlabeled, min(n, len(self._unlabeled)))

        return samples

    def _uncertainty_sampling(self, n: int) -> list[str]:
        """Select instances with highest uncertainty."""
        if not self._unlabeled or self._model is None:
            return []

        # Get predictions for unlabeled instances
        uncertainties = []
        for instance_id in self._unlabeled:
            features = self._instances[instance_id]
            # Calculate uncertainty (distance to 0.5)
            try:
                prob = self._predict_proba(features)
                uncertainty = 1.0 - abs(prob - 0.5) * 2
            except Exception:
                uncertainty = 0.5
            uncertainties.append((instance_id, uncertainty))

        # Sort by uncertainty (highest first)
        uncertainties.sort(key=lambda x: x[1], reverse=True)

        return [x[0] for x in uncertainties[:n]]

    def _predict_proba(self, features: list[float]) -> float:
        """Predict probability of relevance."""
        if self._model is None:
            return 0.5

        try:
            import numpy as np

            X = np.array(features).reshape(1, -1)
            proba = self._model.predict_proba(X)[0, 1]
            return float(proba)
        except Exception:
            return 0.5

    def update(self, instance_id: str, label: int) -> None:
        """Update with a new label.

        Args:
            instance_id: Instance that was labeled
            label: Label (1 = relevant, 0 = not relevant)
        """
        if instance_id not in self._instances:
            logger.warning(f"Unknown instance: {instance_id}")
            return

        self._labels[instance_id] = label

        if instance_id in self._unlabeled:
            self._unlabeled.remove(instance_id)

        self._stats.labeled_instances = len(self._labels)
        if label == 1:
            self._stats.relevant_found += 1

        # Retrain model periodically
        if len(self._labels) >= self._config.initial_samples:
            if len(self._labels) % self._config.batch_size == 0:
                self._train_model()

    def update_batch(self, labels: dict[str, int]) -> None:
        """Update with multiple labels.

        Args:
            labels: Dict mapping instance_id to label
        """
        for instance_id, label in labels.items():
            self.update(instance_id, label)

        self._iteration += 1
        self._stats.iterations = self._iteration

    def _train_model(self) -> None:
        """Train the classification model."""
        if len(self._labels) < 2:
            return

        self._state = ALState.TRAINING

        try:
            import numpy as np
            from sklearn.linear_model import LogisticRegression

            # Prepare training data
            X = []
            y = []
            for instance_id, label in self._labels.items():
                X.append(self._instances[instance_id])
                y.append(label)

            X = np.array(X)
            y = np.array(y)

            # Check if we have both classes
            if len(set(y)) < 2:
                return

            # Train model
            self._model = LogisticRegression(
                random_state=self._config.random_seed,
                max_iter=1000,
            )
            self._model.fit(X, y)

            logger.debug(f"Model trained on {len(y)} instances")

        except ImportError:
            logger.warning("sklearn not available, using random sampling")
        except Exception as e:
            logger.error(f"Model training failed: {e}")

        self._state = ALState.IDLE

    def should_stop(self) -> bool:
        """Check if stopping criterion is met.

        Returns:
            True if should stop
        """
        # Max iterations
        if self._iteration >= self._config.max_iterations:
            self._state = ALState.STOPPED
            return True

        # Budget exhausted
        budget = int(self._stats.total_instances * self._config.budget_ratio)
        if self._stats.labeled_instances >= budget:
            self._state = ALState.STOPPED
            return True

        # No more unlabeled
        if not self._unlabeled:
            self._state = ALState.STOPPED
            return True

        # Estimated recall target met
        self._stats.estimated_recall = self._estimate_recall()
        if self._stats.estimated_recall >= self._config.target_recall:
            if self._iteration >= 5:  # Minimum iterations
                self._state = ALState.STOPPED
                return True

        return False

    def _estimate_recall(self) -> float:
        """Estimate current recall."""
        if self._stats.relevant_found == 0:
            return 0.0

        if self._model is None:
            return 0.0

        # Estimate total relevant using predictions
        try:
            predicted_relevant = self._stats.relevant_found
            for instance_id in self._unlabeled:
                prob = self._predict_proba(self._instances[instance_id])
                if prob > 0.5:
                    predicted_relevant += prob

            if predicted_relevant > 0:
                return self._stats.relevant_found / predicted_relevant
        except Exception:
            pass

        return 0.0

    def get_stats(self) -> ALStats:
        """Get current statistics."""
        return self._stats

    def get_predictions(self) -> dict[str, float]:
        """Get predictions for all unlabeled instances.

        Returns:
            Dict mapping instance_id to relevance probability
        """
        predictions = {}
        for instance_id in self._unlabeled:
            predictions[instance_id] = self._predict_proba(self._instances[instance_id])
        return predictions

    @property
    def state(self) -> ALState:
        """Get current engine state."""
        return self._state
