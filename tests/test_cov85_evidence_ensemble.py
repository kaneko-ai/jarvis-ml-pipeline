"""Coverage tests for jarvis_core.evidence.ensemble."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from jarvis_core.evidence.ensemble import (
    EnsembleClassifier,
    EnsembleConfig,
    EnsembleStrategy,
    grade_evidence,
)
from jarvis_core.evidence.schema import EvidenceGrade, EvidenceLevel, StudyType


def _make_grade(
    level: EvidenceLevel = EvidenceLevel.LEVEL_2A,
    confidence: float = 0.8,
    study_type: StudyType = StudyType.COHORT_RETROSPECTIVE,
):
    return EvidenceGrade(
        level=level,
        study_type=study_type,
        confidence=confidence,
        classifier_source="test",
    )


class TestEnsembleConfig:
    def test_defaults(self) -> None:
        cfg = EnsembleConfig()
        assert cfg.strategy == EnsembleStrategy.WEIGHTED_AVERAGE
        assert cfg.use_llm is True

    def test_custom(self) -> None:
        cfg = EnsembleConfig(strategy=EnsembleStrategy.VOTING, use_llm=False)
        assert cfg.strategy == EnsembleStrategy.VOTING


class TestEnsembleClassifier:
    def test_no_llm(self) -> None:
        cfg = EnsembleConfig(use_llm=False)
        classifier = EnsembleClassifier(config=cfg)
        assert classifier._llm_classifier is None

    def test_classify_rule_only(self) -> None:
        cfg = EnsembleConfig(use_llm=False)
        classifier = EnsembleClassifier(config=cfg)
        result = classifier.classify(title="A randomized controlled trial of X")
        assert result.classifier_source == "ensemble_rule_only"
        assert result.study_type == StudyType.RCT

    def test_classify_llm_failure(self) -> None:
        cfg = EnsembleConfig(use_llm=True)
        with patch("jarvis_core.evidence.ensemble.LLMBasedClassifier") as MockLLM:
            MockLLM.return_value.classify.side_effect = Exception("LLM fail")
            classifier = EnsembleClassifier(config=cfg)
            result = classifier.classify(title="A systematic review")
        assert result.classifier_source == "ensemble_rule_only"
        assert result.level == EvidenceLevel.LEVEL_1A


class TestCombineResults:
    def test_no_llm_grade(self) -> None:
        cfg = EnsembleConfig(use_llm=False)
        classifier = EnsembleClassifier(config=cfg)
        rule = _make_grade(EvidenceLevel.LEVEL_1B, 0.9)
        result = classifier._combine_results(rule, None)
        assert result.classifier_source == "ensemble_rule_only"

    def test_llm_unknown(self) -> None:
        cfg = EnsembleConfig(use_llm=False)
        classifier = EnsembleClassifier(config=cfg)
        rule = _make_grade(EvidenceLevel.LEVEL_2A, 0.8)
        llm = _make_grade(EvidenceLevel.UNKNOWN, 0.3)
        result = classifier._combine_results(rule, llm)
        assert result.classifier_source == "ensemble_rule_only"

    def test_rule_unknown(self) -> None:
        cfg = EnsembleConfig(use_llm=False)
        classifier = EnsembleClassifier(config=cfg)
        rule = _make_grade(EvidenceLevel.UNKNOWN, 0.2)
        llm = _make_grade(EvidenceLevel.LEVEL_1A, 0.9)
        result = classifier._combine_results(rule, llm)
        assert result.classifier_source == "ensemble_llm_only"


class TestWeightedAverage:
    def test_rule_higher(self) -> None:
        cfg = EnsembleConfig(rule_weight=0.7, llm_weight=0.3)
        classifier = EnsembleClassifier(config=cfg)
        rule = _make_grade(EvidenceLevel.LEVEL_1B, 0.9)
        llm = _make_grade(EvidenceLevel.LEVEL_2A, 0.5)
        result = classifier._weighted_average(rule, llm)
        assert result.classifier_source == "ensemble_weighted"
        assert result.level == EvidenceLevel.LEVEL_1B

    def test_llm_higher(self) -> None:
        cfg = EnsembleConfig(rule_weight=0.3, llm_weight=0.7)
        classifier = EnsembleClassifier(config=cfg)
        rule = _make_grade(EvidenceLevel.LEVEL_2A, 0.4)
        llm = _make_grade(EvidenceLevel.LEVEL_1A, 0.9)
        result = classifier._weighted_average(rule, llm)
        assert result.level == EvidenceLevel.LEVEL_1A
        assert result.classifier_source == "ensemble_weighted"
        assert abs(result.confidence - 0.75) < 1e-9
        assert result.raw_scores["rule_confidence"] == 0.4
        assert result.raw_scores["llm_confidence"] == 0.9


class TestVoting:
    def test_agreement(self) -> None:
        cfg = EnsembleConfig(strategy=EnsembleStrategy.VOTING)
        classifier = EnsembleClassifier(config=cfg)
        rule = _make_grade(EvidenceLevel.LEVEL_2A, 0.8)
        llm = _make_grade(EvidenceLevel.LEVEL_2A, 0.9)
        result = classifier._voting(rule, llm)
        assert result.classifier_source == "ensemble_agreement"
        assert result.confidence == 0.9

    def test_disagreement_rule_higher(self) -> None:
        cfg = EnsembleConfig(strategy=EnsembleStrategy.VOTING)
        classifier = EnsembleClassifier(config=cfg)
        rule = _make_grade(EvidenceLevel.LEVEL_1B, 0.9)
        llm = _make_grade(EvidenceLevel.LEVEL_3A, 0.5)
        result = classifier._voting(rule, llm)
        assert result.classifier_source == "ensemble_disagreement"
        assert result.level == EvidenceLevel.LEVEL_1B

    def test_disagreement_llm_higher(self) -> None:
        cfg = EnsembleConfig(strategy=EnsembleStrategy.VOTING)
        classifier = EnsembleClassifier(config=cfg)
        rule = _make_grade(EvidenceLevel.LEVEL_3A, 0.3)
        llm = _make_grade(EvidenceLevel.LEVEL_1B, 0.9)
        result = classifier._voting(rule, llm)
        assert result.level == EvidenceLevel.LEVEL_1B


class TestConfidenceBased:
    def test_rule_higher(self) -> None:
        cfg = EnsembleConfig()
        classifier = EnsembleClassifier(config=cfg)
        rule = _make_grade(EvidenceLevel.LEVEL_1B, 0.9)
        llm = _make_grade(EvidenceLevel.LEVEL_2A, 0.5)
        result = classifier._confidence_based(rule, llm)
        assert result.classifier_source == "ensemble_rule_higher"

    def test_llm_higher(self) -> None:
        cfg = EnsembleConfig()
        classifier = EnsembleClassifier(config=cfg)
        rule = _make_grade(EvidenceLevel.LEVEL_2A, 0.4)
        llm = _make_grade(EvidenceLevel.LEVEL_1A, 0.9)
        result = classifier._confidence_based(rule, llm)
        assert result.classifier_source == "ensemble_llm_higher"


class TestRuleFirst:
    def test_rule_confident(self) -> None:
        cfg = EnsembleConfig(confidence_threshold=0.7)
        classifier = EnsembleClassifier(config=cfg)
        rule = _make_grade(EvidenceLevel.LEVEL_1B, 0.9)
        llm = _make_grade(EvidenceLevel.LEVEL_2A, 0.8)
        result = classifier._rule_first(rule, llm)
        assert result.classifier_source == "ensemble_rule_primary"

    def test_rule_low_confidence(self) -> None:
        cfg = EnsembleConfig(confidence_threshold=0.9)
        classifier = EnsembleClassifier(config=cfg)
        rule = _make_grade(EvidenceLevel.LEVEL_3A, 0.5)
        llm = _make_grade(EvidenceLevel.LEVEL_2A, 0.8)
        result = classifier._rule_first(rule, llm)
        assert result.classifier_source == "ensemble_llm_fallback"


class TestLLMFirst:
    def test_llm_confident(self) -> None:
        cfg = EnsembleConfig(confidence_threshold=0.7)
        classifier = EnsembleClassifier(config=cfg)
        rule = _make_grade(EvidenceLevel.LEVEL_2A, 0.8)
        llm = _make_grade(EvidenceLevel.LEVEL_1A, 0.9)
        result = classifier._llm_first(rule, llm)
        assert result.classifier_source == "ensemble_llm_primary"

    def test_llm_low_confidence(self) -> None:
        cfg = EnsembleConfig(confidence_threshold=0.9)
        classifier = EnsembleClassifier(config=cfg)
        rule = _make_grade(EvidenceLevel.LEVEL_2A, 0.8)
        llm = _make_grade(EvidenceLevel.LEVEL_1A, 0.5)
        result = classifier._llm_first(rule, llm)
        assert result.classifier_source == "ensemble_rule_fallback"


class TestLevelScore:
    def test_all_levels(self) -> None:
        assert EnsembleClassifier._level_score(EvidenceLevel.LEVEL_1A) < EnsembleClassifier._level_score(
            EvidenceLevel.LEVEL_5
        )
        assert EnsembleClassifier._level_score(EvidenceLevel.UNKNOWN) == 99.0


class TestGradeEvidence:
    def test_no_llm(self) -> None:
        result = grade_evidence(
            title="A case report of X",
            abstract="We present a case...",
            use_llm=False,
        )
        assert isinstance(result, EvidenceGrade)
        assert result.classifier_source == "ensemble_rule_only"
        assert result.study_type == StudyType.CASE_REPORT

    def test_with_strategy(self) -> None:
        result = grade_evidence(
            title="A randomized controlled trial",
            use_llm=False,
            strategy=EnsembleStrategy.RULE_FIRST,
        )
        assert isinstance(result, EvidenceGrade)
        assert result.classifier_source == "ensemble_rule_only"
        assert result.study_type == StudyType.RCT
