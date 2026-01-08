"""RepairPolicy.

Per RP-183, defines the contract for automatic repair loop behavior.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RepairPolicy:
    """Policy for automatic repair loop.

    All fields have safe defaults. None or 0 values are not allowed
    for critical limits (per RP-192 Kill Switch requirement).
    """

    max_attempts: int = 3
    max_wall_time_sec: float = 300.0
    max_tool_calls: int = 50
    allowed_actions: list[str] = field(default_factory=lambda: [
        "SWITCH_FETCH_ADAPTER",
        "INCREASE_TOP_K",
        "TIGHTEN_MMR",
        "CITATION_FIRST_PROMPT",
        "BUDGET_REBALANCE",
        "MODEL_ROUTER_SAFE_SWITCH",
    ])
    stop_on: dict[str, Any] = field(default_factory=lambda: {
        "consecutive_no_improvement": 2,
        "same_failure_repeated": 3,
    })
    budget_overrides: dict[str, Any] | None = None

    def __post_init__(self):
        """Validate policy after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate policy values.

        Raises:
            ValueError: If any value is invalid.
        """
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")

        if self.max_wall_time_sec <= 0:
            raise ValueError("max_wall_time_sec must be > 0")

        if self.max_tool_calls < 1:
            raise ValueError("max_tool_calls must be >= 1")

        if not isinstance(self.allowed_actions, list):
            raise ValueError("allowed_actions must be a list")

        if not isinstance(self.stop_on, dict):
            raise ValueError("stop_on must be a dict")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RepairPolicy:
        """Create from dictionary."""
        return cls(
            max_attempts=data.get("max_attempts", 3),
            max_wall_time_sec=data.get("max_wall_time_sec", 300.0),
            max_tool_calls=data.get("max_tool_calls", 50),
            allowed_actions=data.get("allowed_actions", []),
            stop_on=data.get("stop_on", {}),
            budget_overrides=data.get("budget_overrides"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> RepairPolicy:
        """Deserialize from JSON."""
        return cls.from_dict(json.loads(json_str))

    def is_action_allowed(self, action_id: str) -> bool:
        """Check if an action is allowed by this policy."""
        return action_id in self.allowed_actions

    def should_stop_on_no_improvement(self, consecutive_count: int) -> bool:
        """Check if should stop due to no improvement."""
        threshold = self.stop_on.get("consecutive_no_improvement", 2)
        return consecutive_count >= threshold

    def should_stop_on_repeated_failure(self, repeat_count: int) -> bool:
        """Check if should stop due to repeated same failure."""
        threshold = self.stop_on.get("same_failure_repeated", 3)
        return repeat_count >= threshold


# Default safe policy
DEFAULT_REPAIR_POLICY = RepairPolicy(
    max_attempts=3,
    max_wall_time_sec=300.0,
    max_tool_calls=50,
)
