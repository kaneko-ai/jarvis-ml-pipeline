"""Active learning configuration and state types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass
class ALConfig:
    """Active learning configuration.

    Args:
        batch_size: Number of samples per iteration after the initial batch.
        initial_samples: Number of samples for the first query.
        max_iterations: Maximum number of iterations to run.
        model_type: Model identifier (used by higher-level wiring).
        target_recall: Target recall for stopping criteria defaults.
    """

    batch_size: int = 10
    initial_samples: int = 20
    max_iterations: int = 100
    model_type: str = "logistic"
    target_recall: float = 0.95


class ALState(Enum):
    """Active learning engine state."""

    IDLE = "idle"
    TRAINING = "training"
    QUERYING = "querying"
    STOPPED = "stopped"
