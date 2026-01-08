"""Canary Deployment Manager for JARVIS.

Per RP-510, implements canary and blue-green deployment strategies.
"""
from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DeploymentStrategy(Enum):
    """Deployment strategies."""
    ROLLING = "rolling"
    CANARY = "canary"
    BLUE_GREEN = "blue_green"
    RECREATE = "recreate"


class DeploymentStatus(Enum):
    """Deployment status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class CanaryConfig:
    """Canary deployment configuration."""
    initial_weight: float = 0.1  # 10% initial traffic
    increment: float = 0.1  # 10% increment per step
    max_weight: float = 1.0  # 100% final traffic
    step_interval: int = 60  # seconds between steps
    success_threshold: float = 0.99  # 99% success rate required
    error_threshold: float = 0.01  # 1% error rate max
    min_requests: int = 100  # minimum requests before evaluation


@dataclass
class DeploymentVersion:
    """A deployment version."""
    version: str
    image: str
    replicas: int = 1
    weight: float = 0.0
    healthy: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""
    success: bool
    strategy: DeploymentStrategy
    old_version: str
    new_version: str
    duration_seconds: float
    rollback_performed: bool = False
    error: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)


class CanaryDeploymentManager:
    """Manages canary and blue-green deployments.
    
    Per RP-510:
    - Gradual traffic shifting
    - Automatic rollback
    - Health monitoring
    - Metrics collection
    """

    def __init__(
        self,
        config: CanaryConfig | None = None,
        health_checker: Callable[[str], bool] | None = None,
        metrics_collector: Callable[[str], dict[str, float]] | None = None,
    ):
        self.config = config or CanaryConfig()
        self.health_checker = health_checker or self._default_health_check
        self.metrics_collector = metrics_collector or self._default_metrics

        self._current_version: DeploymentVersion | None = None
        self._canary_version: DeploymentVersion | None = None
        self._deployments: dict[str, DeploymentResult] = {}

    def deploy_canary(
        self,
        new_version: str,
        new_image: str,
        current_version: str | None = None,
    ) -> DeploymentResult:
        """Deploy a new version using canary strategy.
        
        Args:
            new_version: New version identifier.
            new_image: New container image.
            current_version: Current version (optional).
            
        Returns:
            Deployment result.
        """
        start_time = time.time()
        old_version = current_version or (
            self._current_version.version if self._current_version else "none"
        )

        # Create canary version
        self._canary_version = DeploymentVersion(
            version=new_version,
            image=new_image,
            replicas=1,
            weight=self.config.initial_weight,
        )

        result = DeploymentResult(
            success=True,
            strategy=DeploymentStrategy.CANARY,
            old_version=old_version,
            new_version=new_version,
            duration_seconds=0,
        )

        # Simulate canary progression
        weight = self.config.initial_weight

        while weight < self.config.max_weight:
            # Check health
            if not self._check_canary_health():
                result.success = False
                result.rollback_performed = True
                result.error = "Canary health check failed"
                self._rollback_canary()
                break

            # Collect metrics
            metrics = self.metrics_collector(new_version)
            result.metrics[f"step_{int(weight*100)}"] = metrics

            # Check error rate
            error_rate = metrics.get("error_rate", 0)
            if error_rate > self.config.error_threshold:
                result.success = False
                result.rollback_performed = True
                result.error = f"Error rate {error_rate:.2%} exceeded threshold"
                self._rollback_canary()
                break

            # Increment weight
            weight = min(weight + self.config.increment, self.config.max_weight)
            self._canary_version.weight = weight

            # In production, wait for step_interval
            # time.sleep(self.config.step_interval)

        if result.success:
            # Promote canary to current
            self._current_version = self._canary_version
            self._canary_version = None

        result.duration_seconds = time.time() - start_time
        self._deployments[new_version] = result

        return result

    def deploy_blue_green(
        self,
        new_version: str,
        new_image: str,
    ) -> DeploymentResult:
        """Deploy using blue-green strategy.
        
        Args:
            new_version: New version identifier.
            new_image: New container image.
            
        Returns:
            Deployment result.
        """
        start_time = time.time()
        old_version = self._current_version.version if self._current_version else "none"

        # Create new (green) environment
        green = DeploymentVersion(
            version=new_version,
            image=new_image,
            replicas=self._current_version.replicas if self._current_version else 1,
            weight=0.0,
        )

        result = DeploymentResult(
            success=True,
            strategy=DeploymentStrategy.BLUE_GREEN,
            old_version=old_version,
            new_version=new_version,
            duration_seconds=0,
        )

        # Test green environment
        if not self.health_checker(new_version):
            result.success = False
            result.error = "Green environment health check failed"
            result.duration_seconds = time.time() - start_time
            return result

        # Switch traffic (atomic)
        green.weight = 1.0
        if self._current_version:
            self._current_version.weight = 0.0

        # Keep old version for quick rollback
        old = self._current_version
        self._current_version = green

        # In production, monitor and potentially rollback
        metrics = self.metrics_collector(new_version)
        result.metrics["post_switch"] = metrics

        if metrics.get("error_rate", 0) > self.config.error_threshold:
            # Rollback to old version
            if old:
                self._current_version = old
                old.weight = 1.0
                green.weight = 0.0
                result.success = False
                result.rollback_performed = True
                result.error = "Post-switch error rate too high"

        result.duration_seconds = time.time() - start_time
        self._deployments[new_version] = result

        return result

    def rollback(self, target_version: str | None = None) -> bool:
        """Rollback to a previous version.
        
        Args:
            target_version: Specific version to rollback to.
            
        Returns:
            True if rollback succeeded.
        """
        if self._canary_version:
            self._rollback_canary()
            return True

        # In production, restore previous deployment
        return False

    def get_current_version(self) -> str | None:
        """Get current deployed version."""
        return self._current_version.version if self._current_version else None

    def get_deployment_history(self) -> list[DeploymentResult]:
        """Get deployment history."""
        return list(self._deployments.values())

    def _check_canary_health(self) -> bool:
        """Check canary health."""
        if not self._canary_version:
            return False
        return self.health_checker(self._canary_version.version)

    def _rollback_canary(self) -> None:
        """Rollback canary deployment."""
        self._canary_version = None

    def _default_health_check(self, version: str) -> bool:
        """Default health check (always healthy)."""
        return True

    def _default_metrics(self, version: str) -> dict[str, float]:
        """Default metrics collector (mock data)."""
        return {
            "success_rate": 0.995 + random.uniform(0, 0.005),
            "error_rate": random.uniform(0, 0.005),
            "latency_p99": random.uniform(100, 200),
            "requests_per_second": random.uniform(100, 500),
        }


# Global manager
_deployment_manager: CanaryDeploymentManager | None = None


def get_deployment_manager() -> CanaryDeploymentManager:
    """Get global deployment manager."""
    global _deployment_manager
    if _deployment_manager is None:
        _deployment_manager = CanaryDeploymentManager()
    return _deployment_manager
