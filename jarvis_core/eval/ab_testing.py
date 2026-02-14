"""A/B Testing Framework.

Per RP-377, implements A/B testing for experiments.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Experiment:
    """An A/B experiment definition."""

    experiment_id: str
    name: str
    variants: list[str]
    traffic_split: dict[str, float]  # variant -> percentage
    start_date: str
    end_date: str | None
    status: str  # draft, running, completed
    metrics: list[str]


@dataclass
class ExperimentResult:
    """Results from an experiment."""

    experiment_id: str
    variant: str
    metric: str
    value: float
    sample_size: int
    confidence: float


class ABTestingFramework:
    """A/B testing framework for experiments.

    Per RP-377:
    - Experiment definition UI
    - Traffic splitting
    - Statistical tests
    """

    def __init__(
        self,
        experiments_dir: str = "experiments",
    ):
        self.experiments_dir = Path(experiments_dir)
        self.experiments_dir.mkdir(parents=True, exist_ok=True)
        self._experiments: dict[str, Experiment] = {}

    def create_experiment(
        self,
        name: str,
        variants: list[str],
        traffic_split: dict[str, float] | None = None,
        metrics: list[str] | None = None,
    ) -> Experiment:
        """Create a new experiment.

        Args:
            name: Experiment name.
            variants: List of variant names.
            traffic_split: Traffic allocation per variant.
            metrics: Metrics to track.

        Returns:
            Created experiment.
        """
        exp_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Default equal split
        if traffic_split is None:
            split = 1.0 / len(variants)
            traffic_split = dict.fromkeys(variants, split)

        experiment = Experiment(
            experiment_id=exp_id,
            name=name,
            variants=variants,
            traffic_split=traffic_split,
            start_date=datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z",
            end_date=None,
            status="draft",
            metrics=metrics or ["success_rate"],
        )

        self._experiments[exp_id] = experiment
        self._save_experiment(experiment)

        return experiment

    def assign_variant(
        self,
        experiment_id: str,
        user_id: str,
    ) -> str:
        """Assign a user to a variant.

        Args:
            experiment_id: Experiment ID.
            user_id: User identifier.

        Returns:
            Assigned variant name.
        """
        experiment = self._experiments.get(experiment_id)
        if not experiment or experiment.status != "running":
            return experiment.variants[0] if experiment else "control"

        # Deterministic assignment based on hash
        hash_input = f"{experiment_id}:{user_id}"
        hash_val = int(hashlib.md5(hash_input.encode(), usedforsecurity=False).hexdigest(), 16)
        bucket = (hash_val % 10000) / 10000.0

        cumulative = 0.0
        for variant, split in experiment.traffic_split.items():
            cumulative += split
            if bucket < cumulative:
                return variant

        return experiment.variants[-1]

    def record_metric(
        self,
        experiment_id: str,
        variant: str,
        metric: str,
        value: float,
    ) -> None:
        """Record a metric observation.

        Args:
            experiment_id: Experiment ID.
            variant: Variant name.
            metric: Metric name.
            value: Metric value.
        """
        log_path = self.experiments_dir / experiment_id / "metrics.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        with open(log_path, "a") as f:
            f.write(
                json.dumps(
                    {
                        "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
                        + "Z",
                        "variant": variant,
                        "metric": metric,
                        "value": value,
                    }
                )
                + "\n"
            )

    def analyze_experiment(
        self,
        experiment_id: str,
    ) -> list[ExperimentResult]:
        """Analyze experiment results.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Results per variant per metric.
        """
        log_path = self.experiments_dir / experiment_id / "metrics.jsonl"
        if not log_path.exists():
            return []

        # Load metrics
        data: dict[str, dict[str, list[float]]] = {}

        with open(log_path) as f:
            for line in f:
                entry = json.loads(line)
                variant = entry["variant"]
                metric = entry["metric"]
                value = entry["value"]

                if variant not in data:
                    data[variant] = {}
                if metric not in data[variant]:
                    data[variant][metric] = []

                data[variant][metric].append(value)

        # Calculate results
        results = []
        for variant, metrics in data.items():
            for metric, values in metrics.items():
                if values:
                    results.append(
                        ExperimentResult(
                            experiment_id=experiment_id,
                            variant=variant,
                            metric=metric,
                            value=sum(values) / len(values),
                            sample_size=len(values),
                            confidence=self._calculate_confidence(values),
                        )
                    )

        return results

    def _calculate_confidence(self, values: list[float]) -> float:
        """Calculate confidence in metric."""
        if len(values) < 30:
            return 0.5
        elif len(values) < 100:
            return 0.7
        else:
            return 0.9

    def _save_experiment(self, experiment: Experiment) -> None:
        """Save experiment to disk."""
        exp_dir = self.experiments_dir / experiment.experiment_id
        exp_dir.mkdir(parents=True, exist_ok=True)

        with open(exp_dir / "config.json", "w") as f:
            json.dump(
                {
                    "experiment_id": experiment.experiment_id,
                    "name": experiment.name,
                    "variants": experiment.variants,
                    "traffic_split": experiment.traffic_split,
                    "start_date": experiment.start_date,
                    "end_date": experiment.end_date,
                    "status": experiment.status,
                    "metrics": experiment.metrics,
                },
                f,
                indent=2,
            )

    def start_experiment(self, experiment_id: str) -> None:
        """Start an experiment."""
        if experiment_id in self._experiments:
            self._experiments[experiment_id].status = "running"
            self._save_experiment(self._experiments[experiment_id])

    def stop_experiment(self, experiment_id: str) -> None:
        """Stop an experiment."""
        if experiment_id in self._experiments:
            self._experiments[experiment_id].status = "completed"
            self._experiments[experiment_id].end_date = (
                datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
            )
            self._save_experiment(self._experiments[experiment_id])
