# JARVIS-ML-Pipeline A+〜S評価達成のための厳密指示書

**対象リポジトリ**: `https://github.com/kaneko-ai/jarvis-ml-pipeline`
**目標スコア**: 100点以上（A+〜S評価）
**現在スコア**: 78/100点（B+）
**必要改善ポイント**: +22点以上

---

## 目次

1. [Phase 1: 緊急対応（テスト欠落修正）](#phase-1-緊急対応テスト欠落修正)
2. [Phase 2: ドキュメント整備](#phase-2-ドキュメント整備)
3. [Phase 3: CI/CD強化](#phase-3-cicd強化)
4. [Phase 4: コード品質向上](#phase-4-コード品質向上)
5. [Phase 5: 機能拡張・高度化](#phase-5-機能拡張高度化)
6. [Phase 6: セキュリティ・本番対応](#phase-6-セキュリティ本番対応)
7. [検証チェックリスト](#検証チェックリスト)

---

## Phase 1: 緊急対応（テスト欠落修正）

### 1.1 `tests/test_prisma.py` の作成 【+2点】

```python
"""Tests for the PRISMA Diagram Generation Module.

Per JARVIS_COMPLETION_PLAN_v3 Task 2.4
"""

import pytest
from pathlib import Path
import tempfile


class TestPRISMASchema:
    """Tests for PRISMA schema."""

    def test_prisma_stage_enum(self):
        """Test PRISMAStage enum values."""
        from jarvis_core.prisma.schema import PRISMAStage
        
        assert PRISMAStage.IDENTIFICATION.value == "identification"
        assert PRISMAStage.SCREENING.value == "screening"
        assert PRISMAStage.ELIGIBILITY.value == "eligibility"
        assert PRISMAStage.INCLUDED.value == "included"

    def test_exclusion_reason_dataclass(self):
        """Test ExclusionReason dataclass."""
        from jarvis_core.prisma.schema import ExclusionReason
        
        reason = ExclusionReason(
            reason="Duplicate publication",
            count=15,
            stage="screening"
        )
        
        assert reason.reason == "Duplicate publication"
        assert reason.count == 15
        assert reason.stage == "screening"

    def test_prisma_data_initialization(self):
        """Test PRISMAData dataclass initialization."""
        from jarvis_core.prisma.schema import PRISMAData, ExclusionReason
        
        data = PRISMAData(
            identification_database=1000,
            identification_other=50,
            duplicates_removed=200,
            records_screened=850,
            records_excluded_screening=500,
            full_text_assessed=350,
            full_text_excluded=100,
            studies_included=250,
            exclusion_reasons=[
                ExclusionReason("Not relevant", 300, "screening"),
                ExclusionReason("No full text", 50, "eligibility"),
            ]
        )
        
        assert data.identification_database == 1000
        assert data.studies_included == 250
        assert len(data.exclusion_reasons) == 2

    def test_prisma_data_validation(self):
        """Test PRISMAData validation logic."""
        from jarvis_core.prisma.schema import PRISMAData
        
        data = PRISMAData(
            identification_database=100,
            identification_other=0,
            duplicates_removed=10,
            records_screened=90,
            records_excluded_screening=40,
            full_text_assessed=50,
            full_text_excluded=20,
            studies_included=30,
        )
        
        # Validate flow consistency
        total_identified = data.identification_database + data.identification_other
        after_duplicates = total_identified - data.duplicates_removed
        assert after_duplicates == data.records_screened
        
        after_screening = data.records_screened - data.records_excluded_screening
        assert after_screening == data.full_text_assessed
        
        after_eligibility = data.full_text_assessed - data.full_text_excluded
        assert after_eligibility == data.studies_included

    def test_prisma_data_to_dict(self):
        """Test PRISMAData serialization."""
        from jarvis_core.prisma.schema import PRISMAData
        
        data = PRISMAData(
            identification_database=500,
            identification_other=25,
            duplicates_removed=75,
            records_screened=450,
            records_excluded_screening=200,
            full_text_assessed=250,
            full_text_excluded=50,
            studies_included=200,
        )
        
        result = data.to_dict()
        
        assert result["identification_database"] == 500
        assert result["studies_included"] == 200
        assert "exclusion_reasons" in result

    def test_prisma_data_from_dict(self):
        """Test PRISMAData deserialization."""
        from jarvis_core.prisma.schema import PRISMAData
        
        input_dict = {
            "identification_database": 300,
            "identification_other": 10,
            "duplicates_removed": 30,
            "records_screened": 280,
            "records_excluded_screening": 100,
            "full_text_assessed": 180,
            "full_text_excluded": 30,
            "studies_included": 150,
        }
        
        data = PRISMAData.from_dict(input_dict)
        
        assert data.identification_database == 300
        assert data.studies_included == 150


class TestPRISMAGenerator:
    """Tests for PRISMA diagram generator."""

    def test_generator_initialization(self):
        """Test PRISMAGenerator initialization."""
        from jarvis_core.prisma.generator import PRISMAGenerator
        
        generator = PRISMAGenerator()
        assert generator is not None

    def test_generate_mermaid_basic(self):
        """Test basic Mermaid diagram generation."""
        from jarvis_core.prisma.generator import PRISMAGenerator
        from jarvis_core.prisma.schema import PRISMAData
        
        generator = PRISMAGenerator()
        data = PRISMAData(
            identification_database=1000,
            identification_other=50,
            duplicates_removed=200,
            records_screened=850,
            records_excluded_screening=500,
            full_text_assessed=350,
            full_text_excluded=100,
            studies_included=250,
        )
        
        mermaid = generator.generate_mermaid(data)
        
        assert "flowchart TD" in mermaid or "graph TD" in mermaid
        assert "1000" in mermaid  # identification_database
        assert "250" in mermaid  # studies_included
        assert "Identification" in mermaid or "identification" in mermaid.lower()

    def test_generate_mermaid_with_exclusion_reasons(self):
        """Test Mermaid diagram with exclusion reasons."""
        from jarvis_core.prisma.generator import PRISMAGenerator
        from jarvis_core.prisma.schema import PRISMAData, ExclusionReason
        
        generator = PRISMAGenerator()
        data = PRISMAData(
            identification_database=500,
            identification_other=0,
            duplicates_removed=50,
            records_screened=450,
            records_excluded_screening=200,
            full_text_assessed=250,
            full_text_excluded=100,
            studies_included=150,
            exclusion_reasons=[
                ExclusionReason("Not RCT", 50, "eligibility"),
                ExclusionReason("Wrong population", 30, "eligibility"),
                ExclusionReason("No outcome data", 20, "eligibility"),
            ]
        )
        
        mermaid = generator.generate_mermaid(data)
        
        assert "Not RCT" in mermaid or "50" in mermaid
        assert "150" in mermaid  # studies_included

    def test_generate_svg(self):
        """Test SVG diagram generation."""
        from jarvis_core.prisma.generator import PRISMAGenerator
        from jarvis_core.prisma.schema import PRISMAData
        
        generator = PRISMAGenerator()
        data = PRISMAData(
            identification_database=100,
            identification_other=10,
            duplicates_removed=20,
            records_screened=90,
            records_excluded_screening=40,
            full_text_assessed=50,
            full_text_excluded=10,
            studies_included=40,
        )
        
        svg = generator.generate_svg(data)
        
        assert svg.startswith("<svg") or svg.startswith("<?xml")
        assert "</svg>" in svg
        assert "100" in svg or "40" in svg

    def test_generate_svg_file_output(self):
        """Test SVG file output."""
        from jarvis_core.prisma.generator import PRISMAGenerator
        from jarvis_core.prisma.schema import PRISMAData
        
        generator = PRISMAGenerator()
        data = PRISMAData(
            identification_database=100,
            identification_other=0,
            duplicates_removed=10,
            records_screened=90,
            records_excluded_screening=30,
            full_text_assessed=60,
            full_text_excluded=10,
            studies_included=50,
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "prisma_flow.svg"
            generator.generate_svg(data, output_path=output_path)
            
            assert output_path.exists()
            content = output_path.read_text()
            assert "<svg" in content or "<?xml" in content

    def test_generate_html_interactive(self):
        """Test interactive HTML diagram generation."""
        from jarvis_core.prisma.generator import PRISMAGenerator
        from jarvis_core.prisma.schema import PRISMAData
        
        generator = PRISMAGenerator()
        data = PRISMAData(
            identification_database=200,
            identification_other=20,
            duplicates_removed=40,
            records_screened=180,
            records_excluded_screening=80,
            full_text_assessed=100,
            full_text_excluded=30,
            studies_included=70,
        )
        
        html = generator.generate_html(data)
        
        assert "<html" in html.lower() or "<!doctype" in html.lower()
        assert "mermaid" in html.lower() or "svg" in html.lower()


class TestGeneratePrismaFlowFunction:
    """Tests for convenience function."""

    def test_generate_prisma_flow_mermaid(self):
        """Test generate_prisma_flow with Mermaid output."""
        from jarvis_core.prisma import generate_prisma_flow
        from jarvis_core.prisma.schema import PRISMAData
        
        data = PRISMAData(
            identification_database=500,
            identification_other=50,
            duplicates_removed=100,
            records_screened=450,
            records_excluded_screening=200,
            full_text_assessed=250,
            full_text_excluded=75,
            studies_included=175,
        )
        
        result = generate_prisma_flow(data, format="mermaid")
        
        assert "flowchart" in result.lower() or "graph" in result.lower()

    def test_generate_prisma_flow_svg(self):
        """Test generate_prisma_flow with SVG output."""
        from jarvis_core.prisma import generate_prisma_flow
        from jarvis_core.prisma.schema import PRISMAData
        
        data = PRISMAData(
            identification_database=100,
            identification_other=0,
            duplicates_removed=10,
            records_screened=90,
            records_excluded_screening=30,
            full_text_assessed=60,
            full_text_excluded=10,
            studies_included=50,
        )
        
        result = generate_prisma_flow(data, format="svg")
        
        assert "<svg" in result or "<?xml" in result

    def test_generate_prisma_flow_from_dict(self):
        """Test generate_prisma_flow from dictionary input."""
        from jarvis_core.prisma import generate_prisma_flow
        
        data_dict = {
            "identification_database": 250,
            "identification_other": 25,
            "duplicates_removed": 50,
            "records_screened": 225,
            "records_excluded_screening": 100,
            "full_text_assessed": 125,
            "full_text_excluded": 25,
            "studies_included": 100,
        }
        
        result = generate_prisma_flow(data_dict, format="mermaid")
        
        assert "250" in result or "100" in result


class TestPRISMA2020Compliance:
    """Tests for PRISMA 2020 statement compliance."""

    def test_prisma_2020_required_items(self):
        """Test that all PRISMA 2020 required items are supported."""
        from jarvis_core.prisma.schema import PRISMAData
        
        # PRISMA 2020 requires these flow diagram elements
        required_attributes = [
            "identification_database",
            "identification_other",
            "duplicates_removed",
            "records_screened",
            "records_excluded_screening",
            "full_text_assessed",
            "full_text_excluded",
            "studies_included",
        ]
        
        data = PRISMAData(
            identification_database=0,
            identification_other=0,
            duplicates_removed=0,
            records_screened=0,
            records_excluded_screening=0,
            full_text_assessed=0,
            full_text_excluded=0,
            studies_included=0,
        )
        
        for attr in required_attributes:
            assert hasattr(data, attr), f"Missing PRISMA 2020 required attribute: {attr}"

    def test_multiple_database_sources(self):
        """Test support for multiple database sources."""
        from jarvis_core.prisma.schema import PRISMAData
        
        # PRISMA 2020 supports multiple database sources
        data = PRISMAData(
            identification_database=1000,
            identification_other=200,
            identification_registers=50,  # Optional: clinical trial registers
            duplicates_removed=150,
            records_screened=1100,
            records_excluded_screening=600,
            full_text_assessed=500,
            full_text_excluded=100,
            studies_included=400,
            database_sources=["PubMed", "Embase", "Cochrane"],
        )
        
        assert data.identification_database + data.identification_other >= data.records_screened + data.duplicates_removed


class TestModuleImports:
    """Test module imports."""

    def test_main_imports(self):
        """Test main module imports."""
        from jarvis_core.prisma import (
            PRISMAData,
            PRISMAStage,
            ExclusionReason,
            PRISMAGenerator,
            generate_prisma_flow,
        )
        
        assert PRISMAData is not None
        assert PRISMAStage is not None
        assert ExclusionReason is not None
        assert PRISMAGenerator is not None
        assert generate_prisma_flow is not None

    def test_schema_imports(self):
        """Test schema module imports."""
        from jarvis_core.prisma.schema import (
            PRISMAData,
            PRISMAStage,
            ExclusionReason,
        )
        
        assert PRISMAData is not None
        assert PRISMAStage is not None
        assert ExclusionReason is not None

    def test_generator_imports(self):
        """Test generator module imports."""
        from jarvis_core.prisma.generator import (
            PRISMAGenerator,
            generate_prisma_flow,
        )
        
        assert PRISMAGenerator is not None
        assert generate_prisma_flow is not None
```

---

### 1.2 `tests/test_active_learning.py` の作成 【+2点】

```python
"""Tests for the Active Learning Module.

Per JARVIS_COMPLETION_PLAN_v3 Task 2.5
"""

import pytest
from unittest.mock import Mock, MagicMock
import numpy as np


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
        embeddings = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.5, 0.5, 0.5],
        ])
        
        selected = strategy.select(embeddings, n=3)
        
        assert len(selected) == 3
        # Should select diverse samples (far apart in embedding space)

    def test_hybrid_strategy(self):
        """Test hybrid uncertainty + diversity strategy."""
        from jarvis_core.active_learning import UncertaintySampling, DiversitySampling
        from jarvis_core.active_learning.query import HybridStrategy
        
        strategy = HybridStrategy(
            uncertainty_weight=0.7,
            diversity_weight=0.3,
        )
        
        probabilities = np.array([0.5, 0.3, 0.7, 0.45])
        embeddings = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0],
        ])
        
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
        from jarvis_core.active_learning import RecallStoppingCriterion, ALState
        
        criterion = RecallStoppingCriterion(target_recall=0.95)
        state = ALState()
        state.record_metrics(iteration=1, recall=0.80)
        
        assert criterion.should_stop(state) == False

    def test_recall_stopping_met(self):
        """Test RecallStoppingCriterion when met."""
        from jarvis_core.active_learning import RecallStoppingCriterion, ALState
        
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
        from jarvis_core.active_learning import BudgetStoppingCriterion, ALState
        
        criterion = BudgetStoppingCriterion(max_labels=100)
        state = ALState()
        state._labeled_count = 50
        
        assert criterion.should_stop(state) == False

    def test_budget_stopping_met(self):
        """Test BudgetStoppingCriterion when met."""
        from jarvis_core.active_learning import BudgetStoppingCriterion, ALState
        
        criterion = BudgetStoppingCriterion(max_labels=100)
        state = ALState()
        state._labeled_count = 100
        
        assert criterion.should_stop(state) == True

    def test_combined_stopping_criteria(self):
        """Test combining multiple stopping criteria."""
        from jarvis_core.active_learning import (
            RecallStoppingCriterion,
            BudgetStoppingCriterion,
            ALState,
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
        labels = {pid: True for pid in initial_batch}
        engine.update_labels(labels)
        
        assert engine.should_stop() == False
        
        # Next batch (10 more = 30 total)
        next_batch = engine.get_next_batch()
        labels = {pid: True for pid in next_batch}
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
        assert result.returncode == 0 or "usage" in result.stdout.lower() or "help" in result.stderr.lower()


class TestModuleImports:
    """Test module imports."""

    def test_main_imports(self):
        """Test main module imports."""
        from jarvis_core.active_learning import (
            ActiveLearningEngine,
            ALConfig,
            ALState,
            QueryStrategy,
            UncertaintySampling,
            DiversitySampling,
            StoppingCriterion,
            RecallStoppingCriterion,
            BudgetStoppingCriterion,
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
```

---

### 1.3 `tests/test_paper_scoring.py` の作成 【+1点】

```python
"""Tests for the Paper Scoring Module.

Per JARVIS_COMPLETION_PLAN_v3 Sprint 19-20
"""

import pytest


class TestScoringWeights:
    """Tests for scoring weights configuration."""

    def test_default_weights(self):
        """Test default scoring weights."""
        from jarvis_core.paper_scoring import ScoringWeights
        
        weights = ScoringWeights()
        
        assert weights.evidence_weight > 0
        assert weights.citation_weight > 0
        assert weights.recency_weight > 0
        assert weights.source_weight > 0
        
        # Weights should sum to approximately 1.0
        total = (
            weights.evidence_weight +
            weights.citation_weight +
            weights.recency_weight +
            weights.source_weight
        )
        assert 0.99 <= total <= 1.01

    def test_custom_weights(self):
        """Test custom scoring weights."""
        from jarvis_core.paper_scoring import ScoringWeights
        
        weights = ScoringWeights(
            evidence_weight=0.4,
            citation_weight=0.3,
            recency_weight=0.2,
            source_weight=0.1,
        )
        
        assert weights.evidence_weight == 0.4
        assert weights.citation_weight == 0.3

    def test_weights_normalization(self):
        """Test weights auto-normalization."""
        from jarvis_core.paper_scoring import ScoringWeights
        
        weights = ScoringWeights(
            evidence_weight=4,
            citation_weight=3,
            recency_weight=2,
            source_weight=1,
            normalize=True,
        )
        
        total = (
            weights.evidence_weight +
            weights.citation_weight +
            weights.recency_weight +
            weights.source_weight
        )
        assert 0.99 <= total <= 1.01


class TestPaperScore:
    """Tests for PaperScore dataclass."""

    def test_paper_score_creation(self):
        """Test PaperScore creation."""
        from jarvis_core.paper_scoring import PaperScore
        
        score = PaperScore(
            paper_id="paper_123",
            overall_score=0.85,
            evidence_score=0.90,
            citation_score=0.80,
            recency_score=0.75,
            source_score=0.95,
        )
        
        assert score.paper_id == "paper_123"
        assert score.overall_score == 0.85

    def test_paper_score_to_dict(self):
        """Test PaperScore serialization."""
        from jarvis_core.paper_scoring import PaperScore
        
        score = PaperScore(
            paper_id="paper_456",
            overall_score=0.72,
            evidence_score=0.80,
            citation_score=0.60,
            recency_score=0.70,
            source_score=0.85,
        )
        
        result = score.to_dict()
        
        assert result["paper_id"] == "paper_456"
        assert result["overall_score"] == 0.72
        assert "evidence_score" in result

    def test_paper_score_comparison(self):
        """Test PaperScore comparison."""
        from jarvis_core.paper_scoring import PaperScore
        
        score_a = PaperScore(paper_id="a", overall_score=0.80)
        score_b = PaperScore(paper_id="b", overall_score=0.90)
        
        assert score_b > score_a
        assert score_a < score_b


class TestPaperScorer:
    """Tests for PaperScorer class."""

    def test_scorer_initialization(self):
        """Test PaperScorer initialization."""
        from jarvis_core.paper_scoring import PaperScorer
        
        scorer = PaperScorer()
        assert scorer is not None

    def test_scorer_with_custom_weights(self):
        """Test PaperScorer with custom weights."""
        from jarvis_core.paper_scoring import PaperScorer, ScoringWeights
        
        weights = ScoringWeights(
            evidence_weight=0.5,
            citation_weight=0.2,
            recency_weight=0.2,
            source_weight=0.1,
        )
        scorer = PaperScorer(weights=weights)
        
        assert scorer.weights.evidence_weight == 0.5

    def test_score_paper_basic(self):
        """Test basic paper scoring."""
        from jarvis_core.paper_scoring import PaperScorer
        from jarvis_core.evidence.schema import EvidenceGrade, EvidenceLevel, StudyType
        
        scorer = PaperScorer()
        
        paper = {
            "paper_id": "test_001",
            "title": "A randomized controlled trial",
            "year": 2024,
            "citation_count": 50,
            "source": "pubmed",
        }
        
        evidence_grade = EvidenceGrade(
            level=EvidenceLevel.LEVEL_1B,
            study_type=StudyType.RCT,
            confidence=0.9,
        )
        
        score = scorer.score(paper, evidence_grade=evidence_grade)
        
        assert score.paper_id == "test_001"
        assert 0 <= score.overall_score <= 1
        assert score.evidence_score > 0

    def test_score_paper_high_evidence(self):
        """Test scoring paper with high evidence level."""
        from jarvis_core.paper_scoring import PaperScorer
        from jarvis_core.evidence.schema import EvidenceGrade, EvidenceLevel, StudyType
        
        scorer = PaperScorer()
        
        paper = {
            "paper_id": "meta_001",
            "year": 2024,
            "citation_count": 100,
            "source": "cochrane",
        }
        
        evidence_grade = EvidenceGrade(
            level=EvidenceLevel.LEVEL_1A,
            study_type=StudyType.SYSTEMATIC_REVIEW,
            confidence=0.95,
        )
        
        score = scorer.score(paper, evidence_grade=evidence_grade)
        
        # High evidence level should result in high evidence score
        assert score.evidence_score >= 0.9

    def test_score_paper_low_evidence(self):
        """Test scoring paper with low evidence level."""
        from jarvis_core.paper_scoring import PaperScorer
        from jarvis_core.evidence.schema import EvidenceGrade, EvidenceLevel, StudyType
        
        scorer = PaperScorer()
        
        paper = {
            "paper_id": "opinion_001",
            "year": 2020,
            "citation_count": 5,
            "source": "preprint",
        }
        
        evidence_grade = EvidenceGrade(
            level=EvidenceLevel.LEVEL_5,
            study_type=StudyType.EXPERT_OPINION,
            confidence=0.6,
        )
        
        score = scorer.score(paper, evidence_grade=evidence_grade)
        
        # Low evidence level should result in lower evidence score
        assert score.evidence_score < 0.5

    def test_recency_scoring(self):
        """Test recency component of scoring."""
        from jarvis_core.paper_scoring import PaperScorer
        
        scorer = PaperScorer()
        
        recent_paper = {"paper_id": "recent", "year": 2025}
        old_paper = {"paper_id": "old", "year": 2010}
        
        recent_score = scorer.score(recent_paper)
        old_score = scorer.score(old_paper)
        
        assert recent_score.recency_score > old_score.recency_score

    def test_citation_scoring(self):
        """Test citation component of scoring."""
        from jarvis_core.paper_scoring import PaperScorer
        
        scorer = PaperScorer()
        
        highly_cited = {"paper_id": "popular", "citation_count": 500}
        low_cited = {"paper_id": "new", "citation_count": 2}
        
        high_score = scorer.score(highly_cited)
        low_score = scorer.score(low_cited)
        
        assert high_score.citation_score > low_score.citation_score

    def test_source_scoring(self):
        """Test source component of scoring."""
        from jarvis_core.paper_scoring import PaperScorer
        
        scorer = PaperScorer()
        
        pubmed_paper = {"paper_id": "pm", "source": "pubmed"}
        preprint_paper = {"paper_id": "pp", "source": "preprint"}
        
        pubmed_score = scorer.score(pubmed_paper)
        preprint_score = scorer.score(preprint_paper)
        
        # Peer-reviewed source should score higher
        assert pubmed_score.source_score >= preprint_score.source_score

    def test_batch_scoring(self):
        """Test batch paper scoring."""
        from jarvis_core.paper_scoring import PaperScorer
        
        scorer = PaperScorer()
        
        papers = [
            {"paper_id": f"paper_{i}", "year": 2020 + i, "citation_count": i * 10}
            for i in range(10)
        ]
        
        scores = scorer.score_batch(papers)
        
        assert len(scores) == 10
        assert all(hasattr(s, "overall_score") for s in scores)


class TestCalculatePaperScoreFunction:
    """Tests for convenience function."""

    def test_calculate_paper_score_basic(self):
        """Test calculate_paper_score function."""
        from jarvis_core.paper_scoring import calculate_paper_score
        
        paper = {
            "paper_id": "func_test",
            "year": 2023,
            "citation_count": 25,
        }
        
        score = calculate_paper_score(paper)
        
        assert score.paper_id == "func_test"
        assert 0 <= score.overall_score <= 1

    def test_calculate_paper_score_with_evidence(self):
        """Test calculate_paper_score with evidence grade."""
        from jarvis_core.paper_scoring import calculate_paper_score
        from jarvis_core.evidence.schema import EvidenceGrade, EvidenceLevel, StudyType
        
        paper = {"paper_id": "with_evidence"}
        evidence = EvidenceGrade(
            level=EvidenceLevel.LEVEL_2B,
            study_type=StudyType.COHORT_PROSPECTIVE,
            confidence=0.8,
        )
        
        score = calculate_paper_score(paper, evidence_grade=evidence)
        
        assert score.evidence_score > 0


class TestModuleImports:
    """Test module imports."""

    def test_main_imports(self):
        """Test main module imports."""
        from jarvis_core.paper_scoring import (
            PaperScore,
            PaperScorer,
            ScoringWeights,
            calculate_paper_score,
        )
        
        assert PaperScore is not None
        assert PaperScorer is not None
        assert ScoringWeights is not None
        assert calculate_paper_score is not None
```

---

### 1.4 `tests/test_hybrid_search.py` の作成 【+1点】

```python
"""Tests for the Hybrid Search Module.

Per JARVIS_COMPLETION_PLAN_v3 Task 1.2
"""

import pytest
import numpy as np


class TestBM25Index:
    """Tests for BM25 index."""

    def test_bm25_initialization(self):
        """Test BM25Index initialization."""
        from jarvis_core.embeddings import BM25Index
        
        index = BM25Index()
        assert index is not None

    def test_bm25_add_documents(self):
        """Test adding documents to BM25 index."""
        from jarvis_core.embeddings import BM25Index
        
        index = BM25Index()
        
        documents = [
            {"id": "1", "text": "machine learning for medical diagnosis"},
            {"id": "2", "text": "deep learning neural networks"},
            {"id": "3", "text": "clinical trial randomized controlled"},
        ]
        
        index.add_documents(documents)
        
        assert index.document_count == 3

    def test_bm25_search(self):
        """Test BM25 search."""
        from jarvis_core.embeddings import BM25Index
        
        index = BM25Index()
        
        documents = [
            {"id": "1", "text": "machine learning for medical diagnosis"},
            {"id": "2", "text": "deep learning neural networks image classification"},
            {"id": "3", "text": "clinical trial randomized controlled study"},
        ]
        
        index.add_documents(documents)
        
        results = index.search("machine learning", top_k=2)
        
        assert len(results) <= 2
        assert results[0]["id"] == "1"  # Most relevant

    def test_bm25_empty_query(self):
        """Test BM25 with empty query."""
        from jarvis_core.embeddings import BM25Index
        
        index = BM25Index()
        index.add_documents([{"id": "1", "text": "test document"}])
        
        results = index.search("", top_k=5)
        
        assert len(results) == 0 or results[0]["score"] == 0


class TestSentenceTransformerEmbedding:
    """Tests for Sentence Transformer embeddings."""

    def test_embedding_initialization(self):
        """Test SentenceTransformerEmbedding initialization."""
        from jarvis_core.embeddings import SentenceTransformerEmbedding
        
        embedder = SentenceTransformerEmbedding()
        assert embedder is not None

    def test_embed_single_text(self):
        """Test embedding single text."""
        from jarvis_core.embeddings import SentenceTransformerEmbedding
        
        embedder = SentenceTransformerEmbedding()
        
        embedding = embedder.embed("This is a test sentence.")
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.ndim == 1
        assert len(embedding) > 0

    def test_embed_batch(self):
        """Test embedding batch of texts."""
        from jarvis_core.embeddings import SentenceTransformerEmbedding
        
        embedder = SentenceTransformerEmbedding()
        
        texts = [
            "First document about machine learning",
            "Second document about clinical trials",
            "Third document about data analysis",
        ]
        
        embeddings = embedder.embed_batch(texts)
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == 3

    def test_embedding_similarity(self):
        """Test embedding similarity."""
        from jarvis_core.embeddings import SentenceTransformerEmbedding
        
        embedder = SentenceTransformerEmbedding()
        
        emb1 = embedder.embed("machine learning")
        emb2 = embedder.embed("artificial intelligence")
        emb3 = embedder.embed("cooking recipes")
        
        # Cosine similarity
        def cosine_sim(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        sim_related = cosine_sim(emb1, emb2)
        sim_unrelated = cosine_sim(emb1, emb3)
        
        assert sim_related > sim_unrelated


class TestHybridSearch:
    """Tests for Hybrid Search."""

    def test_hybrid_search_initialization(self):
        """Test HybridSearch initialization."""
        from jarvis_core.embeddings import HybridSearch
        
        search = HybridSearch()
        assert search is not None

    def test_hybrid_search_add_documents(self):
        """Test adding documents to hybrid search."""
        from jarvis_core.embeddings import HybridSearch
        
        search = HybridSearch()
        
        documents = [
            {"id": "1", "text": "machine learning medical", "title": "ML in Medicine"},
            {"id": "2", "text": "deep learning vision", "title": "Computer Vision"},
        ]
        
        search.add_documents(documents)
        
        assert search.document_count == 2

    def test_hybrid_search_query(self):
        """Test hybrid search query."""
        from jarvis_core.embeddings import HybridSearch
        
        search = HybridSearch()
        
        documents = [
            {"id": "1", "text": "machine learning for medical diagnosis treatment"},
            {"id": "2", "text": "deep learning computer vision image"},
            {"id": "3", "text": "clinical trial drug efficacy randomized"},
        ]
        
        search.add_documents(documents)
        
        results = search.search("machine learning medical", top_k=2)
        
        assert len(results) <= 2
        assert results[0]["id"] == "1"

    def test_hybrid_search_rrf_fusion(self):
        """Test RRF fusion method."""
        from jarvis_core.embeddings import HybridSearch, FusionMethod
        
        search = HybridSearch(fusion_method=FusionMethod.RRF)
        
        documents = [
            {"id": "1", "text": "cancer treatment chemotherapy"},
            {"id": "2", "text": "cancer diagnosis machine learning"},
            {"id": "3", "text": "heart disease prevention"},
        ]
        
        search.add_documents(documents)
        
        results = search.search("cancer machine learning", top_k=3)
        
        # Document 2 should rank high (matches both cancer and ML)
        top_ids = [r["id"] for r in results[:2]]
        assert "2" in top_ids

    def test_hybrid_search_weights(self):
        """Test hybrid search with custom weights."""
        from jarvis_core.embeddings import HybridSearch
        
        # Emphasize BM25 (keyword matching)
        search_bm25_heavy = HybridSearch(bm25_weight=0.8, embedding_weight=0.2)
        
        # Emphasize embeddings (semantic matching)
        search_emb_heavy = HybridSearch(bm25_weight=0.2, embedding_weight=0.8)
        
        documents = [
            {"id": "1", "text": "randomized controlled trial RCT"},
            {"id": "2", "text": "experimental study with random assignment"},
        ]
        
        search_bm25_heavy.add_documents(documents)
        search_emb_heavy.add_documents(documents)
        
        # Query with exact keyword
        results_bm25 = search_bm25_heavy.search("RCT", top_k=2)
        results_emb = search_emb_heavy.search("RCT", top_k=2)
        
        # BM25-heavy should prefer exact match
        assert results_bm25[0]["id"] == "1"


class TestFusionMethod:
    """Tests for fusion methods."""

    def test_fusion_method_enum(self):
        """Test FusionMethod enum."""
        from jarvis_core.embeddings import FusionMethod
        
        assert FusionMethod.RRF.value == "rrf"
        assert FusionMethod.LINEAR.value == "linear"
        assert FusionMethod.WEIGHTED.value == "weighted"


class TestSPECTER2:
    """Tests for SPECTER2 scientific embeddings."""

    def test_specter2_initialization(self):
        """Test SPECTER2Embedding initialization."""
        from jarvis_core.embeddings import SPECTER2Embedding
        
        embedder = SPECTER2Embedding()
        assert embedder is not None

    def test_specter2_embed(self):
        """Test SPECTER2 embedding."""
        from jarvis_core.embeddings import SPECTER2Embedding
        
        embedder = SPECTER2Embedding()
        
        embedding = embedder.embed(
            title="A randomized controlled trial of aspirin",
            abstract="Methods: We conducted a double-blind RCT..."
        )
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.ndim == 1


class TestGetEmbeddingModel:
    """Tests for get_embedding_model factory."""

    def test_get_general_model(self):
        """Test getting general embedding model."""
        from jarvis_core.embeddings import get_embedding_model
        
        model = get_embedding_model("general")
        
        assert model is not None

    def test_get_scientific_model(self):
        """Test getting scientific embedding model."""
        from jarvis_core.embeddings import get_embedding_model
        
        model = get_embedding_model("scientific")
        
        assert model is not None


class TestModuleImports:
    """Test module imports."""

    def test_main_imports(self):
        """Test main module imports."""
        from jarvis_core.embeddings import (
            SentenceTransformerEmbedding,
            get_default_embedding_model,
            get_embedding_model,
            BM25Index,
            HybridSearch,
            FusionMethod,
            SPECTER2Embedding,
        )
        
        assert SentenceTransformerEmbedding is not None
        assert BM25Index is not None
        assert HybridSearch is not None
        assert FusionMethod is not None
```

---

### 1.5 `tests/test_network_offline.py` の作成 【+1点】

```python
"""Tests for the Network/Offline Module.

Per JARVIS_COMPLETION_PLAN_v3 Task 1.5
"""

import pytest
from unittest.mock import Mock, patch


class TestNetworkDetector:
    """Tests for NetworkDetector."""

    def test_detector_initialization(self):
        """Test NetworkDetector initialization."""
        from jarvis_core.network import NetworkDetector
        
        detector = NetworkDetector()
        assert detector is not None

    def test_is_online_when_connected(self):
        """Test is_online returns True when connected."""
        from jarvis_core.network import NetworkDetector
        
        detector = NetworkDetector()
        
        with patch("socket.create_connection") as mock_conn:
            mock_conn.return_value = Mock()
            
            result = detector.is_online()
            
            assert result == True

    def test_is_online_when_disconnected(self):
        """Test is_online returns False when disconnected."""
        from jarvis_core.network import NetworkDetector
        import socket
        
        detector = NetworkDetector()
        
        with patch("socket.create_connection") as mock_conn:
            mock_conn.side_effect = socket.timeout()
            
            result = detector.is_online()
            
            assert result == False

    def test_get_network_status(self):
        """Test get_network_status returns NetworkStatus."""
        from jarvis_core.network import NetworkDetector, NetworkStatus
        
        detector = NetworkDetector()
        
        status = detector.get_status()
        
        assert isinstance(status, NetworkStatus)
        assert hasattr(status, "is_online")
        assert hasattr(status, "latency_ms")


class TestNetworkStatus:
    """Tests for NetworkStatus dataclass."""

    def test_status_creation(self):
        """Test NetworkStatus creation."""
        from jarvis_core.network import NetworkStatus
        
        status = NetworkStatus(
            is_online=True,
            latency_ms=50.0,
            last_check=1704067200.0,
        )
        
        assert status.is_online == True
        assert status.latency_ms == 50.0

    def test_status_offline(self):
        """Test NetworkStatus for offline state."""
        from jarvis_core.network import NetworkStatus
        
        status = NetworkStatus(
            is_online=False,
            latency_ms=None,
            last_check=1704067200.0,
        )
        
        assert status.is_online == False
        assert status.latency_ms is None


class TestDegradationLevel:
    """Tests for DegradationLevel enum."""

    def test_degradation_levels(self):
        """Test DegradationLevel enum values."""
        from jarvis_core.network import DegradationLevel
        
        assert DegradationLevel.FULL.value == "full"
        assert DegradationLevel.DEGRADED.value == "degraded"
        assert DegradationLevel.OFFLINE.value == "offline"


class TestDegradationManager:
    """Tests for DegradationManager."""

    def test_manager_initialization(self):
        """Test DegradationManager initialization."""
        from jarvis_core.network import DegradationManager
        
        manager = DegradationManager()
        assert manager is not None

    def test_get_current_level_online(self):
        """Test get_current_level when online."""
        from jarvis_core.network import DegradationManager, DegradationLevel
        
        manager = DegradationManager()
        
        with patch.object(manager, "_check_network", return_value=True):
            level = manager.get_current_level()
            
            assert level == DegradationLevel.FULL

    def test_get_current_level_offline(self):
        """Test get_current_level when offline."""
        from jarvis_core.network import DegradationManager, DegradationLevel
        
        manager = DegradationManager()
        
        with patch.object(manager, "_check_network", return_value=False):
            level = manager.get_current_level()
            
            assert level == DegradationLevel.OFFLINE

    def test_feature_availability_online(self):
        """Test feature availability when online."""
        from jarvis_core.network import DegradationManager, DegradationLevel
        
        manager = DegradationManager()
        manager._current_level = DegradationLevel.FULL
        
        assert manager.is_feature_available("api_search") == True
        assert manager.is_feature_available("local_search") == True

    def test_feature_availability_offline(self):
        """Test feature availability when offline."""
        from jarvis_core.network import DegradationManager, DegradationLevel
        
        manager = DegradationManager()
        manager._current_level = DegradationLevel.OFFLINE
        
        assert manager.is_feature_available("api_search") == False
        assert manager.is_feature_available("local_search") == True


class TestDegradationAwareDecorator:
    """Tests for degradation_aware decorator."""

    def test_decorator_online(self):
        """Test decorator when online."""
        from jarvis_core.network import degradation_aware
        
        @degradation_aware(feature="api_search")
        def fetch_from_api():
            return "api_result"
        
        with patch("jarvis_core.network.get_degradation_manager") as mock_mgr:
            mock_mgr.return_value.is_feature_available.return_value = True
            
            result = fetch_from_api()
            
            assert result == "api_result"

    def test_decorator_offline_raises(self):
        """Test decorator raises OfflineError when offline."""
        from jarvis_core.network import degradation_aware, OfflineError
        
        @degradation_aware(feature="api_search")
        def fetch_from_api():
            return "api_result"
        
        with patch("jarvis_core.network.get_degradation_manager") as mock_mgr:
            mock_mgr.return_value.is_feature_available.return_value = False
            
            with pytest.raises(OfflineError):
                fetch_from_api()

    def test_decorator_with_fallback(self):
        """Test decorator with fallback function."""
        from jarvis_core.network import degradation_aware
        
        def fallback_func():
            return "fallback_result"
        
        @degradation_aware(feature="api_search", fallback=fallback_func)
        def fetch_from_api():
            return "api_result"
        
        with patch("jarvis_core.network.get_degradation_manager") as mock_mgr:
            mock_mgr.return_value.is_feature_available.return_value = False
            
            result = fetch_from_api()
            
            assert result == "fallback_result"


class TestDegradationAwareWithQueue:
    """Tests for degradation_aware_with_queue decorator."""

    def test_queue_decorator_online(self):
        """Test queue decorator when online."""
        from jarvis_core.network import degradation_aware_with_queue
        
        @degradation_aware_with_queue(feature="api_sync")
        def sync_data(data):
            return f"synced:{data}"
        
        with patch("jarvis_core.network.get_degradation_manager") as mock_mgr:
            mock_mgr.return_value.is_feature_available.return_value = True
            
            result = sync_data("test")
            
            assert result == "synced:test"

    def test_queue_decorator_offline_queues(self):
        """Test queue decorator queues operation when offline."""
        from jarvis_core.network import degradation_aware_with_queue, OfflineQueuedError
        
        @degradation_aware_with_queue(feature="api_sync")
        def sync_data(data):
            return f"synced:{data}"
        
        with patch("jarvis_core.network.get_degradation_manager") as mock_mgr:
            mock_mgr.return_value.is_feature_available.return_value = False
            
            with pytest.raises(OfflineQueuedError) as exc_info:
                sync_data("test")
            
            assert exc_info.value.queued == True


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_is_online_function(self):
        """Test is_online convenience function."""
        from jarvis_core.network import is_online
        
        result = is_online()
        
        assert isinstance(result, bool)

    def test_get_network_status_function(self):
        """Test get_network_status convenience function."""
        from jarvis_core.network import get_network_status, NetworkStatus
        
        status = get_network_status()
        
        assert isinstance(status, NetworkStatus)

    def test_get_degradation_manager_function(self):
        """Test get_degradation_manager convenience function."""
        from jarvis_core.network import get_degradation_manager, DegradationManager
        
        manager = get_degradation_manager()
        
        assert isinstance(manager, DegradationManager)

    def test_get_degradation_manager_singleton(self):
        """Test get_degradation_manager returns singleton."""
        from jarvis_core.network import get_degradation_manager
        
        manager1 = get_degradation_manager()
        manager2 = get_degradation_manager()
        
        assert manager1 is manager2


class TestOfflineErrors:
    """Tests for offline error classes."""

    def test_offline_error(self):
        """Test OfflineError exception."""
        from jarvis_core.network import OfflineError
        
        error = OfflineError("Feature unavailable offline")
        
        assert str(error) == "Feature unavailable offline"
        assert isinstance(error, Exception)

    def test_offline_queued_error(self):
        """Test OfflineQueuedError exception."""
        from jarvis_core.network import OfflineQueuedError
        
        error = OfflineQueuedError("Operation queued", queue_id="q123")
        
        assert error.queued == True
        assert error.queue_id == "q123"


class TestModuleImports:
    """Test module imports."""

    def test_main_imports(self):
        """Test main module imports."""
        from jarvis_core.network import (
            NetworkDetector,
            NetworkStatus,
            is_online,
            get_network_status,
            DegradationLevel,
            DegradationManager,
            get_degradation_manager,
            degradation_aware,
            degradation_aware_with_queue,
            OfflineError,
            OfflineQueuedError,
        )
        
        assert NetworkDetector is not None
        assert NetworkStatus is not None
        assert is_online is not None
        assert DegradationLevel is not None
        assert DegradationManager is not None
```

---

## Phase 2: ドキュメント整備

### 2.1 `docs/api/README.md` の作成 【+1点】

```markdown
# JARVIS Research OS API Reference

## Overview

JARVIS Research OS provides both a Python API for programmatic access and a REST API for web integration.

## Python API

### Evidence Grading

```python
from jarvis_core.evidence import grade_evidence, EvidenceLevel

grade = grade_evidence(
    title="A randomized controlled trial of...",
    abstract="Methods: We conducted a double-blind RCT...",
    use_llm=False,
)

print(f"Level: {grade.level.value}")  # "1b"
print(f"Type: {grade.study_type.value}")  # "randomized_controlled_trial"
print(f"Confidence: {grade.confidence}")  # 0.85
```

### Citation Analysis

```python
from jarvis_core.citation import (
    extract_citation_contexts,
    classify_citation_stance,
    CitationGraph,
)

# Extract citations from text
contexts = extract_citation_contexts(
    text="Previous work [1] showed significant results...",
    paper_id="current_paper",
    reference_map={"1": "cited_paper_id"},
)

# Classify stance
for ctx in contexts:
    stance = classify_citation_stance(ctx.get_full_context())
    print(f"Stance: {stance.stance.value}")  # "support", "contrast", "mention"

# Build citation graph
graph = CitationGraph()
graph.add_edge("paper_a", "paper_b", stance=CitationStance.SUPPORT)
supporting = graph.get_supporting_citations("paper_b")
```

### Contradiction Detection

```python
from jarvis_core.contradiction import (
    Claim,
    ContradictionDetector,
    detect_contradiction,
)

detector = ContradictionDetector()

claim_a = Claim(claim_id="1", text="Drug X increases survival", paper_id="A")
claim_b = Claim(claim_id="2", text="Drug X decreases survival", paper_id="B")

result = detector.detect(claim_a, claim_b)
print(f"Contradictory: {result.is_contradictory}")  # True
print(f"Type: {result.contradiction_type.value}")  # "direct"
```

### PRISMA Diagram Generation

```python
from jarvis_core.prisma import PRISMAData, generate_prisma_flow

data = PRISMAData(
    identification_database=1000,
    identification_other=50,
    duplicates_removed=200,
    records_screened=850,
    records_excluded_screening=500,
    full_text_assessed=350,
    full_text_excluded=100,
    studies_included=250,
)

# Generate Mermaid diagram
mermaid = generate_prisma_flow(data, format="mermaid")

# Generate SVG
svg = generate_prisma_flow(data, format="svg")
```

### Active Learning

```python
from jarvis_core.active_learning import (
    ActiveLearningEngine,
    ALConfig,
    UncertaintySampling,
    BudgetStoppingCriterion,
)

config = ALConfig(batch_size=10, initial_sample_size=20)
criterion = BudgetStoppingCriterion(max_labels=100)
engine = ActiveLearningEngine(config=config, stopping_criterion=criterion)

# Initialize with paper embeddings
engine.initialize(embeddings=embeddings, paper_ids=paper_ids)

# Get initial batch for manual labeling
initial_batch = engine.get_initial_batch()

# Update with labels
labels = {pid: is_relevant for pid, is_relevant in user_labels.items()}
engine.update_labels(labels)

# Get next batch (active learning selects most informative)
next_batch = engine.get_next_batch()

# Check stopping
if engine.should_stop():
    results = engine.export_results()
```

### Hybrid Search

```python
from jarvis_core.embeddings import HybridSearch, FusionMethod

search = HybridSearch(
    fusion_method=FusionMethod.RRF,
    bm25_weight=0.4,
    embedding_weight=0.6,
)

search.add_documents([
    {"id": "1", "text": "machine learning medical diagnosis"},
    {"id": "2", "text": "clinical trial results"},
])

results = search.search("ML in medicine", top_k=10)
```

## REST API

### Base URL

```
http://localhost:8000/api
```

### Authentication

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/runs
```

### Endpoints

#### Health Check

```
GET /api/health
```

#### List Runs

```
GET /api/runs?limit=20
```

#### Get Run Details

```
GET /api/runs/{run_id}
```

#### Start New Run

```
POST /api/runs
Content-Type: application/json

{
  "query": "machine learning cancer diagnosis",
  "max_papers": 50,
  "config": {}
}
```

#### Search Corpus

```
GET /api/search?q=query&top_k=20
```

#### Upload Files

```
POST /api/upload/pdf
Content-Type: multipart/form-data

files: [file1.pdf, file2.pdf]
```

#### Get KPIs

```
GET /api/kpi
```

### Response Format

All responses follow this structure:

```json
{
  "status": "success",
  "data": { ... },
  "errors": [],
  "warnings": []
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 501 | Not Implemented |
| 500 | Internal Server Error |

## Rate Limits

- Default: 100 requests/minute
- Authenticated: 1000 requests/minute

## Versioning

API version is included in the path: `/api/v1/...`

Current version: `v1`
```

---

### 2.2 `CONTRIBUTING.md` の作成 【+1点】

```markdown
# Contributing to JARVIS Research OS

Thank you for your interest in contributing to JARVIS Research OS!

## Development Setup

### Prerequisites

- Python 3.10+
- uv (recommended) or pip
- Node.js 20+ (for dashboard development)

### Installation

```bash
# Clone the repository
git clone https://github.com/kaneko-ai/jarvis-ml-pipeline.git
cd jarvis-ml-pipeline

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"
```

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=jarvis_core --cov-report=html

# Specific module
uv run pytest tests/test_evidence_grading.py -v
```

### Code Style

We use `black` for formatting and `ruff` for linting:

```bash
# Format
uv run black jarvis_core tests

# Lint
uv run ruff check jarvis_core tests

# Fix lint issues
uv run ruff check --fix jarvis_core tests
```

## Pull Request Process

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make changes** and add tests
4. **Run tests** and ensure all pass
5. **Format code** with black
6. **Commit** with clear message:
   ```
   feat(module): Add new feature X
   
   - Detailed description
   - Closes #123
   ```
7. **Push** and create Pull Request

## Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

## Code Standards

### Python

- Type hints required for all public functions
- Docstrings in Google style
- Maximum line length: 100 characters
- Test coverage minimum: 80%

### Tests

- One test file per module: `test_{module}.py`
- Use pytest fixtures
- Mock external dependencies
- Include both positive and negative test cases

## Adding New Modules

1. Create module in `jarvis_core/{module_name}/`
2. Add `__init__.py` with public exports
3. Create test file `tests/test_{module_name}.py`
4. Update `pyproject.toml` if new dependencies needed
5. Add documentation in `docs/`

## Reporting Issues

Please include:

- Python version
- OS
- Steps to reproduce
- Expected vs actual behavior
- Error messages/stack traces

## Code of Conduct

Be respectful, inclusive, and constructive.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
```

---

### 2.3 `docs/user_guide.md` の作成 【+1点】

```markdown
# JARVIS Research OS User Guide

## Introduction

JARVIS Research OS is an AI-powered research assistant for systematic literature reviews.

## Quick Start

### Installation

```bash
pip install jarvis-research-os
```

### Basic Usage

```python
from jarvis_core import run_jarvis

result = run_jarvis(
    goal="Systematic review of machine learning in cancer diagnosis",
    category="paper_survey"
)

print(result)
```

## Core Features

### 1. Evidence Grading

Automatically classify research papers by evidence level (CEBM Oxford scale):

- **Level 1a**: Systematic reviews of RCTs
- **Level 1b**: Individual RCTs
- **Level 2**: Cohort studies
- **Level 3**: Case-control studies
- **Level 4**: Case series
- **Level 5**: Expert opinion

### 2. Citation Analysis

Analyze how papers cite each other:

- **Support**: Citation agrees with findings
- **Contrast**: Citation disagrees/contradicts
- **Mention**: Neutral reference

### 3. Contradiction Detection

Identify conflicting claims across papers:

- Direct contradictions (A vs not-A)
- Quantitative contradictions (50% vs 5%)
- Partial contradictions

### 4. PRISMA Flow Diagrams

Generate PRISMA 2020 compliant flow diagrams for systematic reviews.

### 5. Active Learning

Efficiently screen papers using uncertainty sampling to minimize manual labeling effort.

## CLI Commands

```bash
# Search papers
jarvis search "machine learning cancer"

# Run full pipeline
jarvis run --config pipeline.yaml

# Generate PRISMA diagram
jarvis prisma --output prisma.svg

# Interactive screening
jarvis-screen --input papers.jsonl
```

## Configuration

Create `config.yaml`:

```yaml
search:
  sources:
    - pubmed
    - arxiv
    - semantic_scholar
  max_results: 100

embeddings:
  model: all-MiniLM-L6-v2
  device: auto

evidence:
  use_llm: false
  ensemble_strategy: weighted_average

active_learning:
  batch_size: 10
  initial_sample: 20
  stopping_recall: 0.95

offline:
  enabled: true
  cache_dir: ~/.jarvis/cache
```

## Web Dashboard

Start the web server:

```bash
uvicorn jarvis_web.app:app --port 8000
```

Access at: http://localhost:8000

## Best Practices

1. **Start with clear PICO**: Define Population, Intervention, Comparator, Outcome
2. **Use multiple sources**: Don't rely on a single database
3. **Review edge cases**: Check papers with low confidence scores
4. **Export frequently**: Save progress in standard formats (RIS, BibTeX)

## Troubleshooting

### "Model not found" error

```bash
pip install sentence-transformers
```

### Slow search performance

Enable caching:

```yaml
offline:
  enabled: true
  cache_ttl: 86400
```

### Memory issues with large datasets

Use batch processing:

```python
engine.process_batch(papers, batch_size=100)
```

## Support

- GitHub Issues: https://github.com/kaneko-ai/jarvis-ml-pipeline/issues
- Documentation: https://github.com/kaneko-ai/jarvis-ml-pipeline/docs
```

---

## Phase 3: CI/CD強化

### 3.1 `.github/workflows/ci.yml` の更新 【+3点】

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: uv sync --dev
      - name: Run ruff
        run: uv run ruff check jarvis_core tests
      - name: Run black check
        run: uv run black --check jarvis_core tests

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: uv sync --dev
      - name: Run tests with coverage
        run: |
          uv run pytest \
            --cov=jarvis_core \
            --cov-report=xml \
            --cov-report=html \
            --cov-fail-under=80 \
            -v
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage.xml
          fail_ci_if_error: true
      - name: Upload coverage artifact
        uses: actions/upload-artifact@v4
        with:
          name: coverage-${{ matrix.python-version }}
          path: htmlcov/

  contract_and_unit:
    runs-on: ubuntu-latest
    needs: [lint]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: uv sync --dev
      - name: Generate api map
        run: make api-map
      - name: Contract tests
        run: uv run pytest -q tests/test_api_map_vs_capabilities.py tests/test_front_adapter_contract.py

  api_smoke:
    runs-on: ubuntu-latest
    needs: [test]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: uv sync --all-extras
      - name: Start API server
        run: |
          uv run python -m uvicorn jarvis_web.app:app --port 8000 --log-level warning &
          sleep 3
      - name: API smoke tests
        env:
          API_BASE: http://localhost:8000
        run: uv run pytest -q tests/smoke_api_v1.py

  dashboard_e2e_mock:
    runs-on: ubuntu-latest
    needs: [test]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install uv
        run: pip install uv
      - name: Install python dependencies
        run: uv sync --all-extras
      - name: Install node dependencies
        run: npm ci
      - name: Install Playwright browsers
        run: npx playwright install --with-deps
      - name: Start mock server and dashboard
        run: |
          uv run python -m uvicorn tests.mock_server.app:app --port 4010 --log-level warning &
          python -m http.server 4173 -d dashboard &
          sleep 3
      - name: Dashboard E2E (mock)
        env:
          MOCK_API_BASE: http://localhost:4010
          DASHBOARD_BASE_URL: http://localhost:4173
        run: npx playwright test -c tests/e2e/playwright.config.ts
      - name: Upload Playwright artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-results
          path: playwright-results

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install safety
        run: pip install safety
      - name: Check dependencies for vulnerabilities
        run: safety check -r requirements.txt || true
      - name: Run bandit security scan
        run: |
          pip install bandit
          bandit -r jarvis_core -ll -ii

  build:
    runs-on: ubuntu-latest
    needs: [test, lint]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install build tools
        run: pip install build twine
      - name: Build package
        run: python -m build
      - name: Check package
        run: twine check dist/*
      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
```

---

### 3.2 `codecov.yml` の作成 【+1点】

```yaml
codecov:
  require_ci_to_pass: yes

coverage:
  precision: 2
  round: down
  range: "70...100"

  status:
    project:
      default:
        target: 80%
        threshold: 2%
    patch:
      default:
        target: 80%

parsers:
  gcov:
    branch_detection:
      conditional: yes
      loop: yes
      method: no
      macro: no

comment:
  layout: "reach,diff,flags,files,footer"
  behavior: default
  require_changes: no

flags:
  unittests:
    paths:
      - jarvis_core/
    carryforward: true
```

---

### 3.3 `pyproject.toml` 依存関係修正 【+2点】

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "jarvis-research-os"
version = "5.2.0"
description = "JARVIS Research OS - AI-Powered Systematic Literature Review Assistant"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "JARVIS Team", email = "jarvis@kaneko-ai.dev"}
]
keywords = [
    "systematic-review",
    "literature-review",
    "evidence-grading",
    "citation-analysis",
    "PRISMA",
    "active-learning",
    "research-assistant",
    "AI",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Healthcare Industry",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Scientific/Engineering :: Medical Science Apps.",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]

dependencies = [
    "requests>=2.28.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
ml = [
    "lightgbm>=4.0.0",
    "numpy>=1.24.0",
    "scikit-learn>=1.3.0",
]
pdf = [
    "pymupdf>=1.22.0",
    "pypdf2>=3.0",
    "python-docx>=0.8.11",
    "python-pptx>=0.6.21",
    "reportlab>=4.0",
]
llm = [
    "google-generativeai>=0.3.0",
    "llama-cpp-python>=0.2.0",
]
embedding = [
    "sentence-transformers>=2.2.0",
    "rank_bm25>=0.2.2",
]
web = [
    "fastapi>=0.100.0",
    "uvicorn>=0.22.0",
]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
    "safety>=2.3.0",
    "bandit>=1.7.0",
]
all = [
    "jarvis-research-os[ml,pdf,llm,embedding,web]",
]

[dependency-groups]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
]

[project.scripts]
jarvis = "jarvis_cli:main"
jarvis-screen = "jarvis_core.active_learning.cli:cmd_screen"

[project.urls]
Homepage = "https://github.com/kaneko-ai/jarvis-ml-pipeline"
Documentation = "https://github.com/kaneko-ai/jarvis-ml-pipeline/docs"
Repository = "https://github.com/kaneko-ai/jarvis-ml-pipeline"
Issues = "https://github.com/kaneko-ai/jarvis-ml-pipeline/issues"

[tool.setuptools.packages.find]
where = ["."]
include = ["jarvis_core*", "jarvis_tools*", "jarvis_web*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"
asyncio_mode = "auto"

[tool.coverage.run]
source = ["jarvis_core"]
branch = true
omit = [
    "*/tests/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
fail_under = 80

[tool.black]
line-length = 100
target-version = ["py310", "py311", "py312"]

[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "B", "C4", "UP"]
ignore = ["E501"]

[tool.ruff.isort]
known-first-party = ["jarvis_core", "jarvis_web", "jarvis_tools"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

---

### 3.4 `requirements.txt` の削除と `requirements-dev.txt` への置き換え 【+1点】

**削除**: `requirements.txt`

**新規作成**: `requirements-dev.txt`

```
# Development dependencies (use pyproject.toml for production)
# This file is for legacy compatibility only

-e .[all,dev]
```

---

## Phase 4: コード品質向上

### 4.1 型チェック用 `py.typed` マーカー追加 【+1点】

**ファイル作成**: `jarvis_core/py.typed`

```
# PEP 561 marker file
```

---

### 4.2 `jarvis_core/evidence/__init__.py` に英語description追加 【+1点】

```python
"""JARVIS Evidence Grading Module.

Evidence grading and classification for systematic reviews.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.1
"""

from jarvis_core.evidence.schema import (
    EvidenceLevel,
    EvidenceGrade,
    StudyType,
)
from jarvis_core.evidence.rule_classifier import RuleBasedClassifier
from jarvis_core.evidence.llm_classifier import LLMBasedClassifier
from jarvis_core.evidence.ensemble import EnsembleClassifier, grade_evidence

# Add English descriptions
EVIDENCE_LEVEL_DESCRIPTIONS_EN = {
    "1a": "Systematic review of homogeneous RCTs",
    "1b": "Individual RCT with narrow confidence interval",
    "1c": "All or none study",
    "2a": "Systematic review of homogeneous cohort studies",
    "2b": "Individual cohort study",
    "2c": "Outcomes research; ecological studies",
    "3a": "Systematic review of homogeneous case-control studies",
    "3b": "Individual case-control study",
    "4": "Case series",
    "5": "Expert opinion",
    "unknown": "Unknown",
}

__all__ = [
    "EvidenceLevel",
    "EvidenceGrade",
    "StudyType",
    "RuleBasedClassifier",
    "LLMBasedClassifier",
    "EnsembleClassifier",
    "grade_evidence",
    "EVIDENCE_LEVEL_DESCRIPTIONS_EN",
]
```

---

## Phase 5: 機能拡張・高度化

### 5.1 `jarvis_core/contradiction/semantic_detector.py` の作成 【+2点】

```python
"""Semantic Contradiction Detector.

Uses embedding similarity for advanced contradiction detection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from jarvis_core.contradiction.schema import (
    Claim,
    ContradictionResult,
    ContradictionType,
)


@dataclass
class SemanticConfig:
    """Configuration for semantic contradiction detection."""
    
    similarity_threshold: float = 0.7
    contradiction_threshold: float = 0.3
    use_negation_embedding: bool = True
    model_name: str = "all-MiniLM-L6-v2"


class SemanticContradictionDetector:
    """Semantic contradiction detector using embeddings.
    
    Detects contradictions by:
    1. Computing embedding similarity between claims
    2. Checking if negated version of claim A is similar to claim B
    3. Analyzing predicate-argument structure
    """
    
    def __init__(self, config: Optional[SemanticConfig] = None):
        self.config = config or SemanticConfig()
        self._embedder = None
    
    @property
    def embedder(self):
        if self._embedder is None:
            from jarvis_core.embeddings import SentenceTransformerEmbedding
            self._embedder = SentenceTransformerEmbedding(
                model_name=self.config.model_name
            )
        return self._embedder
    
    def detect(self, claim_a: Claim, claim_b: Claim) -> ContradictionResult:
        """Detect contradiction between two claims using semantic analysis."""
        # Get embeddings
        emb_a = self.embedder.embed(claim_a.text)
        emb_b = self.embedder.embed(claim_b.text)
        
        # Compute similarity
        similarity = self._cosine_similarity(emb_a, emb_b)
        
        # Check if claims are about the same topic (high similarity)
        if similarity < self.config.similarity_threshold:
            return ContradictionResult(
                claim_a=claim_a,
                claim_b=claim_b,
                is_contradictory=False,
                contradiction_type=ContradictionType.NONE,
                confidence=1 - similarity,
                scores={"semantic_similarity": similarity},
            )
        
        # Check negation similarity
        if self.config.use_negation_embedding:
            negated_a = self._negate_claim(claim_a.text)
            emb_neg_a = self.embedder.embed(negated_a)
            neg_similarity = self._cosine_similarity(emb_neg_a, emb_b)
            
            if neg_similarity > self.config.similarity_threshold:
                return ContradictionResult(
                    claim_a=claim_a,
                    claim_b=claim_b,
                    is_contradictory=True,
                    contradiction_type=ContradictionType.DIRECT,
                    confidence=neg_similarity,
                    scores={
                        "semantic_similarity": similarity,
                        "negation_similarity": neg_similarity,
                    },
                )
        
        # Check for partial contradiction using predicate analysis
        partial_score = self._check_partial_contradiction(claim_a, claim_b)
        
        if partial_score > self.config.contradiction_threshold:
            return ContradictionResult(
                claim_a=claim_a,
                claim_b=claim_b,
                is_contradictory=True,
                contradiction_type=ContradictionType.PARTIAL,
                confidence=partial_score,
                scores={
                    "semantic_similarity": similarity,
                    "partial_score": partial_score,
                },
            )
        
        return ContradictionResult(
            claim_a=claim_a,
            claim_b=claim_b,
            is_contradictory=False,
            contradiction_type=ContradictionType.NONE,
            confidence=1 - similarity,
            scores={"semantic_similarity": similarity},
        )
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def _negate_claim(self, text: str) -> str:
        """Create negated version of claim text."""
        # Simple negation patterns
        negation_map = {
            "increases": "decreases",
            "decreases": "increases",
            "improves": "worsens",
            "worsens": "improves",
            "effective": "ineffective",
            "significant": "insignificant",
            "positive": "negative",
            "negative": "positive",
        }
        
        negated = text.lower()
        for word, neg_word in negation_map.items():
            if word in negated:
                negated = negated.replace(word, neg_word)
                break
        else:
            # Add "not" if no specific negation found
            negated = f"It is not the case that {text}"
        
        return negated
    
    def _check_partial_contradiction(
        self, claim_a: Claim, claim_b: Claim
    ) -> float:
        """Check for partial contradiction based on predicate analysis."""
        from jarvis_core.contradiction import ClaimNormalizer
        
        normalizer = ClaimNormalizer()
        norm_a = normalizer.normalize(claim_a.text)
        norm_b = normalizer.normalize(claim_b.text)
        
        # Check for opposite predicates
        opposite_predicates = [
            ("increase", "decrease"),
            ("improve", "worsen"),
            ("effective", "ineffective"),
            ("benefit", "harm"),
        ]
        
        for pred_a, pred_b in opposite_predicates:
            if norm_a.predicate and norm_b.predicate:
                if (pred_a in norm_a.predicate.lower() and 
                    pred_b in norm_b.predicate.lower()):
                    return 0.8
                if (pred_b in norm_a.predicate.lower() and 
                    pred_a in norm_b.predicate.lower()):
                    return 0.8
        
        return 0.0
```

---

### 5.2 `jarvis_core/citation/stance_classifier.py` に詳細実装追加 【+2点】

```python
"""Citation Stance Classifier.

Classifies citation stance as Support, Contrast, or Mention.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.2
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Pattern


class CitationStance(Enum):
    """Citation stance types."""
    
    SUPPORT = "support"
    CONTRAST = "contrast"
    MENTION = "mention"


@dataclass
class StanceResult:
    """Result of stance classification."""
    
    stance: CitationStance
    confidence: float
    evidence: str = ""
    scores: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "stance": self.stance.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "scores": self.scores,
        }


class StanceClassifier:
    """Rule-based stance classifier for citation contexts.
    
    Uses pattern matching to identify support, contrast, or neutral mentions.
    """
    
    def __init__(self):
        self._support_patterns = self._build_support_patterns()
        self._contrast_patterns = self._build_contrast_patterns()
    
    def _build_support_patterns(self) -> List[Pattern]:
        """Build regex patterns for support indicators."""
        patterns = [
            r"\b(?:confirm|support|agree|consistent|corroborate|validate)\b",
            r"\b(?:in\s+(?:line|agreement)\s+with)\b",
            r"\b(?:as\s+(?:shown|demonstrated|reported)\s+by)\b",
            r"\b(?:similar\s+(?:to|findings|results))\b",
            r"\b(?:replicate[ds]?|reproduce[ds]?)\b",
            r"\b(?:extend[s]?\s+(?:the\s+)?(?:work|findings))\b",
            r"\b(?:build[s]?\s+(?:on|upon))\b",
            r"\b(?:following|per)\b",
        ]
        return [re.compile(p, re.IGNORECASE) for p in patterns]
    
    def _build_contrast_patterns(self) -> List[Pattern]:
        """Build regex patterns for contrast indicators."""
        patterns = [
            r"\b(?:contradict|conflict|disagree|inconsistent|oppose)\b",
            r"\b(?:in\s+contrast\s+(?:to|with))\b",
            r"\b(?:unlike|contrary\s+to|whereas)\b",
            r"\b(?:however|but|although|despite)\b",
            r"\b(?:different\s+(?:from|than|results))\b",
            r"\b(?:challenge[s]?|question[s]?|dispute[s]?)\b",
            r"\b(?:fail[s]?\s+to\s+(?:replicate|confirm))\b",
            r"\b(?:refute[s]?|disprove[s]?)\b",
            r"\b(?:not\s+(?:support|confirm|agree))\b",
        ]
        return [re.compile(p, re.IGNORECASE) for p in patterns]
    
    def classify(self, context: str) -> StanceResult:
        """Classify citation stance from context text.
        
        Args:
            context: Text surrounding the citation
            
        Returns:
            StanceResult with stance, confidence, and evidence
        """
        if not context or not context.strip():
            return StanceResult(
                stance=CitationStance.MENTION,
                confidence=0.5,
                evidence="",
            )
        
        # Count pattern matches
        support_matches = []
        contrast_matches = []
        
        for pattern in self._support_patterns:
            matches = pattern.findall(context)
            support_matches.extend(matches)
        
        for pattern in self._contrast_patterns:
            matches = pattern.findall(context)
            contrast_matches.extend(matches)
        
        support_score = len(support_matches)
        contrast_score = len(contrast_matches)
        
        # Determine stance
        if support_score > contrast_score and support_score > 0:
            stance = CitationStance.SUPPORT
            confidence = min(0.9, 0.5 + 0.1 * support_score)
            evidence = ", ".join(support_matches[:3])
        elif contrast_score > support_score and contrast_score > 0:
            stance = CitationStance.CONTRAST
            confidence = min(0.9, 0.5 + 0.1 * contrast_score)
            evidence = ", ".join(contrast_matches[:3])
        else:
            stance = CitationStance.MENTION
            confidence = 0.6
            evidence = ""
        
        return StanceResult(
            stance=stance,
            confidence=confidence,
            evidence=evidence,
            scores={
                "support_score": support_score,
                "contrast_score": contrast_score,
            },
        )


def classify_citation_stance(context: str) -> StanceResult:
    """Convenience function to classify citation stance.
    
    Args:
        context: Text surrounding the citation
        
    Returns:
        StanceResult with classification
    """
    classifier = StanceClassifier()
    return classifier.classify(context)
```

---

## Phase 6: セキュリティ・本番対応

### 6.1 `jarvis_web/config.py` CORS設定改善 【+1点】

```python
"""Web application configuration.

Provides environment-aware configuration for the JARVIS web API.
"""

import os
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class CORSConfig:
    """CORS configuration."""
    
    allow_origins: List[str] = field(default_factory=list)
    allow_credentials: bool = True
    allow_methods: List[str] = field(default_factory=lambda: ["*"])
    allow_headers: List[str] = field(default_factory=lambda: ["*"])
    
    @classmethod
    def from_env(cls) -> "CORSConfig":
        """Create CORS config from environment variables."""
        env = os.getenv("JARVIS_ENV", "development")
        
        if env == "production":
            # Production: restrict origins
            origins_str = os.getenv("CORS_ORIGINS", "")
            origins = [o.strip() for o in origins_str.split(",") if o.strip()]
            if not origins:
                origins = ["https://jarvis.kaneko-ai.dev"]
            return cls(allow_origins=origins)
        else:
            # Development: allow all
            return cls(allow_origins=["*"])


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    
    requests_per_minute: int = 100
    authenticated_rpm: int = 1000
    burst_limit: int = 20
    
    @classmethod
    def from_env(cls) -> "RateLimitConfig":
        """Create rate limit config from environment."""
        return cls(
            requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", "100")),
            authenticated_rpm=int(os.getenv("RATE_LIMIT_AUTH_RPM", "1000")),
            burst_limit=int(os.getenv("RATE_LIMIT_BURST", "20")),
        )


@dataclass
class AppConfig:
    """Application configuration."""
    
    env: str = "development"
    debug: bool = False
    cors: CORSConfig = field(default_factory=CORSConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create app config from environment."""
        env = os.getenv("JARVIS_ENV", "development")
        return cls(
            env=env,
            debug=env == "development",
            cors=CORSConfig.from_env(),
            rate_limit=RateLimitConfig.from_env(),
        )


# Global config instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get application configuration (singleton)."""
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config
```

---

### 6.2 `jarvis_web/app.py` CORS修正 【+1点】

**修正箇所** (app.pyの該当部分を置き換え):

```python
# 以下の部分を修正

from jarvis_web.config import get_config

# ...

if FASTAPI_AVAILABLE:
    from jarvis_web.auth import verify_api_token, verify_token
    from jarvis_web.routes.research import router as research_router
    # ... other imports ...

    app = FastAPI(
        title="JARVIS Research OS",
        description="API for paper survey and knowledge synthesis",
        version="5.2.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Get CORS config from environment
    config = get_config()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.allow_origins,
        allow_credentials=config.cors.allow_credentials,
        allow_methods=config.cors.allow_methods,
        allow_headers=config.cors.allow_headers,
    )
    
    # ... rest of app setup ...
```

---

## 検証チェックリスト

### Phase 1: テスト欠落修正
- [ ] `tests/test_prisma.py` が存在し、全テストがパス
- [ ] `tests/test_active_learning.py` が存在し、全テストがパス
- [ ] `tests/test_paper_scoring.py` が存在し、全テストがパス
- [ ] `tests/test_hybrid_search.py` が存在し、全テストがパス
- [ ] `tests/test_network_offline.py` が存在し、全テストがパス

### Phase 2: ドキュメント
- [ ] `docs/api/README.md` が存在し、全APIが文書化
- [ ] `CONTRIBUTING.md` が存在
- [ ] `docs/user_guide.md` が存在

### Phase 3: CI/CD
- [ ] GitHub Actions CIが全て緑
- [ ] Python 3.10, 3.11, 3.12 マトリクスビルド成功
- [ ] カバレッジ80%以上
- [ ] Codecov連携動作
- [ ] セキュリティスキャン (bandit, safety) パス

### Phase 4: コード品質
- [ ] `py.typed` マーカー存在
- [ ] `black --check` パス
- [ ] `ruff check` パス
- [ ] mypy エラーなし（または最小限）

### Phase 5: 機能拡張
- [ ] `SemanticContradictionDetector` 実装完了
- [ ] `StanceClassifier` 詳細実装完了

### Phase 6: セキュリティ
- [ ] CORS設定が環境変数で制御可能
- [ ] OpenAPI/Swagger UI が `/api/docs` でアクセス可能

---

## 期待スコア

| カテゴリ | 現在 | 追加 | 目標 |
|----------|------|------|------|
| テスト欠落修正 | 0 | +7 | 7 |
| ドキュメント | 16 | +3 | 19 |
| CI/CD | 12 | +7 | 19 |
| コード品質 | 16 | +2 | 18 |
| 機能拡張 | 0 | +4 | 4 |
| セキュリティ | 0 | +2 | 2 |
| **合計** | **78** | **+25** | **103** |

**目標達成時評価: A+ (103/100)**

---

## 実行順序

1. **最優先**: Phase 1 全テストファイル作成（CI失敗の原因になる）
2. **高優先**: Phase 3 CI/CD強化（品質ゲート確立）
3. **中優先**: Phase 2 ドキュメント整備
4. **通常**: Phase 4, 5, 6 順次実行