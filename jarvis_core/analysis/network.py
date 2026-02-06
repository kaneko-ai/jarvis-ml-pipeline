"""Network analysis utilities."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NetworkGraph:
    """Simple directed network representation."""

    nodes: set[str] = field(default_factory=set)
    edges: list[tuple[str, str]] = field(default_factory=list)


def build_network(edges: list[tuple[str, str]]) -> NetworkGraph:
    """Build a network graph from edge pairs.

    Args:
        edges: List of (source, target) pairs.

    Returns:
        NetworkGraph with nodes and edges.
    """
    nodes: set[str] = set()
    for source, target in edges:
        nodes.add(source)
        nodes.add(target)
    return NetworkGraph(nodes=nodes, edges=list(edges))


__all__ = ["NetworkGraph", "build_network"]
