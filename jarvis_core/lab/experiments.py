"""Experiment management helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExperimentConfig:
    """Configuration for an experiment."""

    name: str
    params: dict[str, Any] = field(default_factory=dict)


class ExperimentRunner:
    """Minimal experiment runner."""

    def run(self, config: ExperimentConfig) -> dict[str, Any]:
        """Run an experiment.

        Args:
            config: Experiment configuration.

        Returns:
            Result dictionary.
        """
        return {"name": config.name, "status": "skipped", "params": dict(config.params)}


__all__ = ["ExperimentConfig", "ExperimentRunner"]
