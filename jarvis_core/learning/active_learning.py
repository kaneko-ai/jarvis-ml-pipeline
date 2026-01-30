"""Active Learning System for JARVIS.

Per JARVIS_LOCALFIRST_ROADMAP Task 2.5: Active Learning
Implements active learning for evidence screening and classification.
"""

from __future__ import annotations

import logging
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SamplingStrategy(Enum):
    """Active learning sampling strategies."""

    UNCERTAINTY = "uncertainty"  # Sample most uncertain
    DIVERSITY = "diversity"  # Sample most diverse
    RANDOM = "random"  # Random sampling
    COMBINED = "combined"  # Uncertainty + diversity


class Label(Enum):
    """Labeling options."""

    INCLUDE = "include"
    EXCLUDE = "exclude"
    UNCERTAIN = "uncertain"
    SKIP = "skip"


@dataclass
class LabeledSample:
    """A labeled training sample."""

    sample_id: str
    text: str
    label: Label | None = None
    confidence: float = 0.0
    feedback: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_labeled(self) -> bool:
        return self.label is not None


@dataclass
class ActiveLearningState:
    """State of the active learning process."""

    total_samples: int = 0
    labeled_count: int = 0
    include_count: int = 0
    exclude_count: int = 0
    uncertain_count: int = 0
    current_round: int = 0
    model_accuracy: float = 0.0
    estimated_remaining: int = 0


class UncertaintySampler:
    """Samples based on model uncertainty."""

    def __init__(self, classifier: Callable | None = None):
        self.classifier = classifier

    def get_uncertainty(self, text: str) -> float:
        """Calculate uncertainty score for a sample."""
        if self.classifier is None:
            # Without classifier, use heuristics
            return self._heuristic_uncertainty(text)

        try:
            prob = self.classifier(text)
            # Uncertainty is highest when prob is near 0.5
            return 1.0 - abs(prob - 0.5) * 2
        except Exception:
            return 0.5

    def _heuristic_uncertainty(self, text: str) -> float:
        """Heuristic uncertainty based on text features."""
        text_lower = text.lower()

        # Keywords that suggest clear inclusion/exclusion
        clear_include = ["significant", "effective", "demonstrated", "confirmed"]
        clear_exclude = ["not significant", "failed", "no effect", "excluded"]

        include_score = sum(1 for kw in clear_include if kw in text_lower)
        exclude_score = sum(1 for kw in clear_exclude if kw in text_lower)

        # High uncertainty if both or neither present
        total = include_score + exclude_score
        if total == 0:
            return 0.8  # No clear signals

        balance = abs(include_score - exclude_score) / total
        return 1.0 - balance  # More balanced = more uncertain

    def sample(
        self,
        candidates: list[LabeledSample],
        n: int = 10,
    ) -> list[LabeledSample]:
        """Sample n most uncertain unlabeled samples."""
        unlabeled = [s for s in candidates if not s.is_labeled]

        # Score by uncertainty
        scored = [(s, self.get_uncertainty(s.text)) for s in unlabeled]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [s for s, _ in scored[:n]]


class DiversitySampler:
    """Samples based on diversity (coverage of feature space)."""

    def __init__(self, embedder: Callable | None = None):
        self.embedder = embedder

    def sample(
        self,
        candidates: list[LabeledSample],
        n: int = 10,
        already_selected: list[LabeledSample] | None = None,
    ) -> list[LabeledSample]:
        """Sample n most diverse unlabeled samples."""
        unlabeled = [s for s in candidates if not s.is_labeled]

        if len(unlabeled) <= n:
            return unlabeled

        # Simple diversity: sample from different "clusters"
        # Without embeddings, use text length buckets as proxy
        buckets: dict[int, list[LabeledSample]] = {}
        for s in unlabeled:
            bucket = len(s.text) // 100  # 100-char buckets
            if bucket not in buckets:
                buckets[bucket] = []
            buckets[bucket].append(s)

        # Round-robin from buckets
        selected = []
        bucket_keys = list(buckets.keys())
        idx = 0

        while len(selected) < n and bucket_keys:
            bucket = bucket_keys[idx % len(bucket_keys)]
            if buckets[bucket]:
                selected.append(buckets[bucket].pop())
            else:
                bucket_keys.remove(bucket)
            idx += 1

        return selected


class ActiveLearner:
    """Active learning loop controller."""

    def __init__(
        self,
        samples: list[dict],
        strategy: SamplingStrategy = SamplingStrategy.COMBINED,
        batch_size: int = 10,
    ):
        self.strategy = strategy
        self.batch_size = batch_size

        # Convert to LabeledSample
        self.samples = [
            LabeledSample(
                sample_id=s.get("id", str(i)),
                text=s.get("text", s.get("abstract", "")),
                metadata=s,
            )
            for i, s in enumerate(samples)
        ]

        self.uncertainty_sampler = UncertaintySampler()
        self.diversity_sampler = DiversitySampler()
        self.current_round = 0
        self._history: list[dict] = []

    def get_state(self) -> ActiveLearningState:
        """Get current state."""
        labeled = [s for s in self.samples if s.is_labeled]

        return ActiveLearningState(
            total_samples=len(self.samples),
            labeled_count=len(labeled),
            include_count=sum(1 for s in labeled if s.label == Label.INCLUDE),
            exclude_count=sum(1 for s in labeled if s.label == Label.EXCLUDE),
            uncertain_count=sum(1 for s in labeled if s.label == Label.UNCERTAIN),
            current_round=self.current_round,
            estimated_remaining=len(self.samples) - len(labeled),
        )

    def get_next_batch(self) -> list[LabeledSample]:
        """Get next batch for labeling."""
        unlabeled = [s for s in self.samples if not s.is_labeled]

        if not unlabeled:
            return []

        if self.strategy == SamplingStrategy.UNCERTAINTY:
            return self.uncertainty_sampler.sample(unlabeled, self.batch_size)
        elif self.strategy == SamplingStrategy.DIVERSITY:
            return self.diversity_sampler.sample(unlabeled, self.batch_size)
        elif self.strategy == SamplingStrategy.RANDOM:
            return random.sample(unlabeled, min(self.batch_size, len(unlabeled)))
        else:  # COMBINED
            n_uncertain = self.batch_size // 2
            n_diverse = self.batch_size - n_uncertain

            uncertain = self.uncertainty_sampler.sample(unlabeled, n_uncertain)
            remaining = [s for s in unlabeled if s not in uncertain]
            diverse = self.diversity_sampler.sample(remaining, n_diverse)

            return uncertain + diverse

    def submit_labels(
        self,
        labels: list[tuple[str, Label, str | None]],
    ) -> int:
        """Submit labels for samples.

        Args:
            labels: List of (sample_id, label, optional_feedback).

        Returns:
            Number of labels applied.
        """
        sample_map = {s.sample_id: s for s in self.samples}
        applied = 0

        for item in labels:
            sample_id = item[0]
            label = item[1]
            feedback = item[2] if len(item) > 2 else ""

            if sample_id in sample_map:
                sample_map[sample_id].label = label
                sample_map[sample_id].feedback = feedback or ""
                applied += 1

        if applied > 0:
            self.current_round += 1
            self._history.append(
                {
                    "round": self.current_round,
                    "labels_applied": applied,
                    "state": self.get_state().__dict__,
                }
            )

        return applied

    def get_labeled_samples(self) -> tuple[list[LabeledSample], list[LabeledSample]]:
        """Get included and excluded samples."""
        included = [s for s in self.samples if s.label == Label.INCLUDE]
        excluded = [s for s in self.samples if s.label == Label.EXCLUDE]
        return included, excluded

    def should_continue(self, min_labeled: int = 10) -> bool:
        """Check if more labeling is needed."""
        state = self.get_state()
        unlabeled_ratio = state.estimated_remaining / max(state.total_samples, 1)

        # Stop if:
        # 1. All labeled, or
        # 2. Less than 5% unlabeled and at least min_labeled done
        if state.estimated_remaining == 0:
            return False
        if unlabeled_ratio < 0.05 and state.labeled_count >= min_labeled:
            return False

        return True

    def get_history(self) -> list[dict]:
        """Get labeling history."""
        return self._history


def create_active_learner(
    samples: list[dict],
    strategy: str = "combined",
    batch_size: int = 10,
) -> ActiveLearner:
    """Create an active learner instance.

    Args:
        samples: List of sample dictionaries with 'id' and 'text'.
        strategy: Sampling strategy ('uncertainty', 'diversity', 'random', 'combined').
        batch_size: Number of samples per labeling round.

    Returns:
        ActiveLearner instance.
    """
    strategy_map = {
        "uncertainty": SamplingStrategy.UNCERTAINTY,
        "diversity": SamplingStrategy.DIVERSITY,
        "random": SamplingStrategy.RANDOM,
        "combined": SamplingStrategy.COMBINED,
    }

    return ActiveLearner(
        samples=samples,
        strategy=strategy_map.get(strategy, SamplingStrategy.COMBINED),
        batch_size=batch_size,
    )