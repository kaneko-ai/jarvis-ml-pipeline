"""Query strategies for active learning."""

from __future__ import annotations

from typing import Iterable, Sequence


class QueryStrategy:
    """Base class for query strategies."""

    def select(
        self,
        unlabeled_ids: Sequence[str],
        features: dict[str, Sequence[float]],
        predictions: dict[str, float],
        n: int,
    ) -> list[str]:
        """Select the next batch of samples.

        Args:
            unlabeled_ids: Candidate sample identifiers.
            features: Feature vectors keyed by identifier.
            predictions: Model prediction scores keyed by identifier.
            n: Maximum number of samples to select.

        Returns:
            Selected identifiers in priority order.
        """
        raise NotImplementedError


class UncertaintySampling(QueryStrategy):
    """Select items closest to the decision boundary."""

    def select(
        self,
        unlabeled_ids: Sequence[str],
        features: dict[str, Sequence[float]],
        predictions: dict[str, float],
        n: int,
    ) -> list[str]:
        """Select items with prediction scores closest to 0.5.

        Args:
            unlabeled_ids: Candidate sample identifiers.
            features: Feature vectors keyed by identifier.
            predictions: Model prediction scores keyed by identifier.
            n: Maximum number of samples to select.

        Returns:
            Selected identifiers ordered by uncertainty.
        """
        if n <= 0 or not unlabeled_ids:
            return []
        scored = []
        for item_id in unlabeled_ids:
            pred = predictions.get(item_id, 0.5)
            uncertainty = abs(pred - 0.5)
            scored.append((uncertainty, item_id))
        scored.sort(key=lambda item: item[0])
        return [item_id for _, item_id in scored[:n]]


class DiversitySampling(QueryStrategy):
    """Select uncertain yet diverse samples."""

    def __init__(self, uncertainty_weight: float = 0.7) -> None:
        self._uncertainty_weight = uncertainty_weight

    def select(
        self,
        unlabeled_ids: Sequence[str],
        features: dict[str, Sequence[float]],
        predictions: dict[str, float],
        n: int,
    ) -> list[str]:
        """Select a diverse batch with a bias toward uncertainty.

        Args:
            unlabeled_ids: Candidate sample identifiers.
            features: Feature vectors keyed by identifier.
            predictions: Model prediction scores keyed by identifier.
            n: Maximum number of samples to select.

        Returns:
            Selected identifiers.
        """
        if n <= 0 or not unlabeled_ids:
            return []

        scored = []
        for item_id in unlabeled_ids:
            pred = predictions.get(item_id, 0.5)
            uncertainty = abs(pred - 0.5)
            scored.append((uncertainty, item_id))
        scored.sort(key=lambda item: item[0])

        selected: list[str] = []
        remaining = [item_id for _, item_id in scored]
        if not remaining:
            return []

        selected.append(remaining.pop(0))

        while remaining and len(selected) < n:
            best_id = None
            best_score = None
            for candidate in remaining:
                diversity = _min_distance(candidate, selected, features)
                uncertainty = abs(predictions.get(candidate, 0.5) - 0.5)
                score = (1.0 - self._uncertainty_weight) * diversity + (
                    self._uncertainty_weight * (1.0 - uncertainty)
                )
                if best_score is None or score > best_score:
                    best_score = score
                    best_id = candidate
            if best_id is None:
                break
            selected.append(best_id)
            remaining.remove(best_id)

        return selected[:n]


def _min_distance(
    candidate: str,
    selected: Iterable[str],
    features: dict[str, Sequence[float]],
) -> float:
    """Compute the minimum distance to selected items."""
    candidate_vec = _vector_for(candidate, features)
    distances = []
    for selected_id in selected:
        selected_vec = _vector_for(selected_id, features)
        distances.append(_euclidean(candidate_vec, selected_vec))
    return min(distances) if distances else 0.0


def _vector_for(item_id: str, features: dict[str, Sequence[float]]) -> list[float]:
    """Return a dense vector for the given id."""
    vec = features.get(item_id)
    if vec is None or len(vec) == 0:
        return [0.0]
    return [float(value) for value in vec]


def _euclidean(left: Sequence[float], right: Sequence[float]) -> float:
    """Compute Euclidean distance between two vectors."""
    size = max(len(left), len(right))
    total = 0.0
    for index in range(size):
        l_val = left[index] if index < len(left) else 0.0
        r_val = right[index] if index < len(right) else 0.0
        total += (l_val - r_val) ** 2
    return total**0.5
