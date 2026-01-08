"""
JARVIS Budget Policy Tests
"""

from jarvis_core.budget import (
    BudgetPolicy,
    BudgetSpec,
    BudgetTracker,
)
import pytest


class TestBudgetSpec:
    """BudgetSpec tests."""

    def test_default_values(self):
        """デフォルト値が正しいこと."""
        spec = BudgetSpec()
        assert spec.mode == "standard"
        assert spec.max_tool_calls == 30
        assert spec.max_retries == 2

    def test_from_config(self):
        """設定から生成できること."""
        config = {
            "budget": {
                "mode": "fast",
                "max_tool_calls": 10,
            }
        }
        spec = BudgetSpec.from_config(config)
        assert spec.mode == "fast"
        assert spec.max_tool_calls == 10

    def test_fast_preset(self):
        """fastプリセットが正しいこと."""
        spec = BudgetSpec.fast()
        assert spec.mode == "fast"
        assert spec.max_tool_calls == 10
        assert spec.max_search_results == 3

    def test_high_preset(self):
        """highプリセットが正しいこと."""
        spec = BudgetSpec.high()
        assert spec.mode == "high"
        assert spec.max_tool_calls == 50
        assert spec.max_search_results == 20

class TestBudgetTracker:
    """BudgetTracker tests."""

    def test_record_tool_call(self):
        """ツール呼び出しを記録できること."""
        tracker = BudgetTracker()
        tracker.record_tool_call(3)
        assert tracker.tool_calls_used == 3
        assert len(tracker.events) == 1

    def test_can_call_tool(self):
        """ツール呼び出し可否を判定できること."""
        spec = BudgetSpec(max_tool_calls=5)
        tracker = BudgetTracker(tool_calls_used=4)

        assert tracker.can_call_tool(spec, 1) is True
        assert tracker.can_call_tool(spec, 2) is False

    def test_record_degrade(self):
        """degrade状態を記録できること."""
        tracker = BudgetTracker()
        tracker.record_degrade("budget_low")

        assert tracker.degraded is True
        assert "budget_low" in tracker.degrade_reasons

class TestBudgetPolicy:
    """BudgetPolicy tests."""

    def test_fast_mode_decision(self):
        """fastモードの決定が正しいこと."""
        policy = BudgetPolicy()
        spec = BudgetSpec.fast()
        tracker = BudgetTracker()

        decision = policy.decide(spec, tracker)

        assert decision.should_search is True
        assert decision.num_results <= 3
        assert decision.summary_depth == 1

    def test_high_mode_decision(self):
        """highモードの決定が正しいこと."""
        policy = BudgetPolicy()
        spec = BudgetSpec.high()
        tracker = BudgetTracker()

        decision = policy.decide(spec, tracker)

        assert decision.should_search is True
        assert decision.num_results == spec.max_search_results
        assert decision.summary_depth == spec.max_summary_depth

    def test_budget_exhausted(self):
        """予算超過時に検索不可になること."""
        policy = BudgetPolicy()
        spec = BudgetSpec(max_tool_calls=10)
        tracker = BudgetTracker(tool_calls_used=10)

        decision = policy.decide(spec, tracker)

        assert decision.should_search is False
        assert decision.num_results == 0
        assert decision.allow_retry is False
        assert decision.degrade_reason is not None

    def test_retry_exhausted(self):
        """リトライ超過時にallow_retryがFalseになること."""
        policy = BudgetPolicy()
        spec = BudgetSpec(max_retries=2)
        tracker = BudgetTracker(retries_used=2)

        decision = policy.decide(spec, tracker)

        assert decision.allow_retry is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
