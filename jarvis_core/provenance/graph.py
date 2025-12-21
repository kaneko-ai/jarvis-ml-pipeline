"""Provenance Graph.

Per V4-B02, this provides DAG tracking from Claim→Fact→Evidence→Source.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional


class NodeType(Enum):
    """Types of provenance nodes."""

    SOURCE = "source"      # PDF, URL
    CHUNK = "chunk"        # Extracted chunk
    EVIDENCE = "evidence"  # Evidence unit
    FACT = "fact"          # Verified fact
    INFERENCE = "inference"  # Derived inference
    CLAIM = "claim"        # Final claim
    ARTIFACT = "artifact"  # Output artifact


@dataclass
class ProvenanceNode:
    """A node in the provenance graph."""

    node_id: str
    node_type: NodeType
    content_hash: Optional[str] = None
    content_preview: str = ""
    metadata: dict = field(default_factory=dict)
    parents: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "content_hash": self.content_hash,
            "content_preview": self.content_preview[:100],
            "metadata": self.metadata,
            "parents": self.parents,
        }


class ProvenanceGraph:
    """DAG for tracking provenance."""

    def __init__(self):
        self.nodes: Dict[str, ProvenanceNode] = {}
        self.edges: List[tuple] = []

    def add_node(
        self,
        node_id: str,
        node_type: NodeType,
        content_hash: str = None,
        content_preview: str = "",
        metadata: dict = None,
    ) -> ProvenanceNode:
        """Add a node to the graph."""
        node = ProvenanceNode(
            node_id=node_id,
            node_type=node_type,
            content_hash=content_hash,
            content_preview=content_preview,
            metadata=metadata or {},
        )
        self.nodes[node_id] = node
        return node

    def add_edge(self, from_id: str, to_id: str, relation: str = "derives") -> None:
        """Add an edge from parent to child."""
        if to_id in self.nodes:
            self.nodes[to_id].parents.append(from_id)
        self.edges.append((from_id, to_id, relation))

    def get_ancestors(self, node_id: str) -> List[str]:
        """Get all ancestors of a node."""
        if node_id not in self.nodes:
            return []

        ancestors = set()
        to_visit = list(self.nodes[node_id].parents)

        while to_visit:
            parent_id = to_visit.pop()
            if parent_id in ancestors:
                continue
            ancestors.add(parent_id)
            if parent_id in self.nodes:
                to_visit.extend(self.nodes[parent_id].parents)

        return list(ancestors)

    def get_path_to_source(self, node_id: str) -> List[str]:
        """Get path from node to source."""
        if node_id not in self.nodes:
            return []

        path = [node_id]
        current = node_id

        while current in self.nodes and self.nodes[current].parents:
            parent = self.nodes[current].parents[0]  # Follow first parent
            path.append(parent)
            current = parent

        return path

    def to_dict(self) -> dict:
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [{"from": e[0], "to": e[1], "relation": e[2]} for e in self.edges],
        }

    def save(self, path: str) -> None:
        """Save graph to JSON."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "ProvenanceGraph":
        """Load graph from JSON."""
        graph = cls()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for node_id, node_data in data.get("nodes", {}).items():
            graph.nodes[node_id] = ProvenanceNode(
                node_id=node_data["node_id"],
                node_type=NodeType(node_data["node_type"]),
                content_hash=node_data.get("content_hash"),
                content_preview=node_data.get("content_preview", ""),
                metadata=node_data.get("metadata", {}),
                parents=node_data.get("parents", []),
            )

        for edge in data.get("edges", []):
            graph.edges.append((edge["from"], edge["to"], edge.get("relation", "derives")))

        return graph


def build_provenance_from_artifact(artifact) -> ProvenanceGraph:
    """Build provenance graph from an artifact."""
    graph = ProvenanceGraph()

    # Add artifact node
    graph.add_node(
        node_id=f"artifact_{artifact.kind}",
        node_type=NodeType.ARTIFACT,
        content_preview=artifact.kind,
    )

    # Add fact nodes
    for i, fact in enumerate(artifact.facts):
        fact_id = f"fact_{i}"
        graph.add_node(
            node_id=fact_id,
            node_type=NodeType.FACT,
            content_preview=fact.statement,
        )
        graph.add_edge(fact_id, f"artifact_{artifact.kind}")

        # Add evidence nodes
        for j, ref in enumerate(fact.evidence_refs):
            evidence_id = f"evidence_{i}_{j}"
            graph.add_node(
                node_id=evidence_id,
                node_type=NodeType.EVIDENCE,
                content_hash=ref.chunk_id,
                content_preview=ref.text_snippet,
                metadata={"locator": ref.source_locator},
            )
            graph.add_edge(evidence_id, fact_id)

    # Add inference nodes
    for i, inf in enumerate(artifact.inferences):
        inf_id = f"inference_{i}"
        graph.add_node(
            node_id=inf_id,
            node_type=NodeType.INFERENCE,
            content_preview=inf.statement,
            metadata={"method": inf.method},
        )
        graph.add_edge(inf_id, f"artifact_{artifact.kind}")

    return graph
