"""Tests for RepairPlanner priority.

Per RP-186.
"""
import pytest

pytestmark = pytest.mark.core


class TestRepairPlannerPriority:
    """Tests for RepairPlanner."""

    def test_fetch_failure_actions(self):
        """FETCH_PDF_FAILED should plan SWITCH_FETCH_ADAPTER first."""
        from jarvis_core.runtime.failure_signal import FailureSignal, FailureCode, FailureStage
        from jarvis_core.runtime.remediation.planner import RepairPlanner

        planner = RepairPlanner()

        signals = [FailureSignal(
            code=FailureCode.FETCH_PDF_FAILED,
            message="PDF not found",
            stage=FailureStage.FETCH,
        )]

        config = {"repair_policy": {"allowed_actions": [
            "SWITCH_FETCH_ADAPTER", "INCREASE_TOP_K"
        ]}}

        actions = planner.plan(signals, {}, config)

        assert len(actions) > 0
        assert actions[0] == "SWITCH_FETCH_ADAPTER"

    def test_citation_failure_actions(self):
        """CITATION_GATE_FAILED should plan in order."""
        from jarvis_core.runtime.failure_signal import FailureSignal, FailureCode, FailureStage
        from jarvis_core.runtime.remediation.planner import RepairPlanner

        planner = RepairPlanner()

        signals = [FailureSignal(
            code=FailureCode.CITATION_GATE_FAILED,
            message="Not enough citations",
            stage=FailureStage.VALIDATE,
        )]

        config = {"repair_policy": {"allowed_actions": [
            "INCREASE_TOP_K", "TIGHTEN_MMR", "CITATION_FIRST_PROMPT"
        ]}}

        actions = planner.plan(signals, {}, config)

        assert actions[0] == "INCREASE_TOP_K"

    def test_no_consecutive_same_action(self):
        """Same action should not be applied consecutively."""
        from jarvis_core.runtime.failure_signal import FailureSignal, FailureCode, FailureStage
        from jarvis_core.runtime.remediation.planner import RepairPlanner

        planner = RepairPlanner()

        signals = [FailureSignal(
            code=FailureCode.CITATION_GATE_FAILED,
            message="Not enough citations",
            stage=FailureStage.VALIDATE,
        )]

        # Action was just applied
        state = {"action_history": ["INCREASE_TOP_K"]}

        config = {"repair_policy": {"allowed_actions": [
            "INCREASE_TOP_K", "TIGHTEN_MMR"
        ]}}

        actions = planner.plan(signals, state, config)

        # Should skip INCREASE_TOP_K and go to next
        if actions:
            assert actions[0] != "INCREASE_TOP_K"

    def test_deterministic_output(self):
        """Same signals should always produce same actions."""
        from jarvis_core.runtime.failure_signal import FailureSignal, FailureCode, FailureStage
        from jarvis_core.runtime.remediation.planner import RepairPlanner

        planner = RepairPlanner()

        signals = [FailureSignal(
            code=FailureCode.MODEL_ERROR,
            message="API error",
            stage=FailureStage.GENERATE,
        )]

        config = {"repair_policy": {"allowed_actions": ["MODEL_ROUTER_SAFE_SWITCH"]}}

        actions1 = planner.plan(signals, {}, config)
        actions2 = planner.plan(signals, {}, config)

        assert actions1 == actions2
