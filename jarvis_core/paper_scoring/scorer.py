"""Paper Quality Scorer.

Combines multiple signals to calculate paper quality/reliability scores.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ScoringWeights:
    """Weights for different scoring components."""

    evidence_level: float = 0.25
    citation_support: float = 0.20
    methodology: float = 0.20
    recency: float = 0.10
    journal_impact: float = 0.15
    contradiction_penalty: float = 0.10

    def normalize(self) -> ScoringWeights:
        """Normalize weights to sum to 1.0."""
        total = (
            self.evidence_level +
            self.citation_support +
            self.methodology +
            self.recency +
            self.journal_impact +
            self.contradiction_penalty
        )
        if total == 0:
            return self

        return ScoringWeights(
            evidence_level=self.evidence_level / total,
            citation_support=self.citation_support / total,
            methodology=self.methodology / total,
            recency=self.recency / total,
            journal_impact=self.journal_impact / total,
            contradiction_penalty=self.contradiction_penalty / total,
        )


@dataclass
class PaperScore:
    """Overall quality score for a paper."""

    paper_id: str
    overall_score: float  # 0.0 to 1.0

    # Component scores
    evidence_score: float = 0.0
    citation_score: float = 0.0
    methodology_score: float = 0.0
    recency_score: float = 0.0
    journal_score: float = 0.0
    contradiction_penalty: float = 0.0

    # Metadata
    confidence: float = 0.0
    components: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "paper_id": self.paper_id,
            "overall_score": round(self.overall_score, 3),
            "evidence_score": round(self.evidence_score, 3),
            "citation_score": round(self.citation_score, 3),
            "methodology_score": round(self.methodology_score, 3),
            "recency_score": round(self.recency_score, 3),
            "journal_score": round(self.journal_score, 3),
            "contradiction_penalty": round(self.contradiction_penalty, 3),
            "confidence": round(self.confidence, 3),
        }

    @property
    def grade(self) -> str:
        """Get letter grade."""
        if self.overall_score >= 0.9:
            return "A"
        elif self.overall_score >= 0.8:
            return "B"
        elif self.overall_score >= 0.7:
            return "C"
        elif self.overall_score >= 0.6:
            return "D"
        else:
            return "F"


class PaperScorer:
    """Calculates quality scores for research papers.
    
    Combines evidence level, citation analysis, methodology assessment,
    recency, journal impact, and contradiction detection into an
    overall reliability score.
    
    Example:
        >>> scorer = PaperScorer()
        >>> score = scorer.score(
        ...     paper_id="paper_A",
        ...     evidence_level=2,  # Level 2 evidence
        ...     support_count=10,
        ...     contrast_count=2,
        ... )
        >>> print(f"Score: {score.overall_score:.2f} ({score.grade})")
    """

    def __init__(self, weights: ScoringWeights | None = None):
        """Initialize the scorer.
        
        Args:
            weights: Custom scoring weights
        """
        self._weights = (weights or ScoringWeights()).normalize()

    def score(
        self,
        paper_id: str,
        evidence_level: int = 5,  # 1-5, 1 is best
        support_count: int = 0,
        contrast_count: int = 0,
        total_citations: int = 0,
        methodology_score: float = 0.5,
        publication_year: int = 2020,
        journal_impact_factor: float = 0.0,
        has_contradictions: bool = False,
    ) -> PaperScore:
        """Calculate paper score.
        
        Args:
            paper_id: Paper identifier
            evidence_level: CEBM evidence level (1-5)
            support_count: Number of supporting citations
            contrast_count: Number of contrasting citations
            total_citations: Total citation count
            methodology_score: Methodology quality (0-1)
            publication_year: Year of publication
            journal_impact_factor: Journal impact factor
            has_contradictions: Whether paper has contradictions
            
        Returns:
            PaperScore with overall and component scores
        """
        # Calculate component scores
        evidence_score = self._score_evidence(evidence_level)
        citation_score = self._score_citations(support_count, contrast_count, total_citations)
        methodology_score = min(1.0, max(0.0, methodology_score))
        recency_score = self._score_recency(publication_year)
        journal_score = self._score_journal(journal_impact_factor)
        contradiction_penalty = 0.3 if has_contradictions else 0.0

        # Calculate weighted overall score
        overall = (
            evidence_score * self._weights.evidence_level +
            citation_score * self._weights.citation_support +
            methodology_score * self._weights.methodology +
            recency_score * self._weights.recency +
            journal_score * self._weights.journal_impact -
            contradiction_penalty * self._weights.contradiction_penalty
        )

        overall = max(0.0, min(1.0, overall))

        # Calculate confidence based on available data
        confidence = self._calculate_confidence(
            evidence_level, total_citations, journal_impact_factor
        )

        return PaperScore(
            paper_id=paper_id,
            overall_score=overall,
            evidence_score=evidence_score,
            citation_score=citation_score,
            methodology_score=methodology_score,
            recency_score=recency_score,
            journal_score=journal_score,
            contradiction_penalty=contradiction_penalty,
            confidence=confidence,
        )

    def _score_evidence(self, level: int) -> float:
        """Score based on evidence level (1=best, 5=worst)."""
        scores = {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.4, 5: 0.2}
        return scores.get(level, 0.2)

    def _score_citations(
        self,
        support: int,
        contrast: int,
        total: int,
    ) -> float:
        """Score based on citation analysis."""
        if total == 0:
            return 0.5  # Neutral if no data

        # Higher support-to-contrast ratio is better
        if support + contrast == 0:
            return 0.5

        ratio = support / (support + contrast)

        # Also consider total citations (log scale)
        import math
        citation_factor = min(1.0, math.log10(total + 1) / 3)

        return ratio * 0.7 + citation_factor * 0.3

    def _score_recency(self, year: int) -> float:
        """Score based on publication recency."""
        current_year = 2026
        age = current_year - year

        if age <= 2:
            return 1.0
        elif age <= 5:
            return 0.8
        elif age <= 10:
            return 0.6
        else:
            return 0.4

    def _score_journal(self, impact_factor: float) -> float:
        """Score based on journal impact factor."""
        if impact_factor <= 0:
            return 0.5  # Unknown
        elif impact_factor >= 10:
            return 1.0
        elif impact_factor >= 5:
            return 0.8
        elif impact_factor >= 2:
            return 0.6
        else:
            return 0.4

    def _calculate_confidence(
        self,
        evidence_level: int,
        total_citations: int,
        impact_factor: float,
    ) -> float:
        """Calculate confidence in the score."""
        # Higher confidence with more data
        confidence = 0.5

        if evidence_level <= 3:
            confidence += 0.2

        if total_citations >= 10:
            confidence += 0.2

        if impact_factor > 0:
            confidence += 0.1

        return min(1.0, confidence)


def calculate_paper_score(
    paper_id: str,
    evidence_level: int = 5,
    support_count: int = 0,
    contrast_count: int = 0,
    **kwargs,
) -> PaperScore:
    """Calculate paper score.
    
    Convenience function for quick scoring.
    
    Args:
        paper_id: Paper identifier
        evidence_level: CEBM evidence level (1-5)
        support_count: Number of supporting citations
        contrast_count: Number of contrasting citations
        **kwargs: Additional arguments for PaperScorer.score
        
    Returns:
        PaperScore
    """
    scorer = PaperScorer()
    return scorer.score(
        paper_id=paper_id,
        evidence_level=evidence_level,
        support_count=support_count,
        contrast_count=contrast_count,
        **kwargs,
    )
