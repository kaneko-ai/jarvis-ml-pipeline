"""Citation Graph.

Builds and analyzes citation networks.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.2.3
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from jarvis_core.citation.context_extractor import CitationContext
from jarvis_core.citation.stance_classifier import CitationStance, StanceResult

logger = logging.getLogger(__name__)


@dataclass
class CitationEdge:
    """An edge in the citation graph."""

    source_id: str  # Citing paper
    target_id: str  # Cited paper
    stance: CitationStance = CitationStance.MENTION
    confidence: float = 0.0
    contexts: list[CitationContext] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "stance": self.stance.value,
            "confidence": self.confidence,
            "num_contexts": len(self.contexts),
        }


@dataclass
class PaperNode:
    """A node in the citation graph."""

    paper_id: str
    title: str | None = None
    year: int | None = None
    authors: list[str] = field(default_factory=list)

    # Citation statistics
    cited_by_count: int = 0
    cites_count: int = 0
    support_count: int = 0
    contrast_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "year": self.year,
            "authors": self.authors,
            "cited_by_count": self.cited_by_count,
            "cites_count": self.cites_count,
            "support_count": self.support_count,
            "contrast_count": self.contrast_count,
        }


class CitationGraph:
    """A graph of citation relationships.

    Supports analysis of citation networks including:
    - Finding supporting/contrasting citations
    - Identifying highly cited papers
    - Finding citation chains

    Example:
        >>> graph = CitationGraph()
        >>> graph.add_edge("paper_A", "paper_B", CitationStance.SUPPORT)
        >>> graph.add_edge("paper_A", "paper_C", CitationStance.CONTRAST)
        >>> papers_cited = graph.get_citations("paper_A")
        >>> print(papers_cited)
        ['paper_B', 'paper_C']
    """

    def __init__(self) -> None:
        """Initialize the citation graph."""
        self._nodes: dict[str, PaperNode] = {}
        self._edges: dict[tuple[str, str], CitationEdge] = {}

        # Index for fast lookups
        self._outgoing: dict[str, set[str]] = defaultdict(set)  # paper -> papers it cites
        self._incoming: dict[str, set[str]] = defaultdict(set)  # paper -> papers citing it

    def add_node(
        self,
        paper_id: str,
        title: str | None = None,
        year: int | None = None,
        authors: list[str] | None = None,
    ) -> PaperNode:
        """Add a paper node to the graph.

        Args:
            paper_id: Paper identifier
            title: Paper title
            year: Publication year
            authors: List of author names

        Returns:
            The created or updated PaperNode
        """
        if paper_id not in self._nodes:
            self._nodes[paper_id] = PaperNode(
                paper_id=paper_id,
                title=title,
                year=year,
                authors=authors or [],
            )
        else:
            # Update existing node if new info provided
            node = self._nodes[paper_id]
            if title:
                node.title = title
            if year:
                node.year = year
            if authors:
                node.authors = authors

        return self._nodes[paper_id]

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        stance: CitationStance = CitationStance.MENTION,
        confidence: float = 0.0,
        context: CitationContext | None = None,
    ) -> CitationEdge:
        """Add a citation edge to the graph.

        Args:
            source_id: Citing paper ID
            target_id: Cited paper ID
            stance: Citation stance
            confidence: Classification confidence
            context: Optional citation context

        Returns:
            The created or updated CitationEdge
        """
        # Ensure nodes exist
        self.add_node(source_id)
        self.add_node(target_id)

        edge_key = (source_id, target_id)

        if edge_key not in self._edges:
            self._edges[edge_key] = CitationEdge(
                source_id=source_id,
                target_id=target_id,
                stance=stance,
                confidence=confidence,
            )

            # Update indices
            self._outgoing[source_id].add(target_id)
            self._incoming[target_id].add(source_id)

            # Update node statistics
            self._nodes[source_id].cites_count += 1
            self._nodes[target_id].cited_by_count += 1

            if stance == CitationStance.SUPPORT:
                self._nodes[target_id].support_count += 1
            elif stance == CitationStance.CONTRAST:
                self._nodes[target_id].contrast_count += 1

        edge = self._edges[edge_key]

        if context:
            edge.contexts.append(context)

        return edge

    def get_node(self, paper_id: str) -> PaperNode | None:
        """Get a paper node by ID."""
        return self._nodes.get(paper_id)

    def get_edge(self, source_id: str, target_id: str) -> CitationEdge | None:
        """Get an edge by source and target IDs."""
        return self._edges.get((source_id, target_id))

    def get_citations(self, paper_id: str) -> list[str]:
        """Get papers cited by a given paper."""
        return list(self._outgoing.get(paper_id, set()))

    def get_cited_by(self, paper_id: str) -> list[str]:
        """Get papers that cite a given paper."""
        return list(self._incoming.get(paper_id, set()))

    def get_supporting_citations(self, paper_id: str) -> list[str]:
        """Get papers that cite with support stance."""
        citing_papers = self._incoming.get(paper_id, set())
        supporting = []

        for citing_id in citing_papers:
            edge = self._edges.get((citing_id, paper_id))
            if edge and edge.stance == CitationStance.SUPPORT:
                supporting.append(citing_id)

        return supporting

    def get_contrasting_citations(self, paper_id: str) -> list[str]:
        """Get papers that cite with contrast stance."""
        citing_papers = self._incoming.get(paper_id, set())
        contrasting = []

        for citing_id in citing_papers:
            edge = self._edges.get((citing_id, paper_id))
            if edge and edge.stance == CitationStance.CONTRAST:
                contrasting.append(citing_id)

        return contrasting

    def get_top_cited(self, limit: int = 10) -> list[tuple[str, int]]:
        """Get top cited papers.

        Args:
            limit: Maximum number of results

        Returns:
            List of (paper_id, citation_count) tuples
        """
        papers_by_citations = [
            (node.paper_id, node.cited_by_count) for node in self._nodes.values()
        ]
        papers_by_citations.sort(key=lambda x: x[1], reverse=True)
        return papers_by_citations[:limit]

    def get_controversial_papers(self, min_contrast: int = 2) -> list[str]:
        """Get papers with significant contrasting citations.

        Args:
            min_contrast: Minimum number of contrasting citations

        Returns:
            List of paper IDs
        """
        return [
            node.paper_id for node in self._nodes.values() if node.contrast_count >= min_contrast
        ]

    def to_dict(self) -> dict[str, Any]:
        """Convert graph to dictionary."""
        return {
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "edges": [edge.to_dict() for edge in self._edges.values()],
            "statistics": {
                "node_count": len(self._nodes),
                "edge_count": len(self._edges),
            },
        }

    @property
    def node_count(self) -> int:
        """Number of nodes in the graph."""
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        """Number of edges in the graph."""
        return len(self._edges)


def build_citation_graph(
    contexts: list[CitationContext],
    stance_results: list[StanceResult] | None = None,
) -> CitationGraph:
    """Build a citation graph from contexts and stance results.

    Convenience function for building a graph from extracted citations.

    Args:
        contexts: List of CitationContext objects
        stance_results: Optional stance classification results
            (must be same length as contexts if provided)

    Returns:
        CitationGraph with citations added
    """
    graph = CitationGraph()

    for i, context in enumerate(contexts):
        stance = CitationStance.MENTION
        confidence = 0.0

        if stance_results and i < len(stance_results):
            stance = stance_results[i].stance
            confidence = stance_results[i].confidence

        graph.add_edge(
            source_id=context.citing_paper_id,
            target_id=context.cited_paper_id,
            stance=stance,
            confidence=confidence,
            context=context,
        )

    return graph
