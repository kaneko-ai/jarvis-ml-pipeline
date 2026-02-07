"""Citation Stance Classifier.

Classifies citation stances as Support/Contrast/Mention.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.2.2
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from jarvis_core.citation.context_extractor import CitationContext

logger = logging.getLogger(__name__)


class CitationStance(Enum):
    """Citation stance towards the cited work."""

    SUPPORT = "support"  # Cites to support/confirm
    CONTRAST = "contrast"  # Cites to contrast/critique
    MENTION = "mention"  # Neutral mention/background
    EXTEND = "extend"  # Extends the cited work
    COMPARE = "compare"  # Compares methods/results
    UNKNOWN = "unknown"


@dataclass
class StanceResult:
    """Result of stance classification."""

    stance: CitationStance
    confidence: float
    evidence: str = ""  # Key phrases that led to the classification
    scores: dict[str, float] = field(default_factory=dict)  # Raw scores for all stances

    def __post_init__(self) -> None:
        if self.scores is None:
            self.scores = {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stance": self.stance.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "scores": self.scores,
        }


# Stance indicator patterns
SUPPORT_PATTERNS = [
    re.compile(r"\b(confirm|support|consistent with|in (?:line|agreement) with)\b", re.IGNORECASE),
    re.compile(r"\b(validate|corroborate|replicate|verify)\b", re.IGNORECASE),
    re.compile(r"\b(demonstrated|showed|found(?: that)?|reported)\b", re.IGNORECASE),
    re.compile(r"\b(following|building on|based on|as (?:shown|described))\b", re.IGNORECASE),
]

CONTRAST_PATTERNS = [
    re.compile(r"\b(contrast|contrary|unlike|differ|disagree)\b", re.IGNORECASE),
    re.compile(r"\b(however|although|despite|but|whereas)\b", re.IGNORECASE),
    re.compile(r"\b(limitation|failed|unable|problem|issue)\b", re.IGNORECASE),
    re.compile(r"\b(challenge|question|critique|criticize)\b", re.IGNORECASE),
    re.compile(r"\b(improve(?:d|s)? (?:upon|on)|better than|outperform)\b", re.IGNORECASE),
]

EXTEND_PATTERNS = [
    re.compile(r"\b(extend|expand|build(?:ing)? (?:on|upon)|advance)\b", re.IGNORECASE),
    re.compile(r"\b(further|additional|novel|new approach)\b", re.IGNORECASE),
    re.compile(r"\b(we (?:propose|introduce|present|develop))\b", re.IGNORECASE),
]

COMPARE_PATTERNS = [
    re.compile(r"\b(compare|comparison|similar(?:ly)?|likewise)\b", re.IGNORECASE),
    re.compile(r"\b(versus|vs\.?|against|relative to)\b", re.IGNORECASE),
    re.compile(r"\b(both|like|same as)\b", re.IGNORECASE),
]

MENTION_PATTERNS = [
    re.compile(r"\b(see|refer|note|e\.g\.|i\.e\.)\b", re.IGNORECASE),
    re.compile(r"\b(previous(?:ly)?|earlier|prior|recent(?:ly)?)\b", re.IGNORECASE),
    re.compile(r"\b(studied|examined|investigated|analyzed)\b", re.IGNORECASE),
]


class StanceClassifier:
    """Classifies citation stances using pattern matching.

    Uses linguistic cues to determine whether a citation supports,
    contrasts with, or merely mentions the cited work.

    Example:
        >>> classifier = StanceClassifier()
        >>> result = classifier.classify_text(
        ...     "Our results confirm the findings of Smith et al. [1]."
        ... )
        >>> print(result.stance)
        CitationStance.SUPPORT
    """

    def __init__(self, use_llm: bool = False) -> None:
        """Initialize the classifier.

        Args:
            use_llm: Whether to use LLM for classification (not yet implemented)
        """
        self._use_llm = use_llm

        self._stance_patterns = {
            CitationStance.SUPPORT: SUPPORT_PATTERNS,
            CitationStance.CONTRAST: CONTRAST_PATTERNS,
            CitationStance.EXTEND: EXTEND_PATTERNS,
            CitationStance.COMPARE: COMPARE_PATTERNS,
            CitationStance.MENTION: MENTION_PATTERNS,
        }

        # Weights for stance importance
        self._stance_weights = {
            CitationStance.CONTRAST: 1.5,  # Contrast is often more explicit
            CitationStance.SUPPORT: 1.2,
            CitationStance.EXTEND: 1.1,
            CitationStance.COMPARE: 1.0,
            CitationStance.MENTION: 0.8,  # Mention is a fallback
        }

    def classify(self, context: CitationContext) -> StanceResult:
        """Classify citation stance from context.

        Args:
            context: CitationContext to classify

        Returns:
            StanceResult with classification
        """
        # Use full context for better classification
        text = context.get_full_context()
        return self.classify_text(text)

    def classify_text(self, text: str) -> StanceResult:
        """Classify citation stance from text.

        Args:
            text: Text containing the citation

        Returns:
            StanceResult with classification
        """
        if not text:
            return StanceResult(
                stance=CitationStance.UNKNOWN,
                confidence=0.0,
            )

        # Calculate scores for each stance
        scores: dict[CitationStance, float] = {}
        evidence: dict[CitationStance, list[str]] = {}

        for stance, patterns in self._stance_patterns.items():
            score = 0.0
            matched_phrases = []

            for pattern in patterns:
                matches = pattern.findall(text)
                if matches:
                    score += len(matches) * self._stance_weights.get(stance, 1.0)
                    matched_phrases.extend(matches)

            scores[stance] = score
            evidence[stance] = matched_phrases[:3]  # Keep top 3 phrases

        # Determine best stance
        if not any(scores.values()):
            return StanceResult(
                stance=CitationStance.MENTION,  # Default to neutral mention
                confidence=0.3,
                evidence="No explicit stance indicators",
                scores={s.value: v for s, v in scores.items()},
            )

        # Get stance with highest score
        best_stance = max(scores, key=lambda stance: scores[stance])
        best_score = scores[best_stance]

        # Calculate confidence (normalize by total)
        total_score = sum(scores.values())
        confidence = best_score / total_score if total_score > 0 else 0.0

        # Build evidence string
        evidence_str = ", ".join(evidence.get(best_stance, []))

        return StanceResult(
            stance=best_stance,
            confidence=min(1.0, confidence),
            evidence=evidence_str,
            scores={s.value: v for s, v in scores.items()},
        )

    def classify_batch(
        self,
        contexts: list[CitationContext],
    ) -> list[StanceResult]:
        """Classify multiple citation contexts.

        Args:
            contexts: List of CitationContext objects

        Returns:
            List of StanceResult objects
        """
        return [self.classify(ctx) for ctx in contexts]


def classify_citation_stance(text: str) -> StanceResult:
    """Classify citation stance from text.

    Convenience function for quick classification.

    Args:
        text: Text containing the citation

    Returns:
        StanceResult with classification
    """
    classifier = StanceClassifier()
    return classifier.classify_text(text)
