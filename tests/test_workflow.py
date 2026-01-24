"""
JARVIS Workflow Tests

PDF知見統合: Workflow基盤のテスト
"""

from jarvis_core.evaluation.fitness import (
    FitnessGate,
    FitnessScore,
)
from jarvis_core.workflow.context_packager import (
    ContextPackager,
    LogEntry,
)
from jarvis_core.workflow.repeated_sampling import (
    RepeatedSampler,
)
from jarvis_core.workflow.runner import (
    StepStatus,
    WorkflowRunner,
    WorkflowState,
)
from jarvis_core.workflow.spec import (
    FitnessWeights,
    Mode,
    StepSpec,
    WorkflowSpec,
)
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


class TestWorkflowSpec:
    """WorkflowSpec tests."""

    def test_mode_enum(self):
        """Modeが正しく定義されていること."""
        assert Mode.STEP.value == "step"
        assert Mode.HITL.value == "hitl"
        assert Mode.DURABLE.value == "durable"

    def test_step_spec_from_dict(self):
        """StepSpecが辞書から生成できること."""
        data = {
            "step_id": "test_step",
            "action": "tool",
            "tool": "pubmed_search",
            "requires_approval": True,
        }
        step = StepSpec.from_dict(data)

        assert step.step_id == "test_step"
        assert step.action == "tool"
        assert step.tool == "pubmed_search"
        assert step.requires_approval is True

    def test_fitness_weights_default(self):
        """FitnessWeightsのデフォルト値が正しいこと."""
        weights = FitnessWeights()

        assert weights.correctness == 0.4
        assert weights.regression == 0.2
        assert weights.reproducibility == 0.2
        assert weights.cost == 0.1
        assert weights.latency == 0.1

    def test_workflow_spec_from_dict(self):
        """WorkflowSpecが辞書から生成できること."""
        data = {
            "workflow_id": "test_workflow",
            "mode": "step",
            "objective": "Test objective",
            "steps": [
                {"step_id": "step1", "action": "tool"},
            ],
        }
        spec = WorkflowSpec.from_dict(data)

        assert spec.workflow_id == "test_workflow"
        assert spec.mode == Mode.STEP
        assert len(spec.steps) == 1


class TestWorkflowRunner:
    """WorkflowRunner tests."""

    def test_run_simple_workflow(self):
        """シンプルなワークフローを実行できること."""
        spec = WorkflowSpec(
            workflow_id="test",
            mode=Mode.STEP,
            objective="Test",
            steps=[
                StepSpec(step_id="step1", action="tool"),
            ],
        )

        with TemporaryDirectory() as tmpdir:
            runner = WorkflowRunner(spec, logs_dir=tmpdir)
            state = runner.run()

            assert state.status == "completed"
            assert len(state.step_results) == 1
            assert state.step_results[0].status == StepStatus.COMPLETED

    def test_state_save_and_load(self):
        """状態を保存・読み込みできること."""
        with TemporaryDirectory() as tmpdir:
            state = WorkflowState(
                run_id="test123",
                workflow_id="test_wf",
                mode=Mode.STEP,
            )
            state.save(Path(tmpdir))

            loaded = WorkflowState.load(Path(tmpdir), "test123")

            assert loaded.run_id == "test123"
            assert loaded.workflow_id == "test_wf"


class TestContextPackager:
    """ContextPackager tests."""

    def test_add_log_and_get_bottom_k(self):
        """ログ追加と下位K%取得ができること."""
        packager = ContextPackager(bottom_k_percent=50)

        packager.add_log(LogEntry("run1", "step1", 0.9, "good"))
        packager.add_log(LogEntry("run2", "step1", 0.3, "bad"))
        packager.add_log(LogEntry("run3", "step1", 0.5, "medium"))
        packager.add_log(LogEntry("run4", "step1", 0.7, "ok"))

        bottom = packager.get_bottom_k_logs()

        # 下位50% = 2件（0.3, 0.5）
        assert len(bottom) == 2
        assert bottom[0].score == 0.3

    def test_detect_regression(self):
        """回帰検知ができること."""
        packager = ContextPackager()
        packager.add_log(LogEntry("run1", "step1", 0.9, "best"))

        assert packager.detect_regression(0.85) is True
        assert packager.detect_regression(0.95) is False


class TestRepeatedSampler:
    """RepeatedSampler tests."""

    def test_sample_best_selection(self):
        """ベスト選択ができること."""
        sampler = RepeatedSampler(n_samples=3)

        results = [0.3, 0.7, 0.5]
        idx = [0]

        def gen():
            val = results[idx[0]]
            idx[0] += 1
            return val

        def score(x):
            return x

        best = sampler.sample(gen, score)

        assert best is not None
        assert best.score == 0.7


class TestFitness:
    """Fitness tests."""

    def test_fitness_score_total(self):
        """総合スコアが計算できること."""
        score = FitnessScore(
            correctness=0.8,
            regression=0.0,
            reproducibility=0.9,
            cost=1.0,
            latency=10.0,
        )
        total = score.total()

        assert total > 0

    def test_fitness_gate_pass(self):
        """ゲートを通過できること."""
        gate = FitnessGate()
        score = FitnessScore(
            correctness=0.8,
            regression=0.0,
            reproducibility=0.9,
        )

        passed, failures = gate.check(score)

        assert passed is True
        assert len(failures) == 0

    def test_fitness_gate_fail(self):
        """ゲートで失敗すること."""
        gate = FitnessGate()
        score = FitnessScore(
            correctness=0.5,  # 0.7未満
            regression=0.2,  # 0.1超過
            reproducibility=0.7,  # 0.8未満
        )

        passed, failures = gate.check(score)

        assert passed is False
        assert len(failures) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
