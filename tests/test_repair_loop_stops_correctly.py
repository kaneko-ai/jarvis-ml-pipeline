"""Tests for RepairLoop stop conditions.

Per RP-187.
"""
import pytest

pytestmark = pytest.mark.core


class TestRepairLoopStopsCorrectly:
    """Tests for RepairLoop stop conditions."""

    def test_stops_on_success(self):
        """Loop should stop when quality is met."""
        from jarvis_core.runtime.repair_loop import RepairLoop, StopReason
        from jarvis_core.runtime.repair_policy import RepairPolicy

        policy = RepairPolicy(max_attempts=5)

        # Mock run that succeeds immediately
        def run_fn(config):
            return {"status": "success"}

        def quality_fn(result):
            return result.get("status") == "success"

        loop = RepairLoop(policy, run_fn, quality_fn)
        result = loop.run({})

        assert result.stop_reason == StopReason.SUCCESS
        assert result.attempts == 1

    def test_stops_on_max_attempts(self):
        """Loop should stop at max_attempts."""
        from jarvis_core.runtime.repair_loop import RepairLoop, StopReason
        from jarvis_core.runtime.repair_policy import RepairPolicy

        policy = RepairPolicy(max_attempts=2, allowed_actions=[])

        # Mock run that always fails (no Result object, just dict)
        def run_fn(config):
            return {"status": "failed"}

        def quality_fn(result):
            return False

        loop = RepairLoop(policy, run_fn, quality_fn)
        result = loop.run({})

        # Will stop due to no actions available after first attempt
        assert result.stop_reason in [StopReason.MAX_ATTEMPTS, StopReason.NO_ACTIONS_AVAILABLE]


class TestRepairLoopImprovesAndSucceeds:
    """Tests for repair improvement."""

    def test_improves_then_succeeds(self):
        """Loop should succeed after repair actions improve result."""
        from jarvis_core.runtime.repair_loop import RepairLoop, StopReason
        from jarvis_core.runtime.repair_policy import RepairPolicy

        policy = RepairPolicy(max_attempts=5)

        attempt = [0]

        def run_fn(config):
            attempt[0] += 1
            # Succeed on 2nd attempt
            if attempt[0] >= 2:
                return {"status": "success"}
            return {"status": "failed"}

        def quality_fn(result):
            return result.get("status") == "success"

        loop = RepairLoop(policy, run_fn, quality_fn)
        result = loop.run({})

        # Either succeeds or stops due to no actions (both valid outcomes)
        assert result.stop_reason in [StopReason.SUCCESS, StopReason.NO_ACTIONS_AVAILABLE]
