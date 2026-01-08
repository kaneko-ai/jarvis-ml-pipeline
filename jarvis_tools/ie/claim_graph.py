"""ITER2-02: Claim Graph構築 (Claim Graph).

主張間の関係をグラフとして構築。
- 関係抽出
- グラフ構造
- パス探索
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class ClaimNode:
    """主張ノード."""
    claim_id: str
    claim_text: str
    paper_id: str
    claim_type: str
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text[:100],
            "paper_id": self.paper_id,
            "claim_type": self.claim_type,
            "confidence": self.confidence,
        }


@dataclass
class ClaimEdge:
    """主張エッジ."""
    source_id: str
    target_id: str
    relation_type: str  # supports, contradicts, extends, same_as
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "relation": self.relation_type,
            "confidence": self.confidence,
        }


class ClaimGraph:
    """主張グラフ.
    
    主張間の関係をグラフとして管理。
    """

    RELATION_TYPES = [
        "supports",      # 支持する
        "contradicts",   # 矛盾する
        "extends",       # 拡張する
        "same_as",       # 同じ主張
        "cites",         # 引用する
        "implies",       # 暗示する
    ]

    def __init__(self):
        self._nodes: Dict[str, ClaimNode] = {}
        self._edges: List[ClaimEdge] = []
        self._adjacency: Dict[str, List[ClaimEdge]] = {}

    def add_node(self, node: ClaimNode) -> None:
        """ノードを追加."""
        self._nodes[node.claim_id] = node
        if node.claim_id not in self._adjacency:
            self._adjacency[node.claim_id] = []

    def add_edge(self, edge: ClaimEdge) -> None:
        """エッジを追加."""
        self._edges.append(edge)

        if edge.source_id not in self._adjacency:
            self._adjacency[edge.source_id] = []
        self._adjacency[edge.source_id].append(edge)

    def get_neighbors(
        self,
        claim_id: str,
        relation_type: Optional[str] = None,
    ) -> List[Tuple[ClaimNode, ClaimEdge]]:
        """隣接ノードを取得."""
        edges = self._adjacency.get(claim_id, [])

        if relation_type:
            edges = [e for e in edges if e.relation_type == relation_type]

        results = []
        for edge in edges:
            target = self._nodes.get(edge.target_id)
            if target:
                results.append((target, edge))

        return results

    def find_supporting_claims(self, claim_id: str) -> List[ClaimNode]:
        """支持する主張を検索."""
        neighbors = self.get_neighbors(claim_id, "supports")
        return [node for node, _ in neighbors]

    def find_contradicting_claims(self, claim_id: str) -> List[ClaimNode]:
        """矛盾する主張を検索."""
        neighbors = self.get_neighbors(claim_id, "contradicts")
        return [node for node, _ in neighbors]

    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
    ) -> List[List[ClaimEdge]] | None:
        """2つの主張間のパスを探索."""
        if source_id not in self._nodes or target_id not in self._nodes:
            return None

        # BFS
        queue: List[Tuple[str, List[ClaimEdge]]] = [(source_id, [])]
        visited: Set[str] = set()
        paths = []

        while queue and len(paths) < 10:
            current, path = queue.pop(0)

            if current == target_id and path:
                paths.append(path)
                continue

            if len(path) >= max_depth:
                continue

            if current in visited:
                continue
            visited.add(current)

            for edge in self._adjacency.get(current, []):
                new_path = path + [edge]
                queue.append((edge.target_id, new_path))

        return paths if paths else None

    def get_cluster(self, claim_id: str, max_depth: int = 2) -> Set[str]:
        """主張のクラスタを取得."""
        visited: Set[str] = set()
        queue: List[Tuple[str, int]] = [(claim_id, 0)]

        while queue:
            current, depth = queue.pop(0)

            if current in visited:
                continue
            visited.add(current)

            if depth >= max_depth:
                continue

            for edge in self._adjacency.get(current, []):
                queue.append((edge.target_id, depth + 1))

        return visited

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges],
        }

    @classmethod
    def from_claims(
        cls,
        claims: List[Dict[str, Any]],
        detect_relations: bool = True,
    ) -> "ClaimGraph":
        """主張リストからグラフを構築."""
        graph = cls()

        # ノード追加
        for claim in claims:
            node = ClaimNode(
                claim_id=claim.get("claim_id", ""),
                claim_text=claim.get("claim_text", ""),
                paper_id=claim.get("paper_id", ""),
                claim_type=claim.get("claim_type", "fact"),
                confidence=claim.get("confidence", 0.5),
            )
            graph.add_node(node)

        # 関係検出
        if detect_relations:
            graph._detect_relations()

        return graph

    def _detect_relations(self) -> None:
        """主張間の関係を自動検出."""
        nodes = list(self._nodes.values())

        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                # 同じ論文からの主張
                if node1.paper_id == node2.paper_id:
                    # 簡易的な類似度チェック
                    similarity = self._text_similarity(node1.claim_text, node2.claim_text)

                    if similarity > 0.8:
                        self.add_edge(ClaimEdge(
                            source_id=node1.claim_id,
                            target_id=node2.claim_id,
                            relation_type="same_as",
                            confidence=similarity,
                        ))
                    elif similarity > 0.5:
                        self.add_edge(ClaimEdge(
                            source_id=node1.claim_id,
                            target_id=node2.claim_id,
                            relation_type="supports",
                            confidence=similarity,
                        ))

    def _text_similarity(self, text1: str, text2: str) -> float:
        """テキスト類似度を計算."""
        import re

        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)


def build_claim_graph(claims: List[Dict[str, Any]]) -> ClaimGraph:
    """便利関数: 主張グラフを構築."""
    return ClaimGraph.from_claims(claims)
