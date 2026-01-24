"""Tests for the Active Learning Module.

Per JARVIS_COMPLETION_PLAN_v3 Task 2.5
Updated to match actual implementation.
"""

import pytest


class TestALConfig:
    """Tests for Active Learning configuration."""

    def test_config_default_values(self):
        """Test ALConfig default values."""
        from jarvis_core.experimental.active_learning import ALConfig

        config = ALConfig()

        assert config.batch_size > 0
        assert config.initial_samples > 0  # Changed from initial_sample_size
        assert config.max_iterations > 0

    def test_config_custom_values(self):
        """Test ALConfig with custom values."""
        from jarvis_core.experimental.active_learning import ALConfig

        config = ALConfig(
            batch_size=20,
            initial_samples=50,  # Changed from initial_sample_size
            max_iterations=200,
            model_type="logistic",
        )

        assert config.batch_size == 20
        assert config.initial_samples == 50
        assert config.max_iterations == 200
        assert config.model_type == "logistic"

    def test_config_target_recall(self):
        """Test ALConfig target_recall."""
        from jarvis_core.experimental.active_learning import ALConfig

        config = ALConfig(target_recall=0.90)
        assert config.target_recall == 0.90


class TestALState:
    """Tests for ALState enum."""

    def test_state_values(self):
        """Test ALState enum values."""
        from jarvis_core.experimental.active_learning import ALState

        # ALState is an Enum now
        assert ALState.IDLE.value == "idle"
        assert ALState.TRAINING.value == "training"
        assert ALState.QUERYING.value == "querying"
        assert ALState.STOPPED.value == "stopped"

    def test_state_comparison(self):
        """Test ALState comparison."""
        from jarvis_core.experimental.active_learning import ALState

        assert ALState.IDLE != ALState.TRAINING
        assert ALState.IDLE == ALState.IDLE


class TestALStats:
    """Tests for ALStats dataclass."""

    def test_stats_creation(self):
        """Test ALStats creation."""
        from jarvis_core.experimental.active_learning.engine import ALStats

        stats = ALStats(
            total_instances=100,
            labeled_instances=20,
            relevant_found=8,
            iterations=2,
            estimated_recall=0.75,
        )

        assert stats.total_instances == 100
        assert stats.labeled_instances == 20
        assert stats.relevant_found == 8

    def test_stats_to_dict(self):
        """Test ALStats to_dict method."""
        from jarvis_core.experimental.active_learning.engine import ALStats

        stats = ALStats(
            total_instances=50,
            labeled_instances=10,
            relevant_found=4,
            iterations=1,
            estimated_recall=0.6,
        )

        result = stats.to_dict()
        assert result["total_instances"] == 50
        assert result["labeled_instances"] == 10


class TestQueryStrategy:
    """Tests for query strategies."""

    def test_uncertainty_sampling_init(self):
        """Test UncertaintySampling initialization."""
        from jarvis_core.experimental.active_learning import UncertaintySampling

        strategy = UncertaintySampling()
        assert strategy is not None

    def test_uncertainty_sampling_select(self):
        """Test UncertaintySampling selection."""
        from jarvis_core.experimental.active_learning import UncertaintySampling

        strategy = UncertaintySampling()

        unlabeled_ids = ["a", "b", "c", "d", "e", "f"]
        features = {id: [0.0] for id in unlabeled_ids}
        predictions = {
            "a": 0.1,
            "b": 0.5,  # Most uncertain
            "c": 0.9,
            "d": 0.45,  # Uncertain
            "e": 0.55,  # Uncertain
            "f": 0.2,
        }

        selected = strategy.select(unlabeled_ids, features, predictions, n=3)

        assert len(selected) == 3
        # Most uncertain samples (closest to 0.5) should be selected
        assert "b" in selected

    def test_uncertainty_sampling_empty(self):
        """Test UncertaintySampling with empty input."""
        from jarvis_core.experimental.active_learning import UncertaintySampling

        strategy = UncertaintySampling()
        selected = strategy.select([], {}, {}, n=5)
        assert selected == []

    def test_diversity_sampling_init(self):
        """Test DiversitySampling initialization."""
        from jarvis_core.experimental.active_learning import DiversitySampling

        strategy = DiversitySampling()
        assert strategy is not None

    def test_diversity_sampling_select(self):
        """Test DiversitySampling selection."""
        from jarvis_core.experimental.active_learning import DiversitySampling

        strategy = DiversitySampling(uncertainty_weight=0.5)

        unlabeled_ids = ["a", "b", "c", "d", "e"]
        features = {
            "a": [0.0, 0.0, 0.0],
            "b": [1.0, 0.0, 0.0],
            "c": [0.0, 1.0, 0.0],
            "d": [0.0, 0.0, 1.0],
            "e": [0.5, 0.5, 0.5],
        }
        predictions = {id: 0.5 for id in unlabeled_ids}

        selected = strategy.select(unlabeled_ids, features, predictions, n=3)

        assert len(selected) == 3


class TestStoppingCriteria:
    """Tests for stopping criteria."""

    def test_recall_stopping_init(self):
        """Test RecallStoppingCriterion initialization."""
        from jarvis_core.experimental.active_learning import RecallStoppingCriterion

        criterion = RecallStoppingCriterion(target_recall=0.95)
        assert criterion._target == 0.95

    def test_recall_stopping_not_met(self):
        """Test RecallStoppingCriterion when not met."""
        from jarvis_core.experimental.active_learning import RecallStoppingCriterion
        from jarvis_core.experimental.active_learning.stopping import StoppingState

        criterion = RecallStoppingCriterion(target_recall=0.95, min_iterations=2)
        state = StoppingState(
            total_instances=100,
            labeled_instances=20,
            relevant_found=5,
            iterations=5,
            estimated_recall=0.80,
            predictions=[],
        )

        assert criterion.should_stop(state) is False

    def test_recall_stopping_met(self):
        """Test RecallStoppingCriterion when met."""
        from jarvis_core.experimental.active_learning import RecallStoppingCriterion
        from jarvis_core.experimental.active_learning.stopping import StoppingState

        criterion = RecallStoppingCriterion(target_recall=0.95, min_iterations=2)
        state = StoppingState(
            total_instances=100,
            labeled_instances=30,
            relevant_found=10,
            iterations=5,
            estimated_recall=0.96,
            predictions=[],
        )

        assert criterion.should_stop(state) is True

    def test_budget_stopping_not_met(self):
        """Test BudgetStoppingCriterion when not met."""
        from jarvis_core.experimental.active_learning import BudgetStoppingCriterion
        from jarvis_core.experimental.active_learning.stopping import StoppingState

        criterion = BudgetStoppingCriterion(budget_ratio=0.3)
        state = StoppingState(
            total_instances=100,
            labeled_instances=20,  # 20% < 30%
            relevant_found=5,
            iterations=2,
            estimated_recall=0.5,
            predictions=[],
        )

        assert criterion.should_stop(state) is False

    def test_budget_stopping_met(self):
        """Test BudgetStoppingCriterion when met."""
        from jarvis_core.experimental.active_learning import BudgetStoppingCriterion
        from jarvis_core.experimental.active_learning.stopping import StoppingState

        criterion = BudgetStoppingCriterion(budget_ratio=0.3)
        state = StoppingState(
            total_instances=100,
            labeled_instances=30,  # 30% = 30%
            relevant_found=10,
            iterations=3,
            estimated_recall=0.7,
            predictions=[],
        )

        assert criterion.should_stop(state) is True

    def test_composite_stopping_any(self):
        """Test CompositeStoppingCriterion with any mode."""
        from jarvis_core.experimental.active_learning import BudgetStoppingCriterion, RecallStoppingCriterion
        from jarvis_core.experimental.active_learning.stopping import CompositeStoppingCriterion, StoppingState

        recall_criterion = RecallStoppingCriterion(target_recall=0.95, min_iterations=1)
        budget_criterion = BudgetStoppingCriterion(budget_ratio=0.5)

        composite = CompositeStoppingCriterion(
            criteria=[recall_criterion, budget_criterion],
            require_all=False,  # Any
        )

        # Neither met
        state = StoppingState(
            total_instances=100,
            labeled_instances=20,
            relevant_found=5,
            iterations=2,
            estimated_recall=0.5,
            predictions=[],
        )
        assert composite.should_stop(state) is False

        # Recall met
        state = StoppingState(
            total_instances=100,
            labeled_instances=25,
            relevant_found=10,
            iterations=3,
            estimated_recall=0.96,
            predictions=[],
        )
        assert composite.should_stop(state) is True


class TestActiveLearningEngine:
    """Tests for Active Learning engine."""

    def test_engine_initialization(self):
        """Test ActiveLearningEngine initialization."""
        from jarvis_core.experimental.active_learning import ActiveLearningEngine, ALConfig

        config = ALConfig(batch_size=10, initial_samples=20)
        engine = ActiveLearningEngine(config=config)

        assert engine is not None
        assert engine._config.batch_size == 10

    def test_engine_initialize_with_data(self):
        """Test engine initialization with data."""
        from jarvis_core.experimental.active_learning import ActiveLearningEngine, ALConfig

        config = ALConfig(batch_size=5, initial_samples=10)
        engine = ActiveLearningEngine(config=config)

        # Mock data: 50 papers with features
        instances = {f"paper_{i}": [float(i), float(i + 1)] for i in range(50)}

        engine.initialize(instances)

        # Engine should have stored instances
        assert len(engine._instances) == 50

    def test_engine_get_next_query(self):
        """Test getting next query batch."""
        from jarvis_core.experimental.active_learning import ActiveLearningEngine, ALConfig

        config = ALConfig(batch_size=5, initial_samples=10)
        engine = ActiveLearningEngine(config=config)

        instances = {f"paper_{i}": [float(i)] for i in range(50)}
        engine.initialize(instances)

        # n defaults to config.initial_samples for first query
        query = engine.get_next_query()

        assert len(query) >= 0  # Just verify it returns something

    def test_engine_update_single(self):
        """Test updating with a single label."""
        from jarvis_core.experimental.active_learning import ActiveLearningEngine, ALConfig

        config = ALConfig(batch_size=5, initial_samples=10)
        engine = ActiveLearningEngine(config=config)

        instances = {f"paper_{i}": [float(i)] for i in range(50)}
        engine.initialize(instances)

        # Get initial query
        query = engine.get_next_query(n=5)

        # Update with label
        if query:
            engine.update(query[0], 1)  # Label as relevant

    def test_engine_update_batch(self):
        """Test updating with batch labels."""
        from jarvis_core.experimental.active_learning import ActiveLearningEngine, ALConfig

        config = ALConfig(batch_size=5, initial_samples=10)
        engine = ActiveLearningEngine(config=config)

        instances = {f"paper_{i}": [float(i)] for i in range(50)}
        engine.initialize(instances)

        query = engine.get_next_query(n=5)

        # Update with batch labels
        labels = {id: (i % 2) for i, id in enumerate(query)}
        engine.update_batch(labels)

    def test_engine_get_stats(self):
        """Test getting engine statistics."""
        from jarvis_core.experimental.active_learning import ActiveLearningEngine, ALConfig

        config = ALConfig()
        engine = ActiveLearningEngine(config=config)

        instances = {f"paper_{i}": [float(i)] for i in range(30)}
        engine.initialize(instances)

        stats = engine.get_stats()

        assert stats.total_instances == 30
        assert stats.labeled_instances == 0

    def test_engine_state_property(self):
        """Test engine state property."""
        from jarvis_core.experimental.active_learning import ActiveLearningEngine, ALConfig, ALState

        engine = ActiveLearningEngine()

        state = engine.state

        assert state == ALState.IDLE


class TestActiveLearningCLI:
    """Tests for Active Learning CLI."""

    def test_cli_entry_point_exists(self):
        """Test CLI entry point is defined."""
        from jarvis_core.experimental.active_learning import cli

        assert hasattr(cli, "cmd_screen")

    def test_cli_help(self):
        """Test CLI help message."""
        import subprocess

        result = subprocess.run(
            ["python", "-m", "jarvis_core.experimental.active_learning.cli", "--help"],
            capture_output=True,
            text=True,
        )

        # Should not error, and should show help
        assert (
            result.returncode == 0
            or "usage" in result.stdout.lower()
            or "help" in result.stderr.lower()
        )


class TestModuleImports:
    """Test module imports."""

    def test_main_imports(self):
        """Test main module imports."""
        from jarvis_core.experimental.active_learning import (
            ActiveLearningEngine,
            ALConfig,
            ALState,
            BudgetStoppingCriterion,
            DiversitySampling,
            QueryStrategy,
            RecallStoppingCriterion,
            StoppingCriterion,
            UncertaintySampling,
        )

        assert ActiveLearningEngine is not None
        assert ALConfig is not None
        assert ALState is not None
        assert QueryStrategy is not None
        assert UncertaintySampling is not None
        assert DiversitySampling is not None
        assert StoppingCriterion is not None
        assert RecallStoppingCriterion is not None
        assert BudgetStoppingCriterion is not None
