"""
JARVIS Intelligence Tests

Phase 1-4: 知能密度向上のテスト
"""

from tempfile import TemporaryDirectory

import pytest

from jarvis_core.intelligence.action_planner import (
    ActionPlanner,
)
from jarvis_core.intelligence.decision import (
    DecisionMaker,
    DecisionStatus,
)

# Phase 2
from jarvis_core.intelligence.decision_item import (
    DecisionItem,
    DecisionPattern,
    DecisionStore,
)

# Phase 1
from jarvis_core.intelligence.evaluator_v2 import (
    AxisScore,
    EvaluationAxis,
    IntelligentEvaluator,
    ScoreBreakdown,
)

# Phase 3
from jarvis_core.intelligence.outcome_tracker import (
    OutcomeRecord,
    OutcomeStatus,
)

# Phase 4
from jarvis_core.intelligence.question_generator import (
    QuestionGenerator,
)


class TestPhase1Evaluator:
    """Phase 1: 5軸評価テスト."""

    def test_axis_score_valid(self):
        """有効なスコアが作成できること."""
        score = AxisScore(EvaluationAxis.RELEVANCE, 4, "High relevance")
        assert score.score == 4

    def test_axis_score_invalid(self):
        """無効なスコアでエラーになること."""
        with pytest.raises(ValueError):
            AxisScore(EvaluationAxis.RELEVANCE, 6, "Too high")

    def test_score_breakdown_total(self):
        """合計スコアが計算できること."""
        breakdown = ScoreBreakdown(
            relevance=AxisScore(EvaluationAxis.RELEVANCE, 4, ""),
            novelty=AxisScore(EvaluationAxis.NOVELTY, 3, ""),
            evidence=AxisScore(EvaluationAxis.EVIDENCE, 4, ""),
            effort=AxisScore(EvaluationAxis.EFFORT, 4, ""),
            risk=AxisScore(EvaluationAxis.RISK, 5, ""),
        )
        assert breakdown.total == 20
        assert breakdown.average == 4.0

    def test_evaluator(self):
        """評価器が動作すること."""
        evaluator = IntelligentEvaluator()
        breakdown = evaluator.evaluate("Test Evaluator", "Improve evaluation system")
        assert breakdown.total > 0


class TestPhase1Decision:
    """Phase 1: 判断テスト."""

    def test_decision_accept(self):
        """Accept判断ができること."""
        breakdown = ScoreBreakdown(
            relevance=AxisScore(EvaluationAxis.RELEVANCE, 5, ""),
            novelty=AxisScore(EvaluationAxis.NOVELTY, 4, ""),
            evidence=AxisScore(EvaluationAxis.EVIDENCE, 4, ""),
            effort=AxisScore(EvaluationAxis.EFFORT, 4, ""),
            risk=AxisScore(EvaluationAxis.RISK, 4, ""),
        )

        maker = DecisionMaker()
        decision = maker.decide("test1", "Test Item", breakdown)

        assert decision.status == DecisionStatus.ACCEPT

    def test_decision_reject(self):
        """Reject判断ができること."""
        breakdown = ScoreBreakdown(
            relevance=AxisScore(EvaluationAxis.RELEVANCE, 2, ""),  # Below threshold
            novelty=AxisScore(EvaluationAxis.NOVELTY, 4, ""),
            evidence=AxisScore(EvaluationAxis.EVIDENCE, 1, ""),  # Below threshold
            effort=AxisScore(EvaluationAxis.EFFORT, 4, ""),
            risk=AxisScore(EvaluationAxis.RISK, 4, ""),
        )

        maker = DecisionMaker()
        decision = maker.decide("test2", "Low Quality", breakdown)

        assert decision.status == DecisionStatus.REJECT
        assert decision.reject_reason is not None


class TestPhase2DecisionItem:
    """Phase 2: DecisionItem テスト."""

    def test_decision_store(self):
        """DecisionStoreが動作すること."""
        with TemporaryDirectory() as tmpdir:
            store = DecisionStore(storage_path=tmpdir)

            item = DecisionItem(
                decision_id="test_001",
                context="Test context",
                decision="accept",
                pattern=DecisionPattern.CORE_PRIORITY,
                reason="Test reason",
            )

            store.add(item)

            retrieved = store.get("test_001")
            assert retrieved is not None
            assert retrieved.context == "Test context"


class TestPhase3Outcome:
    """Phase 3: Outcome テスト."""

    def test_outcome_record(self):
        """OutcomeRecordが作成できること."""
        record = OutcomeRecord(
            decision_id="test_001",
            status=OutcomeStatus.SUCCESS,
            effect_description="効果あり",
            cost_justified=True,
            would_repeat=True,
        )

        assert record.status == OutcomeStatus.SUCCESS


class TestPhase4ActionPlan:
    """Phase 4: ActionPlanner テスト."""

    def test_action_planner(self):
        """ActionPlannerが動作すること."""
        planner = ActionPlanner()

        plan = planner.quick_plan(
            topic="Test Topic",
            top_papers=["Paper A", "Paper B"],
            implementation_ideas=["Idea 1"],
            low_priority=["Skip this"],
        )

        assert len(plan.read_items) == 2
        assert len(plan.build_items) == 1
        assert len(plan.ignore_items) == 1

    def test_question_generator(self):
        """QuestionGeneratorが動作すること."""
        generator = QuestionGenerator()
        questions = generator.generate("Test Topic")

        assert len(questions) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
