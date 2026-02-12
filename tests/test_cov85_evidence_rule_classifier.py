"""Coverage tests for jarvis_core.evidence.rule_classifier."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from jarvis_core.evidence.rule_classifier import (
    ClassificationPattern,
    RuleBasedClassifier,
)
from jarvis_core.evidence.schema import EvidenceGrade, EvidenceLevel, StudyType


class TestClassificationPattern:
    def test_fields(self) -> None:
        import re
        pat = ClassificationPattern(
            study_type=StudyType.RCT,
            patterns=[re.compile(r"randomized")],
            weight=1.5,
        )
        assert pat.study_type == StudyType.RCT
        assert pat.weight == 1.5


class TestRuleBasedClassifier:
    def test_init(self) -> None:
        cls = RuleBasedClassifier()
        assert len(cls._patterns) > 0

    def test_classify_rct(self) -> None:
        cls = RuleBasedClassifier()
        result = cls.classify(
            title="A randomized controlled trial of drug X",
            abstract="We conducted a double-blind randomized controlled trial with 200 participants.",
        )
        assert isinstance(result, EvidenceGrade)
        assert result.study_type == StudyType.RCT
        assert result.level == EvidenceLevel.LEVEL_1B

    def test_classify_systematic_review(self) -> None:
        cls = RuleBasedClassifier()
        result = cls.classify(
            title="Systematic review and meta-analysis of interventions",
            abstract="We performed a systematic review and meta-analysis of 42 studies.",
        )
        assert isinstance(result, EvidenceGrade)
        assert result.level == EvidenceLevel.LEVEL_1A
        assert result.study_type in {StudyType.META_ANALYSIS, StudyType.SYSTEMATIC_REVIEW}

    def test_classify_cohort(self) -> None:
        cls = RuleBasedClassifier()
        result = cls.classify(
            title="Prospective cohort study of obesity",
            abstract="This prospective cohort study followed 5000 participants over 10 years.",
        )
        assert isinstance(result, EvidenceGrade)
        assert result.study_type == StudyType.COHORT_PROSPECTIVE
        assert result.level == EvidenceLevel.LEVEL_2B

    def test_classify_case_control(self) -> None:
        cls = RuleBasedClassifier()
        result = cls.classify(
            title="A case-control study of smoking and cancer",
            abstract="We conducted a case-control study comparing 100 cases and 100 controls.",
        )
        assert isinstance(result, EvidenceGrade)
        assert result.study_type == StudyType.CASE_CONTROL
        assert result.level == EvidenceLevel.LEVEL_3B

    def test_classify_case_report(self) -> None:
        cls = RuleBasedClassifier()
        result = cls.classify(
            title="Case report: rare adverse reaction",
            abstract="We report a case of a rare adverse drug reaction.",
        )
        assert isinstance(result, EvidenceGrade)
        assert result.study_type == StudyType.CASE_REPORT
        assert result.level == EvidenceLevel.LEVEL_4

    def test_classify_expert_opinion(self) -> None:
        cls = RuleBasedClassifier()
        result = cls.classify(
            title="Expert commentary on treatment strategies",
            abstract="In this editorial, we present expert opinion on treatment.",
        )
        assert isinstance(result, EvidenceGrade)
        assert result.study_type == StudyType.EXPERT_OPINION
        assert result.level == EvidenceLevel.LEVEL_5

    def test_classify_empty(self) -> None:
        cls = RuleBasedClassifier()
        result = cls.classify(title="", abstract="")
        assert isinstance(result, EvidenceGrade)
        assert result.study_type == StudyType.UNKNOWN
        assert result.level == EvidenceLevel.UNKNOWN
        assert result.confidence == 0.0

    def test_classify_with_full_text(self) -> None:
        cls = RuleBasedClassifier()
        result = cls.classify(
            title="Multi-site study",
            abstract="Clinical trial data",
            full_text="Methods: We enrolled 500 patients in a randomized controlled trial.",
        )
        assert isinstance(result, EvidenceGrade)
        assert result.study_type == StudyType.RCT
        assert result.sample_size == 500

    def test_extract_sample_size(self) -> None:
        cls = RuleBasedClassifier()
        size = cls._extract_sample_size("We enrolled n=500 patients in the study.")
        assert size == 500

    def test_extract_sample_size_alt(self) -> None:
        cls = RuleBasedClassifier()
        size = cls._extract_sample_size("We enrolled 200 participants in the trial")
        assert size == 200

    def test_extract_sample_size_none(self) -> None:
        cls = RuleBasedClassifier()
        size = cls._extract_sample_size("no number here")
        assert size is None

    def test_extract_pico(self) -> None:
        cls = RuleBasedClassifier()
        pico = cls.extract_pico(
            "We enrolled 200 patients with diabetes who received drug X versus placebo "
            "to measure HbA1c reduction."
        )
        assert pico.population is not None
        assert "diabetes" in pico.population.lower()
        assert pico.intervention is not None
        assert "drug x" in pico.intervention.lower()
        assert pico.comparator is not None
        assert "placebo" in pico.comparator.lower()

    def test_extract_population(self) -> None:
        cls = RuleBasedClassifier()
        pop = cls._extract_population("200 patients with hypertension were selected")
        assert pop is not None
        assert "hypertension" in pop.lower()

    def test_extract_intervention(self) -> None:
        cls = RuleBasedClassifier()
        intv = cls._extract_intervention("Patients were treated with drug X")
        assert intv == "drug X"

    def test_extract_comparator(self) -> None:
        cls = RuleBasedClassifier()
        comp = cls._extract_comparator("Drug X was compared with placebo")
        assert comp == "placebo"

    def test_extract_outcome(self) -> None:
        cls = RuleBasedClassifier()
        outcome = cls._extract_outcome("Primary outcome was survival rate")
        assert outcome == "survival rate"

    def test_classify_no_match(self) -> None:
        cls = RuleBasedClassifier()
        result = cls.classify(title="abc def ghi")
        assert result.study_type == StudyType.UNKNOWN

    def test_classify_guideline_variants(self) -> None:
        cls = RuleBasedClassifier()
        assert cls.classify(title="clinical practice guideline").study_type == StudyType.GUIDELINE
        assert cls.classify(title="consensus statement").study_type == StudyType.GUIDELINE

    def test_classify_expert_opinion_variants(self) -> None:
        cls = RuleBasedClassifier()
        assert cls.classify(title="expert opinion").study_type == StudyType.EXPERT_OPINION
        assert cls.classify(title="editorial").study_type == StudyType.EXPERT_OPINION
        assert cls.classify(title="commentary").study_type == StudyType.EXPERT_OPINION

    def test_extract_sample_size_value_error(self) -> None:
        cls = RuleBasedClassifier()
        with patch.object(cls, "_sample_size_pattern") as mock_pat:
            mock_match = MagicMock()
            mock_match.group.return_value = "invalid_int"
            mock_pat.search.return_value = mock_match
            assert cls._extract_sample_size("test") is None

    def test_extract_pico_variants(self) -> None:
        cls = RuleBasedClassifier()
        text = "Patients were treated with drug X. Versus placebo. Outcome measure: death."
        pico = cls.extract_pico(text)
        assert pico.intervention == "drug X"
        assert pico.comparator == "placebo"

    def test_extract_pico_outcome_alt(self) -> None:
        cls = RuleBasedClassifier()
        text = "main outcome measure was blood pressure"
        pico = cls.extract_pico(text)
        assert pico.outcome == "blood pressure"

