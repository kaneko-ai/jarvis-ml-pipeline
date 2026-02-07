"""TD-028: Evidence grading quality tests.

分類精度を検証するテスト。TD-006 の前提基盤。
既存テストは変更しない。
"""

import pytest

from jarvis_core.evidence.rule_classifier import RuleBasedClassifier
from jarvis_core.evidence.schema import EvidenceLevel, StudyType


@pytest.fixture
def classifier() -> RuleBasedClassifier:
    return RuleBasedClassifier()


class TestMetaAnalysisDetection:
    def test_explicit_meta_analysis(self, classifier: RuleBasedClassifier) -> None:
        grade = classifier.classify(
            title="A meta-analysis of randomized controlled trials on statin therapy",
            abstract="We performed a meta-analysis of 25 RCTs involving 150,000 patients.",
        )
        assert grade.study_type == StudyType.META_ANALYSIS
        assert grade.level == EvidenceLevel.LEVEL_1A

    def test_systematic_review_prisma(self, classifier: RuleBasedClassifier) -> None:
        grade = classifier.classify(
            title="Systematic review of immunotherapy in NSCLC",
            abstract="Following PRISMA guidelines, we systematically reviewed 45 studies.",
        )
        assert grade.study_type == StudyType.SYSTEMATIC_REVIEW

    def test_cochrane_review(self, classifier: RuleBasedClassifier) -> None:
        grade = classifier.classify(
            title="Cochrane review: Interventions for preventing falls",
            abstract="This Cochrane review includes 159 trials.",
        )
        assert grade.study_type == StudyType.SYSTEMATIC_REVIEW


class TestRCTDetection:
    def test_explicit_rct(self, classifier: RuleBasedClassifier) -> None:
        grade = classifier.classify(
            title="A randomized controlled trial of drug X versus placebo",
            abstract="We conducted a double-blind, placebo-controlled RCT.",
        )
        assert grade.study_type == StudyType.RCT

    def test_sample_size_extraction(self, classifier: RuleBasedClassifier) -> None:
        grade = classifier.classify(
            title="RCT of intervention X",
            abstract="We enrolled 1,234 participants in this randomized controlled trial.",
        )
        assert grade.sample_size == 1234


class TestLowerLevelDetection:
    def test_prospective_cohort(self, classifier: RuleBasedClassifier) -> None:
        grade = classifier.classify(
            title="Prospective cohort study of dietary factors",
            abstract="We followed 50,000 participants over 10 years.",
        )
        assert grade.study_type == StudyType.COHORT_PROSPECTIVE

    def test_case_report(self, classifier: RuleBasedClassifier) -> None:
        grade = classifier.classify(
            title="Case report: Rare adverse reaction to drug Y",
            abstract="We present a 45-year-old male.",
        )
        assert grade.study_type == StudyType.CASE_REPORT


class TestEdgeCases:
    def test_empty_input(self, classifier: RuleBasedClassifier) -> None:
        grade = classifier.classify(title="", abstract="")
        assert grade.level == EvidenceLevel.UNKNOWN
        assert grade.confidence == 0.0

    def test_pico_extraction_returns_object(self, classifier: RuleBasedClassifier) -> None:
        pico = classifier.extract_pico(
            "In patients with diabetes, metformin versus placebo. "
            "Primary endpoint was HbA1c reduction."
        )
        assert pico is not None

    def test_confidence_in_valid_range(self, classifier: RuleBasedClassifier) -> None:
        grade = classifier.classify(
            title="Observational study of intervention Z",
            abstract="A retrospective cohort of 1,000 participants was analyzed.",
        )
        assert 0.0 <= grade.confidence <= 1.0
