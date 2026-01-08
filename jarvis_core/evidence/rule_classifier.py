"""Rule-Based Evidence Classifier.

Pattern matching and keyword-based evidence level classification.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.1 Rule Classifier
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from re import Pattern

from jarvis_core.evidence.schema import (
    EvidenceGrade,
    EvidenceLevel,
    PICOExtraction,
    StudyType,
)

logger = logging.getLogger(__name__)


@dataclass
class ClassificationPattern:
    """A pattern for classifying study type."""

    study_type: StudyType
    patterns: list[Pattern]
    weight: float = 1.0
    requires_abstract: bool = False


class RuleBasedClassifier:
    """Rule-based evidence classifier using pattern matching.
    
    Uses keywords and patterns to identify study types and assign
    evidence levels based on study design.
    
    Example:
        >>> classifier = RuleBasedClassifier()
        >>> grade = classifier.classify(
        ...     title="A randomized controlled trial of...",
        ...     abstract="Methods: We conducted a double-blind RCT..."
        ... )
        >>> print(grade.level)
        EvidenceLevel.LEVEL_1B
    """

    def __init__(self):
        """Initialize the classifier with patterns."""
        self._patterns = self._build_patterns()
        self._sample_size_pattern = re.compile(
            r"(?:n\s*=\s*|sample\s+(?:size|of)\s*(?:was\s+)?|"
            r"(?:included|enrolled|recruited)\s+)(\d+(?:,\d+)?)",
            re.IGNORECASE
        )

    def _build_patterns(self) -> list[ClassificationPattern]:
        """Build classification patterns."""
        return [
            # Meta-analysis / Systematic Review (Level 1a)
            ClassificationPattern(
                study_type=StudyType.META_ANALYSIS,
                patterns=[
                    re.compile(r"\bmeta[-\s]?analysis\b", re.IGNORECASE),
                    re.compile(r"\bpooled\s+analysis\b", re.IGNORECASE),
                ],
                weight=1.0,
            ),
            ClassificationPattern(
                study_type=StudyType.SYSTEMATIC_REVIEW,
                patterns=[
                    re.compile(r"\bsystematic\s+review\b", re.IGNORECASE),
                    re.compile(r"\bPRISMA\b", re.IGNORECASE),
                    re.compile(r"\bCochrane\s+review\b", re.IGNORECASE),
                ],
                weight=1.0,
            ),

            # RCT (Level 1b)
            ClassificationPattern(
                study_type=StudyType.RCT,
                patterns=[
                    re.compile(r"\brandomized\s+controlled\s+trial\b", re.IGNORECASE),
                    re.compile(r"\brandomised\s+controlled\s+trial\b", re.IGNORECASE),
                    re.compile(r"\bRCT\b"),
                    re.compile(r"\bdouble[-\s]?blind\b", re.IGNORECASE),
                    re.compile(r"\bplacebo[-\s]?controlled\b", re.IGNORECASE),
                    re.compile(r"\brandomly\s+assigned\b", re.IGNORECASE),
                    re.compile(r"\brandomly\s+allocated\b", re.IGNORECASE),
                ],
                weight=0.9,
            ),
            ClassificationPattern(
                study_type=StudyType.CROSSOVER_TRIAL,
                patterns=[
                    re.compile(r"\bcrossover\s+(?:trial|study|design)\b", re.IGNORECASE),
                    re.compile(r"\bcross[-\s]?over\b", re.IGNORECASE),
                ],
                weight=0.9,
            ),

            # Cohort studies (Level 2b)
            ClassificationPattern(
                study_type=StudyType.COHORT_PROSPECTIVE,
                patterns=[
                    re.compile(r"\bprospective\s+cohort\b", re.IGNORECASE),
                    re.compile(r"\blongitudinal\s+study\b", re.IGNORECASE),
                    re.compile(r"\bfollow[-\s]?up\s+study\b", re.IGNORECASE),
                ],
                weight=0.8,
            ),
            ClassificationPattern(
                study_type=StudyType.COHORT_RETROSPECTIVE,
                patterns=[
                    re.compile(r"\bretrospective\s+cohort\b", re.IGNORECASE),
                    re.compile(r"\bretrospective\s+analysis\b", re.IGNORECASE),
                    re.compile(r"\bhistorical\s+cohort\b", re.IGNORECASE),
                ],
                weight=0.8,
            ),

            # Case-control (Level 3b)
            ClassificationPattern(
                study_type=StudyType.CASE_CONTROL,
                patterns=[
                    re.compile(r"\bcase[-\s]?control\s+study\b", re.IGNORECASE),
                    re.compile(r"\bmatched\s+controls\b", re.IGNORECASE),
                ],
                weight=0.7,
            ),

            # Cross-sectional (Level 4)
            ClassificationPattern(
                study_type=StudyType.CROSS_SECTIONAL,
                patterns=[
                    re.compile(r"\bcross[-\s]?sectional\s+study\b", re.IGNORECASE),
                    re.compile(r"\bprevalence\s+study\b", re.IGNORECASE),
                    re.compile(r"\bsurvey\s+study\b", re.IGNORECASE),
                ],
                weight=0.6,
            ),

            # Case series / Case report (Level 4)
            ClassificationPattern(
                study_type=StudyType.CASE_SERIES,
                patterns=[
                    re.compile(r"\bcase\s+series\b", re.IGNORECASE),
                    re.compile(r"\bcase\s+studies\b", re.IGNORECASE),
                ],
                weight=0.5,
            ),
            ClassificationPattern(
                study_type=StudyType.CASE_REPORT,
                patterns=[
                    re.compile(r"\bcase\s+report\b", re.IGNORECASE),
                    re.compile(r"\bcase\s+presentation\b", re.IGNORECASE),
                ],
                weight=0.4,
            ),

            # Guidelines and reviews (Level 5)
            ClassificationPattern(
                study_type=StudyType.GUIDELINE,
                patterns=[
                    re.compile(r"\bclinical\s+(?:practice\s+)?guideline\b", re.IGNORECASE),
                    re.compile(r"\bconsensus\s+statement\b", re.IGNORECASE),
                ],
                weight=0.5,
            ),
            ClassificationPattern(
                study_type=StudyType.NARRATIVE_REVIEW,
                patterns=[
                    re.compile(r"\breview\s+article\b", re.IGNORECASE),
                    re.compile(r"\bliterature\s+review\b", re.IGNORECASE),
                    re.compile(r"\bnarrative\s+review\b", re.IGNORECASE),
                ],
                weight=0.4,
            ),
            ClassificationPattern(
                study_type=StudyType.EXPERT_OPINION,
                patterns=[
                    re.compile(r"\bexpert\s+opinion\b", re.IGNORECASE),
                    re.compile(r"\beditorial\b", re.IGNORECASE),
                    re.compile(r"\bcommentary\b", re.IGNORECASE),
                ],
                weight=0.3,
            ),
        ]

    def classify(
        self,
        title: str = "",
        abstract: str = "",
        full_text: str = "",
    ) -> EvidenceGrade:
        """Classify evidence level from text.
        
        Args:
            title: Paper title
            abstract: Paper abstract
            full_text: Full paper text (optional)
            
        Returns:
            EvidenceGrade with classification result
        """
        # Combine text for matching
        combined_text = f"{title} {abstract} {full_text}".strip()

        if not combined_text:
            return EvidenceGrade.unknown()

        # Find matching patterns
        matches: list[tuple[StudyType, float]] = []

        for pattern_config in self._patterns:
            for pattern in pattern_config.patterns:
                if pattern.search(combined_text):
                    matches.append((
                        pattern_config.study_type,
                        pattern_config.weight,
                    ))
                    break  # Only count each pattern config once

        if not matches:
            return EvidenceGrade(
                level=EvidenceLevel.UNKNOWN,
                study_type=StudyType.UNKNOWN,
                confidence=0.0,
                classifier_source="rule",
            )

        # Get the highest-weighted match
        matches.sort(key=lambda x: x[1], reverse=True)
        best_match = matches[0]

        study_type = best_match[0]
        confidence = best_match[1]

        # Boost confidence if multiple patterns match
        if len(matches) > 1:
            confidence = min(1.0, confidence + 0.1 * (len(matches) - 1))

        # Extract sample size
        sample_size = self._extract_sample_size(combined_text)

        # Adjust evidence level based on study characteristics
        level = study_type.default_evidence_level

        # Store raw scores
        raw_scores = {m[0].value: m[1] for m in matches}

        return EvidenceGrade(
            level=level,
            study_type=study_type,
            confidence=confidence,
            sample_size=sample_size,
            classifier_source="rule",
            raw_scores=raw_scores,
        )

    def _extract_sample_size(self, text: str) -> int | None:
        """Extract sample size from text."""
        match = self._sample_size_pattern.search(text)
        if match:
            try:
                # Remove commas and convert to int
                size_str = match.group(1).replace(",", "")
                return int(size_str)
            except ValueError:
                pass
        return None

    def extract_pico(self, text: str) -> PICOExtraction:
        """Extract PICO components from text.
        
        Args:
            text: Paper text (abstract preferred)
            
        Returns:
            PICOExtraction with extracted components
        """
        # Simple pattern-based extraction
        population = self._extract_population(text)
        intervention = self._extract_intervention(text)
        comparator = self._extract_comparator(text)
        outcome = self._extract_outcome(text)

        return PICOExtraction(
            population=population,
            intervention=intervention,
            comparator=comparator,
            outcome=outcome,
        )

    def _extract_population(self, text: str) -> str | None:
        """Extract population/participants from text."""
        patterns = [
            re.compile(r"(?:patients|participants|subjects)\s+with\s+([^.]{10,80})", re.IGNORECASE),
            re.compile(r"(?:included|enrolled)\s+(\d+\s+[^.]{10,60})", re.IGNORECASE),
        ]
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return None

    def _extract_intervention(self, text: str) -> str | None:
        """Extract intervention from text."""
        patterns = [
            re.compile(r"(?:treated\s+with|received|administered)\s+([^.]{5,60})", re.IGNORECASE),
            re.compile(r"intervention\s+(?:group|arm)?\s*(?:received)?\s*([^.]{5,60})", re.IGNORECASE),
        ]
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return None

    def _extract_comparator(self, text: str) -> str | None:
        """Extract comparator from text."""
        patterns = [
            re.compile(r"(?:compared\s+(?:to|with)|versus|vs\.?)\s+([^.]{5,60})", re.IGNORECASE),
            re.compile(r"control\s+group\s+received\s+([^.]{5,60})", re.IGNORECASE),
            re.compile(r"placebo", re.IGNORECASE),
        ]
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                if pattern.pattern == r"placebo":
                    return "placebo"
                return match.group(1).strip()
        return None

    def _extract_outcome(self, text: str) -> str | None:
        """Extract primary outcome from text."""
        patterns = [
            re.compile(r"primary\s+(?:end\s*point|outcome)\s+(?:was|is)?\s*([^.]{10,80})", re.IGNORECASE),
            re.compile(r"main\s+outcome\s+(?:measure)?\s*(?:was|is)?\s*([^.]{10,80})", re.IGNORECASE),
        ]
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return None
