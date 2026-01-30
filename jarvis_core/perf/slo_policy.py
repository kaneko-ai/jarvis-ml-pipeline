"""SLO Policy.

Per V4-C02, this defines and enforces SLO constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SLOViolation(Enum):
    """Types of SLO violations."""

    TIME_EXCEEDED = "time_exceeded"
    COST_EXCEEDED = "cost_exceeded"
    MEMORY_EXCEEDED = "memory_exceeded"
    QUALITY_BELOW = "quality_below"


@dataclass
class SLOPolicy:
    """Service Level Objective policy."""

    # Time limits (seconds)
    max_time_quick: float = 60.0  # quick_plan max time
    max_time_deep: float = 600.0  # deep_plan max time

    # Cost limits (tokens)
    max_tokens_quick: int = 50000
    max_tokens_deep: int = 500000

    # Memory limits (MB)
    max_memory_mb: int = 2048

    # Quality thresholds
    min_fact_precision: float = 0.8
    max_unsupported_rate: float = 0.1

    # Action on violation
    downgrade_on_violation: bool = True

    def to_dict(self) -> dict:
        return {
            "max_time_quick": self.max_time_quick,
            "max_time_deep": self.max_time_deep,
            "max_tokens_quick": self.max_tokens_quick,
            "max_tokens_deep": self.max_tokens_deep,
            "max_memory_mb": self.max_memory_mb,
            "min_fact_precision": self.min_fact_precision,
            "max_unsupported_rate": self.max_unsupported_rate,
            "downgrade_on_violation": self.downgrade_on_violation,
        }


@dataclass
class SLOStatus:
    """Current SLO status."""

    elapsed_seconds: float = 0.0
    tokens_used: int = 0
    memory_mb: float = 0.0
    current_precision: float = 1.0
    current_unsupported_rate: float = 0.0
    violations: list = field(default_factory=list)

    def check(self, policy: SLOPolicy, mode: str = "quick") -> list:
        """Check for violations.

        Args:
            policy: SLO policy.
            mode: Execution mode (quick/deep).

        Returns:
            List of violations.
        """
        violations = []

        max_time = policy.max_time_quick if mode == "quick" else policy.max_time_deep
        max_tokens = policy.max_tokens_quick if mode == "quick" else policy.max_tokens_deep

        if self.elapsed_seconds > max_time:
            violations.append(SLOViolation.TIME_EXCEEDED)

        if self.tokens_used > max_tokens:
            violations.append(SLOViolation.COST_EXCEEDED)

        if self.memory_mb > policy.max_memory_mb:
            violations.append(SLOViolation.MEMORY_EXCEEDED)

        if self.current_precision < policy.min_fact_precision:
            violations.append(SLOViolation.QUALITY_BELOW)

        if self.current_unsupported_rate > policy.max_unsupported_rate:
            violations.append(SLOViolation.QUALITY_BELOW)

        self.violations = violations
        return violations


def check_slo(
    status: SLOStatus,
    policy: SLOPolicy = None,
    mode: str = "quick",
) -> tuple[bool, list]:
    """Check SLO status.

    Args:
        status: Current status.
        policy: SLO policy (uses default if None).
        mode: Execution mode.

    Returns:
        Tuple of (is_passing, violations).
    """
    policy = policy or SLOPolicy()
    violations = status.check(policy, mode)
    return len(violations) == 0, violations


def get_default_policy() -> SLOPolicy:
    """Get default SLO policy."""
    return SLOPolicy()


def should_downgrade(
    status: SLOStatus,
    policy: SLOPolicy,
    mode: str = "deep",
) -> tuple[bool, str]:
    """Check if we should downgrade from deep to quick.

    Args:
        status: Current status.
        policy: SLO policy.
        mode: Current mode.

    Returns:
        Tuple of (should_downgrade, reason).
    """
    if mode != "deep":
        return False, ""

    if not policy.downgrade_on_violation:
        return False, ""

    # Check if approaching limits
    time_ratio = status.elapsed_seconds / policy.max_time_deep
    token_ratio = status.tokens_used / policy.max_tokens_deep

    if time_ratio > 0.8:
        return True, "Approaching time limit"

    if token_ratio > 0.8:
        return True, "Approaching token limit"

    return False, ""
