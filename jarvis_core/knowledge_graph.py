"""Knowledge Graph × Vector Hybrid.

Per Issue Ω-9, this integrates causal edges with vector distances.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paper_vector import PaperVector


@dataclass
class KnowledgeEdge:
    """An edge in the knowledge graph."""

    source: str
    target: str
    relation: str
    weight: float
    evidence_papers: list[str] = field(default_factory=list)


@dataclass
class KnowledgeNode:
    """A node in the knowledge graph."""

    id: str
    label: str
    node_type: str  # concept, method, paper
    attributes: dict = field(default_factory=dict)


class HybridKnowledgeGraph:
    """Hybrid knowledge graph with vectors and edges."""

    def __init__(self):
        self.nodes: dict[str, KnowledgeNode] = {}
        self.edges: list[KnowledgeEdge] = []
        self.vectors: dict[str, PaperVector] = {}

    def add_paper_vector(self, pv: PaperVector) -> None:
        """Add a paper vector to the graph."""
        self.vectors[pv.paper_id] = pv

        # Create paper node
        self.nodes[pv.paper_id] = KnowledgeNode(
            id=pv.paper_id,
            label=pv.source_locator,
            node_type="paper",
            attributes={"year": pv.metadata.year},
        )

        # Create concept nodes and edges
        for concept, score in pv.concept.concepts.items():
            if concept not in self.nodes:
                self.nodes[concept] = KnowledgeNode(
                    id=concept,
                    label=concept,
                    node_type="concept",
                )

            self.edges.append(
                KnowledgeEdge(
                    source=pv.paper_id,
                    target=concept,
                    relation="discusses",
                    weight=score,
                    evidence_papers=[pv.paper_id],
                )
            )

    def build_from_vectors(self, vectors: list[PaperVector]) -> None:
        """Build graph from list of paper vectors."""
        for pv in vectors:
            self.add_paper_vector(pv)

        # Build concept-concept edges based on co-occurrence
        self._build_concept_edges()

    def _build_concept_edges(self) -> None:
        """Build edges between concepts based on co-occurrence."""
        concept_papers: dict[str, set[str]] = {}

        for pv in self.vectors.values():
            for concept in pv.concept.concepts:
                if concept not in concept_papers:
                    concept_papers[concept] = set()
                concept_papers[concept].add(pv.paper_id)

        concepts = list(concept_papers.keys())
        for i, c1 in enumerate(concepts):
            for c2 in concepts[i + 1 :]:
                shared = concept_papers[c1] & concept_papers[c2]
                if shared:
                    weight = len(shared) / max(len(concept_papers[c1]), len(concept_papers[c2]))
                    self.edges.append(
                        KnowledgeEdge(
                            source=c1,
                            target=c2,
                            relation="co_occurs",
                            weight=weight,
                            evidence_papers=list(shared),
                        )
                    )

    def get_vector_distance(self, id1: str, id2: str) -> float:
        """Get vector distance between two papers."""
        pv1 = self.vectors.get(id1)
        pv2 = self.vectors.get(id2)

        if not pv1 or not pv2:
            return float("inf")

        # Use biological axis distance
        ba1 = pv1.biological_axis.as_tuple()
        ba2 = pv2.biological_axis.as_tuple()

        return math.sqrt(sum((a - b) ** 2 for a, b in zip(ba1, ba2)))

    def get_graph_distance(self, id1: str, id2: str) -> int:
        """Get shortest path distance in graph."""
        # Simple BFS
        if id1 not in self.nodes or id2 not in self.nodes:
            return -1

        adjacency: dict[str, set[str]] = {}
        for edge in self.edges:
            if edge.source not in adjacency:
                adjacency[edge.source] = set()
            if edge.target not in adjacency:
                adjacency[edge.target] = set()
            adjacency[edge.source].add(edge.target)
            adjacency[edge.target].add(edge.source)

        visited = {id1}
        queue = [(id1, 0)]

        while queue:
            current, dist = queue.pop(0)
            if current == id2:
                return dist

            for neighbor in adjacency.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))

        return -1

    def get_hybrid_similarity(self, id1: str, id2: str) -> float:
        """Get hybrid similarity combining vector and graph."""
        vec_dist = self.get_vector_distance(id1, id2)
        graph_dist = self.get_graph_distance(id1, id2)

        if vec_dist == float("inf") or graph_dist < 0:
            return 0.0

        # Normalize distances to 0-1 similarity
        vec_sim = 1 / (1 + vec_dist)
        graph_sim = 1 / (1 + graph_dist)

        return 0.6 * vec_sim + 0.4 * graph_sim

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "nodes": [
                {"id": n.id, "label": n.label, "type": n.node_type} for n in self.nodes.values()
            ],
            "edges": [
                {"source": e.source, "target": e.target, "relation": e.relation, "weight": e.weight}
                for e in self.edges
            ],
            "paper_count": len(self.vectors),
        }


def build_knowledge_graph(vectors: list[PaperVector]) -> HybridKnowledgeGraph:
    """Build a hybrid knowledge graph from vectors."""
    graph = HybridKnowledgeGraph()
    graph.build_from_vectors(vectors)
    return graph
