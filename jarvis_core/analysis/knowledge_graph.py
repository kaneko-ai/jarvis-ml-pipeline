"""
JARVIS Knowledge Graph

6. 知識グラフ: 概念関係を可視化
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Node:
    """ノード."""

    id: str
    label: str
    node_type: str  # concept, paper, claim, author, entity
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.node_type,
            "properties": self.properties,
        }


@dataclass
class Edge:
    """エッジ."""

    source: str
    target: str
    edge_type: str  # cites, mentions, supports, contradicts, coauthor
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.edge_type,
            "weight": self.weight,
            "properties": self.properties,
        }


class KnowledgeGraph:
    """知識グラフ.

    概念・論文・主張の関係を管理
    """

    def __init__(self):
        """初期化."""
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []

    def add_node(
        self,
        node_id: str,
        label: str,
        node_type: str,
        properties: dict[str, Any] | None = None,
    ) -> Node:
        """ノードを追加."""
        if node_id in self.nodes:
            return self.nodes[node_id]

        node = Node(
            id=node_id,
            label=label,
            node_type=node_type,
            properties=properties or {},
        )
        self.nodes[node_id] = node
        return node

    def add_edge(
        self,
        source: str,
        target: str,
        edge_type: str,
        weight: float = 1.0,
        properties: dict[str, Any] | None = None,
    ) -> Edge:
        """エッジを追加."""
        edge = Edge(
            source=source,
            target=target,
            edge_type=edge_type,
            weight=weight,
            properties=properties or {},
        )
        self.edges.append(edge)
        return edge

    def add_paper(self, paper_id: str, title: str, **kwargs) -> Node:
        """論文ノードを追加."""
        return self.add_node(paper_id, title, "paper", kwargs)

    def add_concept(self, concept: str) -> Node:
        """概念ノードを追加."""
        concept_id = f"concept:{concept.lower().replace(' ', '_')}"
        return self.add_node(concept_id, concept, "concept")

    def add_claim(self, claim_id: str, claim_text: str, **kwargs) -> Node:
        """主張ノードを追加."""
        return self.add_node(claim_id, claim_text[:50], "claim", kwargs)

    def link_paper_concept(self, paper_id: str, concept: str, weight: float = 1.0):
        """論文と概念をリンク."""
        concept_node = self.add_concept(concept)
        self.add_edge(paper_id, concept_node.id, "mentions", weight)

    def link_papers(self, source_id: str, target_id: str, edge_type: str = "cites"):
        """論文間をリンク."""
        self.add_edge(source_id, target_id, edge_type)

    def link_claim_evidence(self, claim_id: str, evidence_id: str):
        """主張と根拠をリンク."""
        self.add_edge(claim_id, evidence_id, "supports")

    def get_neighbors(self, node_id: str) -> list[tuple[str, str, float]]:
        """隣接ノードを取得."""
        neighbors = []
        for edge in self.edges:
            if edge.source == node_id:
                neighbors.append((edge.target, edge.edge_type, edge.weight))
            elif edge.target == node_id:
                neighbors.append((edge.source, edge.edge_type, edge.weight))
        return neighbors

    def get_subgraph(self, node_ids: set[str]) -> KnowledgeGraph:
        """サブグラフを取得."""
        subgraph = KnowledgeGraph()

        for node_id in node_ids:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                subgraph.add_node(node.id, node.label, node.node_type, node.properties)

        for edge in self.edges:
            if edge.source in node_ids and edge.target in node_ids:
                subgraph.add_edge(edge.source, edge.target, edge.edge_type, edge.weight)

        return subgraph

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換."""
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
        }

    def save(self, path: str):
        """保存."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"Saved knowledge graph to {path}")

    def load(self, path: str):
        """読み込み."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        for node_data in data.get("nodes", []):
            self.add_node(
                node_data["id"],
                node_data["label"],
                node_data["type"],
                node_data.get("properties"),
            )

        for edge_data in data.get("edges", []):
            self.add_edge(
                edge_data["source"],
                edge_data["target"],
                edge_data["type"],
                edge_data.get("weight", 1.0),
                edge_data.get("properties"),
            )

        logger.info(f"Loaded knowledge graph from {path}")

    def to_networkx(self):
        """NetworkXグラフに変換."""
        try:
            import networkx as nx

            G = nx.DiGraph()

            for node in self.nodes.values():
                G.add_node(node.id, label=node.label, node_type=node.node_type, **node.properties)

            for edge in self.edges:
                G.add_edge(edge.source, edge.target, edge_type=edge.edge_type, weight=edge.weight)

            return G

        except ImportError:
            logger.warning("networkx not installed")
            return None

    def stats(self) -> dict[str, int]:
        """統計を取得."""
        node_types = {}
        for node in self.nodes.values():
            node_types[node.node_type] = node_types.get(node.node_type, 0) + 1

        edge_types = {}
        for edge in self.edges:
            edge_types[edge.edge_type] = edge_types.get(edge.edge_type, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": node_types,
            "edge_types": edge_types,
        }