"""Chaos Engineering Framework.

Per RP-580, implements failure injection for testing resilience.
"""

from __future__ import annotations

import random
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any


class ChaosType(Enum):
    """Types of chaos experiments."""

    LATENCY = "latency"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    NETWORK = "network"


@dataclass
class ChaosConfig:
    """Chaos experiment configuration."""

    enabled: bool = False
    probability: float = 0.1  # 10% chance
    min_latency_ms: float = 100
    max_latency_ms: float = 5000
    failure_rate: float = 0.1
    timeout_rate: float = 0.05
    targets: list[str] = field(default_factory=list)


@dataclass
class ChaosExperiment:
    """A chaos experiment."""

    experiment_id: str
    name: str
    chaos_type: ChaosType
    config: dict[str, Any]
    started_at: float | None = None
    ended_at: float | None = None
    affected_calls: int = 0


class ChaosMonkey:
    """Chaos engineering framework.

    Per RP-580:
    - Failure injection
    - Latency injection
    - Resource exhaustion
    - Game days support
    """

    def __init__(self, config: ChaosConfig | None = None):
        self.config = config or ChaosConfig()
        self._experiments: dict[str, ChaosExperiment] = {}
        self._active_experiments: list[str] = []
        self._lock = threading.Lock()

    def is_enabled(self) -> bool:
        """Check if chaos is enabled."""
        return self.config.enabled

    def enable(self) -> None:
        """Enable chaos engineering."""
        self.config.enabled = True

    def disable(self) -> None:
        """Disable chaos engineering."""
        self.config.enabled = False
        self._active_experiments.clear()

    def start_experiment(
        self,
        name: str,
        chaos_type: ChaosType,
        config: dict[str, Any] | None = None,
    ) -> ChaosExperiment:
        """Start a chaos experiment.

        Args:
            name: Experiment name.
            chaos_type: Type of chaos.
            config: Experiment config.

        Returns:
            Started experiment.
        """
        import uuid

        exp_id = str(uuid.uuid4())[:8]
        experiment = ChaosExperiment(
            experiment_id=exp_id,
            name=name,
            chaos_type=chaos_type,
            config=config or {},
            started_at=time.time(),
        )

        with self._lock:
            self._experiments[exp_id] = experiment
            self._active_experiments.append(exp_id)

        return experiment

    def stop_experiment(self, experiment_id: str) -> None:
        """Stop a chaos experiment.

        Args:
            experiment_id: Experiment ID.
        """
        with self._lock:
            if experiment_id in self._experiments:
                self._experiments[experiment_id].ended_at = time.time()
            if experiment_id in self._active_experiments:
                self._active_experiments.remove(experiment_id)

    def inject_latency(
        self,
        target: str | None = None,
    ) -> float:
        """Inject latency if enabled.

        Args:
            target: Target service/function.

        Returns:
            Injected latency in seconds.
        """
        if not self.is_enabled():
            return 0.0

        if target and self.config.targets and target not in self.config.targets:
            return 0.0

        if random.random() > self.config.probability:
            return 0.0

        latency_ms = random.uniform(
            self.config.min_latency_ms,
            self.config.max_latency_ms,
        )
        latency_s = latency_ms / 1000

        time.sleep(latency_s)

        # Record in active experiments
        for exp_id in self._active_experiments:
            if self._experiments[exp_id].chaos_type == ChaosType.LATENCY:
                self._experiments[exp_id].affected_calls += 1

        return latency_s

    def should_fail(
        self,
        target: str | None = None,
    ) -> bool:
        """Check if should inject failure.

        Args:
            target: Target service/function.

        Returns:
            True if should fail.
        """
        if not self.is_enabled():
            return False

        if target and self.config.targets and target not in self.config.targets:
            return False

        should_fail = random.random() < self.config.failure_rate

        if should_fail:
            for exp_id in self._active_experiments:
                if self._experiments[exp_id].chaos_type == ChaosType.FAILURE:
                    self._experiments[exp_id].affected_calls += 1

        return should_fail

    def should_timeout(
        self,
        target: str | None = None,
    ) -> bool:
        """Check if should inject timeout.

        Args:
            target: Target service/function.

        Returns:
            True if should timeout.
        """
        if not self.is_enabled():
            return False

        if target and self.config.targets and target not in self.config.targets:
            return False

        return random.random() < self.config.timeout_rate

    def get_experiment_results(
        self,
        experiment_id: str,
    ) -> dict[str, Any] | None:
        """Get experiment results.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Experiment results.
        """
        exp = self._experiments.get(experiment_id)
        if not exp:
            return None

        return {
            "experiment_id": exp.experiment_id,
            "name": exp.name,
            "chaos_type": exp.chaos_type.value,
            "started_at": exp.started_at,
            "ended_at": exp.ended_at,
            "duration_seconds": (exp.ended_at or time.time()) - exp.started_at,
            "affected_calls": exp.affected_calls,
        }


# Global chaos monkey instance
_chaos_monkey: ChaosMonkey | None = None


def get_chaos_monkey() -> ChaosMonkey:
    """Get global chaos monkey."""
    global _chaos_monkey
    if _chaos_monkey is None:
        _chaos_monkey = ChaosMonkey()
    return _chaos_monkey


def chaos_enabled(func: Callable) -> Callable:
    """Decorator to inject chaos into function calls."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        monkey = get_chaos_monkey()
        target = func.__name__

        # Inject latency
        monkey.inject_latency(target)

        # Check for failure
        if monkey.should_fail(target):
            raise ChaosException(f"Chaos failure injected for {target}")

        # Check for timeout
        if monkey.should_timeout(target):
            raise TimeoutError(f"Chaos timeout injected for {target}")

        return func(*args, **kwargs)

    return wrapper


class ChaosException(Exception):
    """Exception raised by chaos injection."""

    pass