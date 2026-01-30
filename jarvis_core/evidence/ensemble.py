"""Ensemble Evidence Classifier.

Combines rule-based and LLM-based classifiers.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.1 Ensemble
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

from jarvis_core.evidence.llm_classifier import LLMBasedClassifier, LLMConfig
from jarvis_core.evidence.rule_classifier import RuleBasedClassifier
from jarvis_core.evidence.schema import (
    EvidenceGrade,
    EvidenceLevel,
)

logger = logging.getLogger(__name__)


class EnsembleStrategy(Enum):
    """Strategy for combining classifier results."""

    WEIGHTED_AVERAGE = "weighted_average"
    VOTING = "voting"
    CONFIDENCE_BASED = "confidence_based"
    RULE_FIRST = "rule_first"  # Use rule, fall back to LLM
    LLM_FIRST = "llm_first"  # Use LLM, fall back to rule


@dataclass
class EnsembleConfig:
    """Configuration for ensemble classifier."""

    strategy: EnsembleStrategy = EnsembleStrategy.WEIGHTED_AVERAGE
    rule_weight: float = 0.4
    llm_weight: float = 0.6
    confidence_threshold: float = 0.8
    require_agreement: bool = False
    use_llm: bool = True  # Set to False for offline mode


class EnsembleClassifier:
    """Ensemble classifier combining rule-based and LLM classifiers.

    Supports multiple combination strategies:
    - WEIGHTED_AVERAGE: Weighted combination of confidence scores
    - VOTING: Majority vote (requires agreement)
    - CONFIDENCE_BASED: Use highest confidence result
    - RULE_FIRST: Use rule-based, fall back to LLM if low confidence
    - LLM_FIRST: Use LLM, fall back to rule-based if unavailable

    Example:
        >>> classifier = EnsembleClassifier()
        >>> grade = classifier.classify(
        ...     title="A randomized controlled trial of...",
        ...     abstract="Methods: We conducted a double-blind RCT..."
        ... )
        >>> print(grade.level)
        EvidenceLevel.LEVEL_1B
    """

    def __init__(
        self,
        config: EnsembleConfig | None = None,
        llm_config: LLMConfig | None = None,
    ):
        """Initialize the ensemble classifier.

        Args:
            config: Ensemble configuration
            llm_config: LLM configuration
        """
        self._config = config or EnsembleConfig()

        self._rule_classifier = RuleBasedClassifier()
        self._llm_classifier = LLMBasedClassifier(llm_config) if self._config.use_llm else None

    def classify(
        self,
        title: str = "",
        abstract: str = "",
        full_text: str = "",
    ) -> EvidenceGrade:
        """Classify evidence level using ensemble.

        Args:
            title: Paper title
            abstract: Paper abstract
            full_text: Full paper text (optional)

        Returns:
            EvidenceGrade with classification result
        """
        # Get rule-based classification
        rule_grade = self._rule_classifier.classify(title, abstract, full_text)

        # Get LLM classification if enabled
        llm_grade = None
        if self._llm_classifier:
            try:
                llm_grade = self._llm_classifier.classify(title, abstract, full_text)
            except Exception as e:
                logger.warning(f"LLM classification failed: {e}")

        # Combine results based on strategy
        return self._combine_results(rule_grade, llm_grade)

    def _combine_results(
        self,
        rule_grade: EvidenceGrade,
        llm_grade: EvidenceGrade | None,
    ) -> EvidenceGrade:
        """Combine classifier results based on strategy."""
        strategy = self._config.strategy

        # Handle missing LLM result
        if llm_grade is None or llm_grade.level == EvidenceLevel.UNKNOWN:
            rule_grade.classifier_source = "ensemble_rule_only"
            return rule_grade

        # Handle missing rule result
        if rule_grade.level == EvidenceLevel.UNKNOWN:
            llm_grade.classifier_source = "ensemble_llm_only"
            return llm_grade

        if strategy == EnsembleStrategy.RULE_FIRST:
            return self._rule_first(rule_grade, llm_grade)
        elif strategy == EnsembleStrategy.LLM_FIRST:
            return self._llm_first(rule_grade, llm_grade)
        elif strategy == EnsembleStrategy.VOTING:
            return self._voting(rule_grade, llm_grade)
        elif strategy == EnsembleStrategy.CONFIDENCE_BASED:
            return self._confidence_based(rule_grade, llm_grade)
        else:
            return self._weighted_average(rule_grade, llm_grade)

    def _weighted_average(
        self,
        rule_grade: EvidenceGrade,
        llm_grade: EvidenceGrade,
    ) -> EvidenceGrade:
        """Weighted average strategy."""
        rule_weight = self._config.rule_weight
        llm_weight = self._config.llm_weight

        # Normalize weights
        total = rule_weight + llm_weight
        rule_weight /= total
        llm_weight /= total

        # Calculate weighted confidence
        rule_score = rule_grade.confidence * rule_weight
        llm_score = llm_grade.confidence * llm_weight

        # Choose level with higher weighted score
        if rule_score >= llm_score:
            base_grade = rule_grade
        else:
            base_grade = llm_grade

        # Combine confidence
        combined_confidence = (
            rule_grade.confidence * rule_weight + llm_grade.confidence * llm_weight
        )

        return EvidenceGrade(
            level=base_grade.level,
            study_type=base_grade.study_type,
            confidence=combined_confidence,
            sample_size=rule_grade.sample_size or llm_grade.sample_size,
            classifier_source="ensemble_weighted",
            raw_scores={
                "rule_confidence": rule_grade.confidence,
                "llm_confidence": llm_grade.confidence,
                "rule_level": rule_grade.level.value,
                "llm_level": llm_grade.level.value,
            },
        )

    def _voting(
        self,
        rule_grade: EvidenceGrade,
        llm_grade: EvidenceGrade,
    ) -> EvidenceGrade:
        """Voting strategy (require agreement)."""
        if rule_grade.level == llm_grade.level:
            # Agreement - high confidence
            return EvidenceGrade(
                level=rule_grade.level,
                study_type=rule_grade.study_type,
                confidence=max(rule_grade.confidence, llm_grade.confidence),
                sample_size=rule_grade.sample_size,
                classifier_source="ensemble_agreement",
            )
        else:
            # Disagreement - use higher confidence
            if rule_grade.confidence >= llm_grade.confidence:
                result = rule_grade
            else:
                result = llm_grade

            # Reduce confidence due to disagreement
            result.confidence *= 0.7
            result.classifier_source = "ensemble_disagreement"
            result.quality_notes.append(
                f"Classifiers disagreed: rule={rule_grade.level.value}, "
                f"llm={llm_grade.level.value}"
            )
            return result

    def _confidence_based(
        self,
        rule_grade: EvidenceGrade,
        llm_grade: EvidenceGrade,
    ) -> EvidenceGrade:
        """Use highest confidence result."""
        if rule_grade.confidence >= llm_grade.confidence:
            result = rule_grade
            result.classifier_source = "ensemble_rule_higher"
        else:
            result = llm_grade
            result.classifier_source = "ensemble_llm_higher"

        return result

    def _rule_first(
        self,
        rule_grade: EvidenceGrade,
        llm_grade: EvidenceGrade,
    ) -> EvidenceGrade:
        """Rule-first with LLM fallback."""
        threshold = self._config.confidence_threshold

        if rule_grade.confidence >= threshold:
            rule_grade.classifier_source = "ensemble_rule_primary"
            return rule_grade
        else:
            llm_grade.classifier_source = "ensemble_llm_fallback"
            return llm_grade

    def _llm_first(
        self,
        rule_grade: EvidenceGrade,
        llm_grade: EvidenceGrade,
    ) -> EvidenceGrade:
        """LLM-first with rule fallback."""
        threshold = self._config.confidence_threshold

        if llm_grade.confidence >= threshold:
            llm_grade.classifier_source = "ensemble_llm_primary"
            return llm_grade
        else:
            rule_grade.classifier_source = "ensemble_rule_fallback"
            return rule_grade


# Convenience function
def grade_evidence(
    title: str = "",
    abstract: str = "",
    full_text: str = "",
    use_llm: bool = True,
    strategy: EnsembleStrategy = EnsembleStrategy.WEIGHTED_AVERAGE,
) -> EvidenceGrade:
    """Grade evidence level from paper text.

    Convenience function for quick classification.

    Args:
        title: Paper title
        abstract: Paper abstract
        full_text: Full paper text (optional)
        use_llm: Whether to use LLM classifier
        strategy: Ensemble strategy to use

    Returns:
        EvidenceGrade with classification result

    Example:
        >>> from jarvis_core.evidence import grade_evidence
        >>> grade = grade_evidence(
        ...     title="A randomized controlled trial...",
        ...     abstract="Methods: We conducted a double-blind RCT..."
        ... )
        >>> print(f"Evidence: {grade.level.description}")
        Evidence: 個別のRCT（狭い信頼区間）
    """
    config = EnsembleConfig(
        strategy=strategy,
        use_llm=use_llm,
    )

    classifier = EnsembleClassifier(config=config)
    return classifier.classify(title, abstract, full_text)