"""Tests for the Evidence Grading Module.

Per JARVIS_COMPLETION_PLAN_v3 Task 2.1
"""


class TestEvidenceSchema:
    """Tests for evidence schema."""

    def test_evidence_level_enum(self):
        """Test EvidenceLevel enum values."""
        from jarvis_core.evidence.schema import EvidenceLevel

        assert EvidenceLevel.LEVEL_1A.value == "1a"
        assert EvidenceLevel.LEVEL_1B.value == "1b"
        assert EvidenceLevel.LEVEL_4.value == "4"
        assert EvidenceLevel.LEVEL_5.value == "5"

    def test_evidence_level_ranking(self):
        """Test evidence level ranking."""
        from jarvis_core.evidence.schema import EvidenceLevel

        # Level 1a should be higher (lower numeric rank) than Level 5
        assert EvidenceLevel.LEVEL_1A.numeric_rank < EvidenceLevel.LEVEL_5.numeric_rank
        assert EvidenceLevel.LEVEL_1B.numeric_rank < EvidenceLevel.LEVEL_2A.numeric_rank

    def test_evidence_level_description(self):
        """Test evidence level descriptions."""
        from jarvis_core.evidence.schema import EvidenceLevel

        assert "系統的レビュー" in EvidenceLevel.LEVEL_1A.description
        assert "RCT" in EvidenceLevel.LEVEL_1B.description
        assert "専門家" in EvidenceLevel.LEVEL_5.description

    def test_study_type_default_level(self):
        """Test study type to default evidence level mapping."""
        from jarvis_core.evidence.schema import EvidenceLevel, StudyType

        assert StudyType.SYSTEMATIC_REVIEW.default_evidence_level == EvidenceLevel.LEVEL_1A
        assert StudyType.RCT.default_evidence_level == EvidenceLevel.LEVEL_1B
        assert StudyType.CASE_CONTROL.default_evidence_level == EvidenceLevel.LEVEL_3B
        assert StudyType.CASE_SERIES.default_evidence_level == EvidenceLevel.LEVEL_4
        assert StudyType.EXPERT_OPINION.default_evidence_level == EvidenceLevel.LEVEL_5

    def test_evidence_grade_dataclass(self):
        """Test EvidenceGrade dataclass."""
        from jarvis_core.evidence.schema import EvidenceGrade, EvidenceLevel, StudyType

        grade = EvidenceGrade(
            level=EvidenceLevel.LEVEL_1B,
            study_type=StudyType.RCT,
            confidence=0.85,
            sample_size=100,
        )

        assert grade.level == EvidenceLevel.LEVEL_1B
        assert grade.study_type == StudyType.RCT
        assert grade.confidence == 0.85
        assert grade.sample_size == 100

    def test_evidence_grade_to_dict(self):
        """Test EvidenceGrade serialization."""
        from jarvis_core.evidence.schema import EvidenceGrade, EvidenceLevel, StudyType

        grade = EvidenceGrade(
            level=EvidenceLevel.LEVEL_1B,
            study_type=StudyType.RCT,
            confidence=0.85,
        )

        data = grade.to_dict()
        assert data["level"] == "1b"
        assert data["study_type"] == "randomized_controlled_trial"
        assert data["confidence"] == 0.85

    def test_pico_extraction_dataclass(self):
        """Test PICOExtraction dataclass."""
        from jarvis_core.evidence.schema import PICOExtraction

        pico = PICOExtraction(
            population="Adults with diabetes",
            intervention="Metformin",
            comparator="Placebo",
            outcome="HbA1c reduction",
        )

        assert pico.is_complete() == True

        incomplete_pico = PICOExtraction(population="Adults")
        assert incomplete_pico.is_complete() == False


class TestRuleBasedClassifier:
    """Tests for rule-based classifier."""

    def test_classifier_init(self):
        """Test classifier initialization."""
        from jarvis_core.evidence.rule_classifier import RuleBasedClassifier

        classifier = RuleBasedClassifier()
        assert classifier is not None

    def test_classify_rct(self):
        """Test RCT classification."""
        from jarvis_core.evidence.rule_classifier import RuleBasedClassifier
        from jarvis_core.evidence.schema import EvidenceLevel, StudyType

        classifier = RuleBasedClassifier()

        grade = classifier.classify(
            title="A randomized controlled trial of aspirin for cardiovascular prevention",
            abstract="Methods: We enrolled 1000 patients in a double-blind, placebo-controlled trial.",
        )

        assert grade.study_type == StudyType.RCT
        assert grade.level == EvidenceLevel.LEVEL_1B
        assert grade.confidence > 0.5

    def test_classify_systematic_review(self):
        """Test systematic review classification."""
        from jarvis_core.evidence.rule_classifier import RuleBasedClassifier
        from jarvis_core.evidence.schema import EvidenceLevel, StudyType

        classifier = RuleBasedClassifier()

        grade = classifier.classify(
            title="A systematic review and meta-analysis of statin therapy",
            abstract="We searched PubMed, Cochrane Library, and EMBASE following PRISMA guidelines.",
        )

        assert grade.study_type in [StudyType.SYSTEMATIC_REVIEW, StudyType.META_ANALYSIS]
        assert grade.level == EvidenceLevel.LEVEL_1A

    def test_classify_cohort(self):
        """Test cohort study classification."""
        from jarvis_core.evidence.rule_classifier import RuleBasedClassifier
        from jarvis_core.evidence.schema import StudyType

        classifier = RuleBasedClassifier()

        grade = classifier.classify(
            title="A prospective cohort study of diet and cancer risk",
            abstract="We followed 50,000 participants for 10 years.",
        )

        assert grade.study_type == StudyType.COHORT_PROSPECTIVE
        assert grade.confidence > 0.5

    def test_classify_case_control(self):
        """Test case-control study classification."""
        from jarvis_core.evidence.rule_classifier import RuleBasedClassifier
        from jarvis_core.evidence.schema import StudyType

        classifier = RuleBasedClassifier()

        grade = classifier.classify(
            title="A case-control study of smoking and lung cancer",
            abstract="Cases were matched with controls from the same hospital.",
        )

        assert grade.study_type == StudyType.CASE_CONTROL

    def test_extract_sample_size(self):
        """Test sample size extraction."""
        from jarvis_core.evidence.rule_classifier import RuleBasedClassifier

        classifier = RuleBasedClassifier()

        # Test cases with study type keywords so classification succeeds
        test_cases = [
            ("This randomized controlled trial enrolled 1,000 patients", 1000),
            ("In this RCT, n = 500", 500),
            ("This prospective cohort study recruited 250 subjects", 250),
        ]

        for text, expected in test_cases:
            grade = classifier.classify(abstract=text)
            assert grade.sample_size == expected, f"Failed for: {text}"

    def test_classify_unknown(self):
        """Test classification of unknown text."""
        from jarvis_core.evidence.rule_classifier import RuleBasedClassifier
        from jarvis_core.evidence.schema import EvidenceLevel

        classifier = RuleBasedClassifier()

        grade = classifier.classify(
            title="Some generic paper about science",
            abstract="This paper discusses various topics.",
        )

        assert grade.level == EvidenceLevel.UNKNOWN or grade.confidence < 0.5

    def test_pico_extraction(self):
        """Test PICO extraction."""
        from jarvis_core.evidence.rule_classifier import RuleBasedClassifier

        classifier = RuleBasedClassifier()

        abstract = """
        This randomized trial included patients with type 2 diabetes.
        Participants received metformin 500mg twice daily compared to placebo.
        The primary endpoint was HbA1c reduction at 12 months.
        """

        pico = classifier.extract_pico(abstract)

        # At least population or intervention should be extracted
        assert pico.population or pico.intervention or pico.comparator


class TestEnsembleClassifier:
    """Tests for ensemble classifier."""

    def test_ensemble_init(self):
        """Test ensemble classifier initialization."""
        from jarvis_core.evidence.ensemble import EnsembleClassifier, EnsembleConfig

        config = EnsembleConfig(use_llm=False)
        classifier = EnsembleClassifier(config=config)
        assert classifier is not None

    def test_ensemble_classify_without_llm(self):
        """Test ensemble classification without LLM."""
        from jarvis_core.evidence.ensemble import EnsembleClassifier, EnsembleConfig
        from jarvis_core.evidence.schema import EvidenceLevel

        config = EnsembleConfig(use_llm=False)
        classifier = EnsembleClassifier(config=config)

        grade = classifier.classify(
            title="A randomized controlled trial",
            abstract="We conducted a double-blind RCT with n=500 patients.",
        )

        assert grade.level == EvidenceLevel.LEVEL_1B
        assert "rule" in grade.classifier_source

    def test_grade_evidence_function(self):
        """Test convenience function."""
        from jarvis_core.evidence import grade_evidence
        from jarvis_core.evidence.schema import EvidenceLevel

        grade = grade_evidence(
            title="A systematic review of cancer treatment",
            abstract="We followed PRISMA guidelines and included 50 RCTs.",
            use_llm=False,
        )

        assert grade.level == EvidenceLevel.LEVEL_1A
        assert grade.confidence > 0


class TestModuleImports:
    """Test module imports."""

    def test_main_imports(self):
        """Test main module imports."""
        from jarvis_core.evidence import (
            EnsembleClassifier,
            EvidenceGrade,
            EvidenceLevel,
            RuleBasedClassifier,
            StudyType,
            grade_evidence,
        )

        assert EvidenceLevel is not None
        assert EvidenceGrade is not None
        assert StudyType is not None
        assert RuleBasedClassifier is not None
        assert EnsembleClassifier is not None
        assert grade_evidence is not None
