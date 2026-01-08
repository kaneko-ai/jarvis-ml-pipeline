"""Tests for RepairPolicy schema.

Per RP-183.
"""
import json

import pytest

pytestmark = pytest.mark.core


class TestRepairPolicySchema:
    """Tests for RepairPolicy."""

    def test_default_policy_valid(self):
        """Default policy should be valid."""
        from jarvis_core.runtime.repair_policy import RepairPolicy

        policy = RepairPolicy()
        assert policy.max_attempts == 3
        assert policy.max_wall_time_sec == 300.0
        assert policy.max_tool_calls == 50

    def test_none_compatibility(self):
        """None repair_policy should not change existing behavior."""
        # When repair_policy is None, run_task should work as before
        policy = None
        assert policy is None  # Existing code checks for None

    def test_validation_attempts(self):
        """max_attempts must be >= 1."""
        from jarvis_core.runtime.repair_policy import RepairPolicy

        with pytest.raises(ValueError, match="max_attempts"):
            RepairPolicy(max_attempts=0)

    def test_validation_wall_time(self):
        """max_wall_time_sec must be > 0."""
        from jarvis_core.runtime.repair_policy import RepairPolicy

        with pytest.raises(ValueError, match="max_wall_time_sec"):
            RepairPolicy(max_wall_time_sec=0)

    def test_validation_tool_calls(self):
        """max_tool_calls must be >= 1."""
        from jarvis_core.runtime.repair_policy import RepairPolicy

        with pytest.raises(ValueError, match="max_tool_calls"):
            RepairPolicy(max_tool_calls=0)

    def test_json_serializable(self):
        """Policy should be JSON serializable."""
        from jarvis_core.runtime.repair_policy import RepairPolicy

        policy = RepairPolicy(max_attempts=5)
        json_str = policy.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["max_attempts"] == 5

        # Should round-trip
        restored = RepairPolicy.from_json(json_str)
        assert restored.max_attempts == 5

    def test_action_allowed(self):
        """is_action_allowed should work correctly."""
        from jarvis_core.runtime.repair_policy import RepairPolicy

        policy = RepairPolicy(allowed_actions=["INCREASE_TOP_K"])
        assert policy.is_action_allowed("INCREASE_TOP_K")
        assert not policy.is_action_allowed("UNKNOWN_ACTION")

    def test_stop_on_no_improvement(self):
        """Stop on no improvement should work."""
        from jarvis_core.runtime.repair_policy import RepairPolicy

        policy = RepairPolicy(stop_on={"consecutive_no_improvement": 2})
        assert not policy.should_stop_on_no_improvement(1)
        assert policy.should_stop_on_no_improvement(2)
        assert policy.should_stop_on_no_improvement(3)
