"""Tests for RP-370+ evaluation features.

Core tests for eval.
"""

import pytest

pytestmark = pytest.mark.core


class TestABTesting:
    """Tests for RP-377 A/B Testing."""

    def test_create_experiment(self):
        """Should create experiment."""
        from jarvis_core.eval.ab_testing import ABTestingFramework

        ab = ABTestingFramework(experiments_dir="test_experiments")
        exp = ab.create_experiment(
            name="Test Experiment",
            variants=["control", "treatment"],
        )

        assert exp.experiment_id
        assert len(exp.variants) == 2

    def test_deterministic_assignment(self):
        """Assignment should be deterministic."""
        from jarvis_core.eval.ab_testing import ABTestingFramework

        ab = ABTestingFramework()
        exp = ab.create_experiment("Test", ["a", "b"])
        ab.start_experiment(exp.experiment_id)

        v1 = ab.assign_variant(exp.experiment_id, "user123")
        v2 = ab.assign_variant(exp.experiment_id, "user123")

        assert v1 == v2  # Same user, same variant


class TestAutoEval:
    """Tests for RP-370 Automated Eval."""

    def test_check_degradation(self):
        """Should detect degradation."""
        from jarvis_core.eval.auto_eval import AutomatedEvalPipeline

        pipeline = AutomatedEvalPipeline()

        current = {"success_rate": 0.50}  # Below 0.80 baseline
        alerts = pipeline.check_degradation(current)

        assert len(alerts) > 0
        assert any(a.metric == "success_rate" for a in alerts)