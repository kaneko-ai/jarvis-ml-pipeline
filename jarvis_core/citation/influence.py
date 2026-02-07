"""Citation Influence Calculator.

Calculates influence and controversy scores for papers.
Per JARVIS_COMPLETION_INSTRUCTION Task 2.2.2
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jarvis_core.citation.stance_classifier import CitationStance


@dataclass
class InfluenceScore:
    """Influence score for a paper."""

    paper_id: str
    total_citations: int
    support_count: int
    contrast_count: int
    mention_count: int
    influence_score: float
    controversy_score: float

    def to_dict(self) -> dict[str, float | int | str]:
        return {
            "paper_id": self.paper_id,
            "total_citations": self.total_citations,
            "support_count": self.support_count,
            "contrast_count": self.contrast_count,
            "mention_count": self.mention_count,
            "influence_score": self.influence_score,
            "controversy_score": self.controversy_score,
        }


class InfluenceCalculator:
    """Calculates paper influence based on citation stances."""

    def __init__(self, citation_graph: Any | None = None) -> None:
        """Initialize calculator.

        Args:
            citation_graph: Optional CitationGraph instance
        """
        self._graph = citation_graph

    def calculate(
        self,
        paper_id: str,
        citations: list[Any] | None = None,
    ) -> InfluenceScore:
        """Calculate influence score for a paper.

        Args:
            paper_id: Paper ID
            citations: Optional list of citation objects with stance attribute

        Returns:
            InfluenceScore object
        """
        if citations is None and self._graph:
            citations = self._graph.get_citations(paper_id)

        if not citations:
            return InfluenceScore(
                paper_id=paper_id,
                total_citations=0,
                support_count=0,
                contrast_count=0,
                mention_count=0,
                influence_score=0.0,
                controversy_score=0.0,
            )

        support = sum(1 for c in citations if getattr(c, "stance", None) == CitationStance.SUPPORT)
        contrast = sum(
            1 for c in citations if getattr(c, "stance", None) == CitationStance.CONTRAST
        )
        mention = sum(1 for c in citations if getattr(c, "stance", None) == CitationStance.MENTION)

        total = len(citations)

        # Influence score: citations * (support_rate + 0.5 * contrast_rate)
        support_rate = support / total if total > 0 else 0
        contrast_rate = contrast / total if total > 0 else 0

        influence = total * (support_rate + 0.5 * contrast_rate)

        # Controversy score: proportion of contrasting citations
        controversy = contrast_rate

        return InfluenceScore(
            paper_id=paper_id,
            total_citations=total,
            support_count=support,
            contrast_count=contrast,
            mention_count=mention,
            influence_score=influence,
            controversy_score=controversy,
        )

    def rank_papers(
        self,
        paper_ids: list[str],
        citations_map: dict[str, list[Any]] | None = None,
        by: str = "influence",
    ) -> list[InfluenceScore]:
        """Rank papers by influence or controversy.

        Args:
            paper_ids: List of paper IDs
            citations_map: Dict mapping paper_id to list of citations
            by: Ranking criterion ("influence", "controversy", "citations")

        Returns:
            Sorted list of InfluenceScore objects
        """
        citations_map = citations_map or {}
        scores = [self.calculate(pid, citations_map.get(pid, [])) for pid in paper_ids]

        if by == "influence":
            return sorted(scores, key=lambda x: x.influence_score, reverse=True)
        elif by == "controversy":
            return sorted(scores, key=lambda x: x.controversy_score, reverse=True)
        elif by == "citations":
            return sorted(scores, key=lambda x: x.total_citations, reverse=True)

        return scores
