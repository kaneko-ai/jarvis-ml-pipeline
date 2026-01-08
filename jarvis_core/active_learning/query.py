"""Query Strategies for Active Learning.

Different strategies for selecting instances to label.
"""

from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class QueryStrategy(ABC):
    """Base class for query strategies."""

    @abstractmethod
    def select(
        self,
        unlabeled_ids: list[str],
        features: dict[str, list[float]],
        predictions: dict[str, float],
        n: int,
    ) -> list[str]:
        """Select instances to query.
        
        Args:
            unlabeled_ids: IDs of unlabeled instances
            features: Feature vectors for all instances
            predictions: Model predictions (probabilities) for unlabeled
            n: Number of instances to select
            
        Returns:
            List of selected instance IDs
        """
        pass


class UncertaintySampling(QueryStrategy):
    """Select instances with highest prediction uncertainty."""

    def select(
        self,
        unlabeled_ids: list[str],
        features: dict[str, list[float]],
        predictions: dict[str, float],
        n: int,
    ) -> list[str]:
        """Select most uncertain instances."""
        if not unlabeled_ids:
            return []

        # Calculate uncertainty (closer to 0.5 = more uncertain)
        uncertainties = []
        for instance_id in unlabeled_ids:
            prob = predictions.get(instance_id, 0.5)
            uncertainty = 1.0 - abs(prob - 0.5) * 2
            uncertainties.append((instance_id, uncertainty))

        # Sort by uncertainty (highest first)
        uncertainties.sort(key=lambda x: x[1], reverse=True)

        return [x[0] for x in uncertainties[:n]]


class DiversitySampling(QueryStrategy):
    """Select diverse instances based on feature distance."""

    def __init__(self, uncertainty_weight: float = 0.5):
        """Initialize with uncertainty weighting.
        
        Args:
            uncertainty_weight: Weight for uncertainty vs diversity (0-1)
        """
        self._uncertainty_weight = uncertainty_weight

    def select(
        self,
        unlabeled_ids: list[str],
        features: dict[str, list[float]],
        predictions: dict[str, float],
        n: int,
    ) -> list[str]:
        """Select diverse and uncertain instances."""
        if not unlabeled_ids:
            return []

        if n >= len(unlabeled_ids):
            return unlabeled_ids

        selected = []
        remaining = list(unlabeled_ids)

        try:
            import numpy as np

            # Convert features to numpy
            feature_matrix = np.array([features[id] for id in remaining])

            # Start with most uncertain
            uncertainties = {
                id: 1.0 - abs(predictions.get(id, 0.5) - 0.5) * 2
                for id in remaining
            }

            first_id = max(remaining, key=lambda x: uncertainties[x])
            selected.append(first_id)
            remaining.remove(first_id)

            # Greedy selection for diversity
            while len(selected) < n and remaining:
                # Calculate min distance to selected set for each remaining
                selected_indices = [unlabeled_ids.index(s) for s in selected]
                selected_features = feature_matrix[selected_indices]

                best_id = None
                best_score = -1

                for id in remaining:
                    idx = unlabeled_ids.index(id)
                    feat = feature_matrix[idx].reshape(1, -1)

                    # Min distance to selected
                    distances = np.linalg.norm(selected_features - feat, axis=1)
                    min_dist = np.min(distances) if len(distances) > 0 else 1.0

                    # Combined score
                    uncertainty = uncertainties[id]
                    score = (
                        self._uncertainty_weight * uncertainty +
                        (1 - self._uncertainty_weight) * min_dist
                    )

                    if score > best_score:
                        best_score = score
                        best_id = id

                if best_id:
                    selected.append(best_id)
                    remaining.remove(best_id)
                else:
                    break

            return selected

        except ImportError:
            # Fallback to random
            return random.sample(remaining, min(n, len(remaining)))


class RandomSampling(QueryStrategy):
    """Random instance selection."""

    def __init__(self, seed: int = 42):
        """Initialize with random seed."""
        self._rng = random.Random(seed)

    def select(
        self,
        unlabeled_ids: list[str],
        features: dict[str, list[float]],
        predictions: dict[str, float],
        n: int,
    ) -> list[str]:
        """Select random instances."""
        if not unlabeled_ids:
            return []

        return self._rng.sample(unlabeled_ids, min(n, len(unlabeled_ids)))


class BalancedSampling(QueryStrategy):
    """Sample to balance predicted classes."""

    def select(
        self,
        unlabeled_ids: list[str],
        features: dict[str, list[float]],
        predictions: dict[str, float],
        n: int,
    ) -> list[str]:
        """Select balanced mix of predicted classes."""
        if not unlabeled_ids:
            return []

        # Split by predicted class
        predicted_pos = [
            (id, predictions.get(id, 0.5))
            for id in unlabeled_ids
            if predictions.get(id, 0.5) > 0.5
        ]
        predicted_neg = [
            (id, predictions.get(id, 0.5))
            for id in unlabeled_ids
            if predictions.get(id, 0.5) <= 0.5
        ]

        # Sort by uncertainty within each class
        predicted_pos.sort(key=lambda x: abs(x[1] - 0.5))
        predicted_neg.sort(key=lambda x: abs(x[1] - 0.5))

        # Interleave
        selected = []
        pos_idx = 0
        neg_idx = 0

        while len(selected) < n:
            if pos_idx < len(predicted_pos) and neg_idx < len(predicted_neg):
                if len(selected) % 2 == 0:
                    selected.append(predicted_pos[pos_idx][0])
                    pos_idx += 1
                else:
                    selected.append(predicted_neg[neg_idx][0])
                    neg_idx += 1
            elif pos_idx < len(predicted_pos):
                selected.append(predicted_pos[pos_idx][0])
                pos_idx += 1
            elif neg_idx < len(predicted_neg):
                selected.append(predicted_neg[neg_idx][0])
                neg_idx += 1
            else:
                break

        return selected
