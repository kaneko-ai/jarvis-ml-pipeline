"""Knowledge graph utilities."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GraphNode:
    """Graph node."""

    node_id: str


@dataclass
class GraphEdge:
    """Graph edge."""

    source: str
    target: str


@dataclass
class KnowledgeGraph:
    """Minimal knowledge graph container."""

    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)

    def add_edge(self, source: str, target: str) -> None:
        """Add an edge to the graph.

        Args:
            source: Source node id.
            target: Target node id.
        """
        if source not in self.nodes:
            self.nodes[source] = GraphNode(node_id=source)
        if target not in self.nodes:
            self.nodes[target] = GraphNode(node_id=target)
        self.edges.append(GraphEdge(source=source, target=target))


__all__ = ["GraphNode", "GraphEdge", "KnowledgeGraph"]
