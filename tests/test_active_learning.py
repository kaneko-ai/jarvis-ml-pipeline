"""Tests for the Active Learning Module.

Per JARVIS_COMPLETION_PLAN_v3 Task 2.5
"""

import numpy as np
import pytest


class TestALConfig:
    """Tests for Active Learning configuration."""

    def test_config_default_values(self):
        """Test ALConfig default values."""
        from jarvis_core.active_learning import ALConfig

        config = ALConfig()

        assert config.batch_size > 0
        assert config.initial_sample_size > 0
        assert 0.0 <= config.uncertainty_threshold <= 1.0

    def test_config_custom_values(self):
        """Test ALConfig with custom values."""
        from jarvis_core.active_learning import ALConfig

        config = ALConfig(
            batch_size=20,
            initial_sample_size=50,
            uncertainty_threshold=0.6,
            model_type="lightgbm",
        )

        assert config.batch_size == 20
        assert config.initial_sample_size == 50
        assert config.uncertainty_threshold == 0.6
        assert config.model_type == "lightgbm"

    def test_config_validation(self):
        """Test ALConfig validation."""
        from jarvis_core.active_learning import ALConfig

        # Invalid batch_size should raise or be handled
        with pytest.raises((ValueError, AssertionError)):
            ALConfig(batch_size=0)

        with pytest.raises((ValueError, AssertionError)):
            ALConfig(batch_size=-1)

    def test_config_to_dict(self):
        """Test ALConfig serialization."""
        from jarvis_core.active_learning import ALConfig

        config = ALConfig(batch_size=15, initial_sample_size=30)
        result = config.to_dict()

        assert result["batch_size"] == 15
        assert result["initial_sample_size"] == 30


class TestALState:
    """Tests for Active Learning state management."""

    def test_state_initialization(self):
        """Test ALState initialization."""
        from jarvis_core.active_learning import ALState

        state = ALState()

        assert state.iteration == 0
        assert state.labeled_count == 0
        assert state.unlabeled_count == 0
        assert len(state.labeled_indices) == 0

    def test_state_update(self):
        """Test ALState update after labeling."""
        from jarvis_core.active_learning import ALState

        state = ALState(unlabeled_count=100)

        state.add_labeled([0, 1, 2, 3, 4])

        assert state.labeled_count == 5
        assert state.unlabeled_count == 95
        assert state.iteration == 1
        assert set(state.labeled_indices) == {0, 1, 2, 3, 4}

    def test_state_metrics_tracking(self):
        """Test ALState metrics tracking."""
        from jarvis_core.active_learning import ALState

        state = ALState()

        state.record_metrics(
            iteration=1,
            precision=0.85,
            recall=0.90,
            f1=0.87,
        )

        assert len(state.metrics_history) == 1
        assert state.metrics_history[0]["precision"] == 0.85

    def test_state_serialization(self):
        """Test ALState serialization and deserialization."""
        from jarvis_core.active_learning import ALState

        state = ALState(unlabeled_count=50)
        state.add_labeled([1, 2, 3])
        state.record_metrics(iteration=1, precision=0.8, recall=0.9, f1=0.85)

        state_dict = state.to_dict()
        restored = ALState.from_dict(state_dict)

        assert restored.labeled_count == state.labeled_count
        assert restored.iteration == state.iteration
        assert len(restored.metrics_history) == 1


class TestQueryStrategy:
    """Tests for query strategies."""

    def test_uncertainty_sampling_init(self):
        """Test UncertaintySampling initialization."""
        from jarvis_core.active_learning import UncertaintySampling

        strategy = UncertaintySampling()
        assert strategy is not None

    def test_uncertainty_sampling_select(self):
        """Test UncertaintySampling selection."""
        from jarvis_core.active_learning import UncertaintySampling

        strategy = UncertaintySampling()

        # Mock probabilities: higher uncertainty = closer to 0.5
        probabilities = np.array([0.1, 0.5, 0.9, 0.45, 0.55, 0.2])

        selected = strategy.select(probabilities, n=3)

        assert len(selected) == 3
        # Most uncertain samples (closest to 0.5) should be selected
        assert 1 in selected  # prob = 0.5
        assert 3 in selected  # prob = 0.45
        assert 4 in selected  # prob = 0.55

    def test_uncertainty_sampling_with_mask(self):
        """Test UncertaintySampling with already labeled mask."""
        from jarvis_core.active_learning import UncertaintySampling

        strategy = UncertaintySampling()

        probabilities = np.array([0.5, 0.5, 0.5, 0.5])
        already_labeled = {0, 2}  # indices 0 and 2 are already labeled

        selected = strategy.select(probabilities, n=2, exclude=already_labeled)

        assert len(selected) == 2
        assert 0 not in selected
        assert 2 not in selected

    def test_diversity_sampling_init(self):
        """Test DiversitySampling initialization."""
        from jarvis_core.active_learning import DiversitySampling

        strategy = DiversitySampling()
        assert strategy is not None

    def test_diversity_sampling_select(self):
        """Test DiversitySampling selection."""
        from jarvis_core.active_learning import DiversitySampling

        strategy = DiversitySampling()

        # Mock embeddings: 5 samples with 3 features
        embeddings = np.array(
            [
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
                [0.5, 0.5, 0.5],
            ]
        )

        selected = strategy.select(embeddings, n=3)

        assert len(selected) == 3
        # Should select diverse samples (far apart in embedding space)

    def test_hybrid_strategy(self):
        """Test hybrid uncertainty + diversity strategy."""
        from jarvis_core.active_learning.query import HybridStrategy

        strategy = HybridStrategy(
            uncertainty_weight=0.7,
            diversity_weight=0.3,
        )

        probabilities = np.array([0.5, 0.3, 0.7, 0.45])
        embeddings = np.array(
            [
                [0.0, 0.0],
                [1.0, 0.0],
                [0.0, 1.0],
                [1.0, 1.0],
            ]
        )

        selected = strategy.select(
            probabilities=probabilities,
            embeddings=embeddings,
            n=2,
        )

        assert len(selected) == 2


class TestStoppingCriterion:
    """Tests for stopping criteria."""

    def test_recall_stopping_init(self):
        """Test RecallStoppingCriterion initialization."""
        from jarvis_core.active_learning import RecallStoppingCriterion

        criterion = RecallStoppingCriterion(target_recall=0.95)
        assert criterion.target_recall == 0.95

    def test_recall_stopping_not_met(self):
        """Test RecallStoppingCriterion when not met."""
        from jarvis_core.active_learning import ALState, RecallStoppingCriterion

        criterion = RecallStoppingCriterion(target_recall=0.95)
        state = ALState()
        state.record_metrics(iteration=1, recall=0.80)

        assert criterion.should_stop(state) == False

    def test_recall_stopping_met(self):
        """Test RecallStoppingCriterion when met."""
        from jarvis_core.active_learning import ALState, RecallStoppingCriterion

        criterion = RecallStoppingCriterion(target_recall=0.95)
        state = ALState()
        state.record_metrics(iteration=1, recall=0.96)

        assert criterion.should_stop(state) == True

    def test_budget_stopping_init(self):
        """Test BudgetStoppingCriterion initialization."""
        from jarvis_core.active_learning import BudgetStoppingCriterion

        criterion = BudgetStoppingCriterion(max_labels=100)
        assert criterion.max_labels == 100

    def test_budget_stopping_not_met(self):
        """Test BudgetStoppingCriterion when not met."""
        from jarvis_core.active_learning import ALState, BudgetStoppingCriterion

        criterion = BudgetStoppingCriterion(max_labels=100)
        state = ALState()
        state._labeled_count = 50

        assert criterion.should_stop(state) == False

    def test_budget_stopping_met(self):
        """Test BudgetStoppingCriterion when met."""
        from jarvis_core.active_learning import ALState, BudgetStoppingCriterion

        criterion = BudgetStoppingCriterion(max_labels=100)
        state = ALState()
        state._labeled_count = 100

        assert criterion.should_stop(state) == True

    def test_combined_stopping_criteria(self):
        """Test combining multiple stopping criteria."""
        from jarvis_core.active_learning import (
            ALState,
            BudgetStoppingCriterion,
            RecallStoppingCriterion,
        )
        from jarvis_core.active_learning.stopping import CombinedStoppingCriterion

        recall_criterion = RecallStoppingCriterion(target_recall=0.95)
        budget_criterion = BudgetStoppingCriterion(max_labels=100)

        combined = CombinedStoppingCriterion(
            criteria=[recall_criterion, budget_criterion],
            mode="any",  # Stop if ANY criterion is met
        )

        state = ALState()
        state._labeled_count = 50
        state.record_metrics(iteration=1, recall=0.80)

        assert combined.should_stop(state) == False

        state.record_metrics(iteration=2, recall=0.96)
        assert combined.should_stop(state) == True


class TestActiveLearningEngine:
    """Tests for Active Learning engine."""

    def test_engine_initialization(self):
        """Test ActiveLearningEngine initialization."""
        from jarvis_core.active_learning import ActiveLearningEngine, ALConfig

        config = ALConfig(batch_size=10, initial_sample_size=20)
        engine = ActiveLearningEngine(config=config)

        assert engine is not None
        assert engine.config.batch_size == 10

    def test_engine_initialize_with_data(self):
        """Test engine initialization with data."""
        from jarvis_core.active_learning import ActiveLearningEngine, ALConfig

        config = ALConfig(batch_size=5, initial_sample_size=10)
        engine = ActiveLearningEngine(config=config)

        # Mock data: 100 papers with embeddings
        embeddings = np.random.rand(100, 128)
        paper_ids = [f"paper_{i}" for i in range(100)]

        engine.initialize(embeddings=embeddings, paper_ids=paper_ids)

        assert engine.state.unlabeled_count == 100
        assert len(engine.paper_ids) == 100

    def test_engine_get_initial_batch(self):
        """Test getting initial batch for labeling."""
        from jarvis_core.active_learning import ActiveLearningEngine, ALConfig

        config = ALConfig(batch_size=5, initial_sample_size=10)
        engine = ActiveLearningEngine(config=config)

        embeddings = np.random.rand(50, 64)
        paper_ids = [f"paper_{i}" for i in range(50)]
        engine.initialize(embeddings=embeddings, paper_ids=paper_ids)

        initial_batch = engine.get_initial_batch()

        assert len(initial_batch) == 10  # initial_sample_size
        assert all(pid in paper_ids for pid in initial_batch)

    def test_engine_update_labels(self):
        """Test updating labels."""
        from jarvis_core.active_learning import ActiveLearningEngine, ALConfig

        config = ALConfig(batch_size=5, initial_sample_size=10)
        engine = ActiveLearningEngine(config=config)

        embeddings = np.random.rand(50, 64)
        paper_ids = [f"paper_{i}" for i in range(50)]
        engine.initialize(embeddings=embeddings, paper_ids=paper_ids)

        initial_batch = engine.get_initial_batch()

        # Simulate labeling: 3 relevant, 7 not relevant
        labels = {pid: (i < 3) for i, pid in enumerate(initial_batch)}

        engine.update_labels(labels)

        assert engine.state.labeled_count == 10
        assert engine.state.iteration == 1

    def test_engine_get_next_batch(self):
        """Test getting next batch using active learning."""
        from jarvis_core.active_learning import ActiveLearningEngine, ALConfig

        config = ALConfig(batch_size=5, initial_sample_size=10)
        engine = ActiveLearningEngine(config=config)

        embeddings = np.random.rand(50, 64)
        paper_ids = [f"paper_{i}" for i in range(50)]
        engine.initialize(embeddings=embeddings, paper_ids=paper_ids)

        # Initial labeling
        initial_batch = engine.get_initial_batch()
        labels = {pid: (i % 2 == 0) for i, pid in enumerate(initial_batch)}
        engine.update_labels(labels)

        # Get next batch
        next_batch = engine.get_next_batch()

        assert len(next_batch) == 5  # batch_size
        assert all(pid not in initial_batch for pid in next_batch)

    def test_engine_train_model(self):
        """Test model training."""
        from jarvis_core.active_learning import ActiveLearningEngine, ALConfig

        config = ALConfig(batch_size=5, initial_sample_size=20, model_type="lightgbm")
        engine = ActiveLearningEngine(config=config)

        embeddings = np.random.rand(100, 64)
        paper_ids = [f"paper_{i}" for i in range(100)]
        engine.initialize(embeddings=embeddings, paper_ids=paper_ids)

        # Initial labeling
        initial_batch = engine.get_initial_batch()
        labels = {pid: (i % 3 == 0) for i, pid in enumerate(initial_batch)}
        engine.update_labels(labels)

        # Model should be trained
        assert engine.model is not None

    def test_engine_predict_relevance(self):
        """Test relevance prediction."""
        from jarvis_core.active_learning import ActiveLearningEngine, ALConfig

        config = ALConfig(batch_size=5, initial_sample_size=20)
        engine = ActiveLearningEngine(config=config)

        embeddings = np.random.rand(100, 64)
        paper_ids = [f"paper_{i}" for i in range(100)]
        engine.initialize(embeddings=embeddings, paper_ids=paper_ids)

        # Initial labeling
        initial_batch = engine.get_initial_batch()
        labels = {pid: (i % 2 == 0) for i, pid in enumerate(initial_batch)}
        engine.update_labels(labels)

        # Predict relevance for remaining papers
        predictions = engine.predict_relevance()

        assert len(predictions) == 80  # 100 - 20 initial
        assert all(0 <= p <= 1 for p in predictions.values())

    def test_engine_stopping_check(self):
        """Test stopping criterion check."""
        from jarvis_core.active_learning import (
            ActiveLearningEngine,
            ALConfig,
            BudgetStoppingCriterion,
        )

        config = ALConfig(batch_size=10, initial_sample_size=20)
        criterion = BudgetStoppingCriterion(max_labels=30)
        engine = ActiveLearningEngine(config=config, stopping_criterion=criterion)

        embeddings = np.random.rand(100, 64)
        paper_ids = [f"paper_{i}" for i in range(100)]
        engine.initialize(embeddings=embeddings, paper_ids=paper_ids)

        # Initial labeling (20)
        initial_batch = engine.get_initial_batch()
        labels = dict.fromkeys(initial_batch, True)
        engine.update_labels(labels)

        assert engine.should_stop() == False

        # Next batch (10 more = 30 total)
        next_batch = engine.get_next_batch()
        labels = dict.fromkeys(next_batch, True)
        engine.update_labels(labels)

        assert engine.should_stop() == True

    def test_engine_export_results(self):
        """Test exporting screening results."""
        from jarvis_core.active_learning import ActiveLearningEngine, ALConfig

        config = ALConfig(batch_size=5, initial_sample_size=10)
        engine = ActiveLearningEngine(config=config)

        embeddings = np.random.rand(50, 64)
        paper_ids = [f"paper_{i}" for i in range(50)]
        engine.initialize(embeddings=embeddings, paper_ids=paper_ids)

        # Labeling
        initial_batch = engine.get_initial_batch()
        labels = {pid: (i < 5) for i, pid in enumerate(initial_batch)}
        engine.update_labels(labels)

        results = engine.export_results()

        assert "labeled" in results
        assert "predicted" in results
        assert "metrics" in results
        assert len(results["labeled"]) == 10


class TestActiveLearningCLI:
    """Tests for Active Learning CLI."""

    def test_cli_entry_point_exists(self):
        """Test CLI entry point is defined."""
        from jarvis_core.active_learning import cli

        assert hasattr(cli, "cmd_screen")

    def test_cli_help(self):
        """Test CLI help message."""
        import subprocess

        result = subprocess.run(
            ["python", "-m", "jarvis_core.active_learning.cli", "--help"],
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
        from jarvis_core.active_learning import (
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
