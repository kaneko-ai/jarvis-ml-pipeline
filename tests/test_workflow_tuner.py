"""Tests for workflow tuner module."""

from unittest.mock import MagicMock, patch

import pytest
from jarvis_core.workflow.tuner import WorkflowTuner
from jarvis_core.workflow.spec import WorkflowSpec, Budgets, FitnessWeights, Mode


@pytest.fixture
def mock_spec():
    budgets = Budgets(max_iters=5, n_samples=2, max_cost=10.0)
    weights = FitnessWeights(
        correctness=0.5, regression=0.2, reproducibility=0.1, cost=0.1, latency=0.1
    )
    return WorkflowSpec(
        workflow_id="test_workflow",
        mode=Mode.STEP,
        objective="Test objective",
        steps=[],
        budgets=budgets,
        fitness=weights,
    )


class TestWorkflowTuner:
    def test_init(self, mock_spec, tmp_path):
        tuner = WorkflowTuner(mock_spec, logs_dir=str(tmp_path))
        assert tuner.spec == mock_spec
        assert tuner.logs_dir == tmp_path
        # Goldset warning check could be done with caplog if needed

    def test_calculate_fitness(self, mock_spec):
        tuner = WorkflowTuner(mock_spec)

        scores = {
            "correctness": 1.0,  # 0.5 * 1.0 = 0.5
            "regression": 0.0,  # 0.2 * (1 - 0) = 0.2
            "reproducibility": 1.0,  # 0.1 * 1.0 = 0.1
            "cost": 5.0,  # 0.1 * (1 - 0.5) = 0.05
            "latency": 50.0,  # 0.1 * (1 - 0.5) = 0.05
        }
        # Total: 0.5 + 0.2 + 0.1 + 0.05 + 0.05 = 0.9

        fitness = tuner._calculate_fitness(scores)
        assert fitness == pytest.approx(0.9)

    @patch("jarvis_core.workflow.tuner.WorkflowRunner")
    def test_tune_convergence(self, mock_runner_cls, mock_spec, tmp_path):
        tuner = WorkflowTuner(mock_spec, logs_dir=str(tmp_path))

        # Mock generator and evaluator
        generator = MagicMock(return_value=mock_spec)

        # Evaluator returns high scores
        evaluator = MagicMock(
            return_value={
                "correctness": 1.0,
                "regression": 0.0,
                "reproducibility": 1.0,
                "cost": 0.0,
                "latency": 0.0,
            }
        )

        # Mock runner instance
        mock_runner = MagicMock()
        mock_runner.run.return_value = MagicMock()  # WorkflowState
        mock_runner_cls.return_value = mock_runner

        # Increase threshold to force loop if scores weren't perfect,
        # but here scores are perfect (1.0) so it should hit threshold (0.8)
        result = tuner.tune(generator, evaluator, fitness_threshold=0.8)

        assert result.converged is True
        assert result.reason == "threshold_reached"
        assert result.final_fitness > 0.8
        assert len(result.iterations) == 1  # converged immediately

    @patch("jarvis_core.workflow.tuner.WorkflowRunner")
    def test_tune_budget_exceeded(self, mock_runner_cls, mock_spec, tmp_path):
        # Set max cost low
        mock_spec.budgets.max_cost = 1.0
        tuner = WorkflowTuner(mock_spec, logs_dir=str(tmp_path))

        generator = MagicMock(return_value=mock_spec)

        # Evaluator returns low scores
        evaluator = MagicMock(return_value={"correctness": 0.0, "cost": 10.0})  # High cost

        mock_runner = MagicMock()
        mock_runner.run.return_value = MagicMock()
        mock_runner_cls.return_value = mock_runner

        # Mock sampler to track cost
        # Since WorkflowTuner uses RepeatedSampler, we need to ensure sample consumption
        # updates the cost. But WorkflowRunner mock just returns.
        # However, tuner._sample_and_evaluate calls sampler.sample.
        # sampler.sample runs tasks and updates cost.
        # evaluator's return value is passed to _calculate_fitness,
        # but cost accumulation logic is inside RepeatedSampler which we are using real instance of.
        # RepeatedSampler uses the cost returned by the score function? No.
        # Let's check RepeatedSampler implementation or just mock it.
        # Actually Tuner instantiated RepeatedSampler.

        # Simulating cost increase via side_effect on sampler.sample is tricky because it's a real object.
        # Let's manually set cost on the sampler after first iteration effectively.
        # But we can't easily interrupt the loop.

        # Alternative: Mock self.sampler
        tuner.sampler = MagicMock()
        tuner.sampler.total_cost = 0.0  # Initialize as float

        # Let's mock _sample_and_evaluate to consume cost
        with patch.object(tuner, "_sample_and_evaluate") as mock_sample:
            mock_result = MagicMock()
            mock_result.output = {"scores": {"correctness": 0.1}}
            mock_sample.return_value = mock_result

            # Side effect to increase cost
            def side_effect(*args, **kwargs):
                tuner.sampler.total_cost += 5.0
                return mock_result

            mock_sample.side_effect = side_effect

            result = tuner.tune(generator, evaluator)

            assert result.reason == "budget_exceeded"
            assert result.converged is False

    @patch("jarvis_core.workflow.tuner.WorkflowRunner")
    def test_tune_max_iters(self, mock_runner_cls, mock_spec, tmp_path):
        tuner = WorkflowTuner(mock_spec, logs_dir=str(tmp_path))

        generator = MagicMock(return_value=mock_spec)
        evaluator = MagicMock(return_value={"correctness": 0.5})  # Not enough to pass threshold

        mock_runner = MagicMock()
        mock_runner_cls.return_value = mock_runner

        result = tuner.tune(generator, evaluator, fitness_threshold=0.9)

        assert result.reason == "max_iters"
        assert len(result.iterations) == mock_spec.budgets.max_iters

    def test_prepare_context(self, mock_spec):
        tuner = WorkflowTuner(mock_spec)
        tuner._best_fitness = 0.5
        tuner._prev_best_scores = {"acc": 0.5}

        context = tuner._prepare_context()
        # ContextPackager returns keys like 'bottom_logs', 'score_diffs', etc.
        assert "score_diffs" in context or "bottom_logs" in context
        # Check if context packager logic is invoked
