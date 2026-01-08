"""Tests for PRISMA Generator and Active Learning.

Tests for Task 2.4-2.5
"""


class TestPRISMAGenerator:
    """Tests for PRISMA flow diagram generator."""

    def test_prisma_stats_dataclass(self):
        """Test PRISMAStats dataclass."""
        from jarvis_core.reporting.prisma_generator import PRISMAStats

        stats = PRISMAStats(
            records_identified_database=1000,
            records_identified_other=50,
            records_removed_duplicates=100,
        )

        assert stats.records_identified_database == 1000
        assert stats.records_removed_duplicates == 100

    def test_calculate_totals(self):
        """Test statistics calculation."""
        from jarvis_core.reporting.prisma_generator import PRISMAStats

        stats = PRISMAStats(
            records_identified_database=1000,
            records_identified_other=50,
            records_removed_duplicates=100,
            records_excluded_title_abstract=500,
        )
        stats.calculate_totals()

        assert stats.records_screened == 950  # 1050 - 100
        assert stats.reports_sought == 450  # 950 - 500

    def test_prisma_diagram_dataclass(self):
        """Test PRISMADiagram dataclass."""
        from jarvis_core.reporting.prisma_generator import PRISMADiagram, PRISMAStats

        stats = PRISMAStats()
        diagram = PRISMADiagram(
            title="Test Review",
            date="2026-01-06",
            stats=stats,
            databases_searched=["PubMed"],
        )

        d = diagram.to_dict()
        assert d["title"] == "Test Review"
        assert "stats" in d

    def test_generator_generate(self):
        """Test diagram generation."""
        from jarvis_core.reporting.prisma_generator import PRISMAGenerator, PRISMAStats

        generator = PRISMAGenerator()
        stats = PRISMAStats(
            records_identified_database=500,
            records_removed_duplicates=50,
        )

        diagram = generator.generate(stats, "My Review")

        assert diagram.title == "My Review"
        assert len(diagram.databases_searched) > 0

    def test_to_markdown(self):
        """Test Markdown output."""
        from jarvis_core.reporting.prisma_generator import PRISMAGenerator, PRISMAStats

        generator = PRISMAGenerator()
        stats = PRISMAStats(
            records_identified_database=100,
            records_identified_other=10,
            records_removed_duplicates=15,
            records_excluded_title_abstract=30,
            studies_included_review=20,
        )

        diagram = generator.generate(stats, "Test")
        md = generator.to_markdown(diagram)

        assert "# PRISMA 2020 Flow Diagram" in md
        assert "Test" in md

    def test_to_mermaid(self):
        """Test Mermaid output."""
        from jarvis_core.reporting.prisma_generator import PRISMAGenerator, PRISMAStats

        generator = PRISMAGenerator()
        stats = PRISMAStats(
            records_identified_database=100,
            studies_included_review=10,
        )

        diagram = generator.generate(stats)
        mermaid = generator.to_mermaid(diagram)

        assert "flowchart TD" in mermaid
        assert "Identification" in mermaid

    def test_from_pipeline_results(self):
        """Test generation from pipeline results."""
        from jarvis_core.reporting.prisma_generator import PRISMAGenerator

        generator = PRISMAGenerator()

        search_results = [{"id": i, "doi": f"10.{i}/test"} for i in range(100)]
        screened_results = [{"id": i} for i in range(50)]
        included_results = [{"id": i} for i in range(20)]

        diagram = generator.from_pipeline_results(
            search_results, screened_results, included_results
        )

        assert diagram.stats.records_identified_database == 100
        assert diagram.stats.studies_included_review == 20

    def test_generate_prisma_function(self):
        """Test convenience function."""
        from jarvis_core.reporting.prisma_generator import generate_prisma

        output = generate_prisma(
            search_results=[{"id": 1}],
            screened_results=[{"id": 1}],
            included_results=[{"id": 1}],
            output_format="markdown",
        )

        assert "PRISMA" in output


class TestActiveLearning:
    """Tests for Active Learning system."""

    def test_sampling_strategy_enum(self):
        """Test SamplingStrategy enum."""
        from jarvis_core.learning.active_learning import SamplingStrategy

        assert SamplingStrategy.UNCERTAINTY.value == "uncertainty"
        assert SamplingStrategy.COMBINED.value == "combined"

    def test_label_enum(self):
        """Test Label enum."""
        from jarvis_core.learning.active_learning import Label

        assert Label.INCLUDE.value == "include"
        assert Label.EXCLUDE.value == "exclude"

    def test_labeled_sample_dataclass(self):
        """Test LabeledSample dataclass."""
        from jarvis_core.learning.active_learning import Label, LabeledSample

        sample = LabeledSample(
            sample_id="s1",
            text="Test text",
        )

        assert not sample.is_labeled

        sample.label = Label.INCLUDE
        assert sample.is_labeled

    def test_active_learning_state(self):
        """Test ActiveLearningState dataclass."""
        from jarvis_core.learning.active_learning import ActiveLearningState

        state = ActiveLearningState(
            total_samples=100,
            labeled_count=20,
            include_count=15,
            exclude_count=5,
        )

        assert state.total_samples == 100
        assert state.estimated_remaining == 0  # default

    def test_uncertainty_sampler_heuristic(self):
        """Test uncertainty sampling heuristics."""
        from jarvis_core.learning.active_learning import UncertaintySampler

        sampler = UncertaintySampler()

        # Clear inclusion text should have lower uncertainty
        clear_include = "The study demonstrated significant effects"
        clear_exclude = "The study failed to find any effect"
        ambiguous = "The study examined various factors"

        u_include = sampler.get_uncertainty(clear_include)
        u_exclude = sampler.get_uncertainty(clear_exclude)
        u_ambiguous = sampler.get_uncertainty(ambiguous)

        assert u_ambiguous > u_include or u_ambiguous > u_exclude

    def test_active_learner_init(self):
        """Test ActiveLearner initialization."""
        from jarvis_core.learning.active_learning import ActiveLearner

        samples = [
            {"id": "1", "text": "Sample one"},
            {"id": "2", "text": "Sample two"},
        ]

        learner = ActiveLearner(samples)

        state = learner.get_state()
        assert state.total_samples == 2
        assert state.labeled_count == 0

    def test_get_next_batch(self):
        """Test getting next batch for labeling."""
        from jarvis_core.learning.active_learning import ActiveLearner

        samples = [{"id": str(i), "text": f"Sample {i}"} for i in range(20)]
        learner = ActiveLearner(samples, batch_size=5)

        batch = learner.get_next_batch()

        assert len(batch) == 5
        assert all(not s.is_labeled for s in batch)

    def test_submit_labels(self):
        """Test submitting labels."""
        from jarvis_core.learning.active_learning import ActiveLearner, Label

        samples = [{"id": str(i), "text": f"Sample {i}"} for i in range(10)]
        learner = ActiveLearner(samples)

        # Submit some labels
        labels = [
            ("0", Label.INCLUDE, "Good paper"),
            ("1", Label.EXCLUDE, "Not relevant"),
        ]

        applied = learner.submit_labels(labels)

        assert applied == 2

        state = learner.get_state()
        assert state.labeled_count == 2
        assert state.include_count == 1
        assert state.exclude_count == 1

    def test_get_labeled_samples(self):
        """Test getting labeled samples."""
        from jarvis_core.learning.active_learning import ActiveLearner, Label

        samples = [{"id": str(i), "text": f"Sample {i}"} for i in range(5)]
        learner = ActiveLearner(samples)

        learner.submit_labels([
            ("0", Label.INCLUDE, None),
            ("1", Label.INCLUDE, None),
            ("2", Label.EXCLUDE, None),
        ])

        included, excluded = learner.get_labeled_samples()

        assert len(included) == 2
        assert len(excluded) == 1

    def test_should_continue(self):
        """Test continuation check."""
        from jarvis_core.learning.active_learning import ActiveLearner, Label

        samples = [{"id": str(i), "text": f"Sample {i}"} for i in range(10)]
        learner = ActiveLearner(samples)

        assert learner.should_continue() is True

        # Label all samples
        for s in learner.samples:
            s.label = Label.INCLUDE

        assert learner.should_continue() is False

    def test_create_active_learner_function(self):
        """Test convenience function."""
        from jarvis_core.learning.active_learning import create_active_learner

        samples = [{"id": "1", "text": "Test"}]
        learner = create_active_learner(samples, strategy="uncertainty")

        assert learner is not None
        assert learner.get_state().total_samples == 1


class TestPhase2Complete:
    """Integration tests for complete Phase 2."""

    def test_all_phase2_modules(self):
        """Test all Phase 2 modules import."""
        from jarvis_core.analysis.citation_stance import analyze_citations
        from jarvis_core.analysis.contradiction_detector import detect_contradictions
        from jarvis_core.analysis.grade_system import EnsembleGrader
        from jarvis_core.learning.active_learning import create_active_learner
        from jarvis_core.reporting.prisma_generator import generate_prisma

        assert EnsembleGrader is not None
        assert analyze_citations is not None
        assert detect_contradictions is not None
        assert generate_prisma is not None
        assert create_active_learner is not None
