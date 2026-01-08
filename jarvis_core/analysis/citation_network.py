"""
JARVIS Citation Network

9. 引用ネットワーク: 被引用数・引用関係の分析
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CitationNode:
    """引用ノード."""
    paper_id: str
    title: str
    year: int
    citations_count: int = 0
    cited_by: list[str] = field(default_factory=list)
    cites: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "year": self.year,
            "citations_count": self.citations_count,
            "cited_by": self.cited_by,
            "cites": self.cites,
        }


@dataclass
class CitationStats:
    """引用統計."""
    total_papers: int
    total_citations: int
    avg_citations: float
    most_cited: list[tuple[str, int]]
    citation_distribution: dict[str, int]  # year -> count

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_papers": self.total_papers,
            "total_citations": self.total_citations,
            "avg_citations": self.avg_citations,
            "most_cited": self.most_cited,
            "citation_distribution": self.citation_distribution,
        }


class CitationNetwork:
    """引用ネットワーク.
    
    論文間の引用関係を分析
    """

    def __init__(self):
        """初期化."""
        self.nodes: dict[str, CitationNode] = {}

    def add_paper(
        self,
        paper_id: str,
        title: str,
        year: int,
        citations_count: int = 0,
    ) -> CitationNode:
        """論文を追加."""
        if paper_id in self.nodes:
            return self.nodes[paper_id]

        node = CitationNode(
            paper_id=paper_id,
            title=title,
            year=year,
            citations_count=citations_count,
        )
        self.nodes[paper_id] = node
        return node

    def add_citation(self, citing_id: str, cited_id: str):
        """引用関係を追加."""
        if citing_id in self.nodes:
            self.nodes[citing_id].cites.append(cited_id)

        if cited_id in self.nodes:
            self.nodes[cited_id].cited_by.append(citing_id)
            self.nodes[cited_id].citations_count += 1

    def get_stats(self) -> CitationStats:
        """統計を取得."""
        if not self.nodes:
            return CitationStats(
                total_papers=0,
                total_citations=0,
                avg_citations=0.0,
                most_cited=[],
                citation_distribution={},
            )

        total_citations = sum(n.citations_count for n in self.nodes.values())
        avg_citations = total_citations / len(self.nodes)

        # 最も引用されている論文
        sorted_nodes = sorted(
            self.nodes.values(),
            key=lambda n: n.citations_count,
            reverse=True,
        )
        most_cited = [(n.paper_id, n.citations_count) for n in sorted_nodes[:10]]

        # 年ごとの分布
        distribution = {}
        for node in self.nodes.values():
            year_str = str(node.year)
            distribution[year_str] = distribution.get(year_str, 0) + 1

        return CitationStats(
            total_papers=len(self.nodes),
            total_citations=total_citations,
            avg_citations=avg_citations,
            most_cited=most_cited,
            citation_distribution=distribution,
        )

    def find_influential_papers(self, top_n: int = 5) -> list[CitationNode]:
        """影響力のある論文を検索."""
        sorted_nodes = sorted(
            self.nodes.values(),
            key=lambda n: n.citations_count,
            reverse=True,
        )
        return sorted_nodes[:top_n]

    def find_citing_chain(
        self,
        paper_id: str,
        max_depth: int = 3,
    ) -> list[list[str]]:
        """引用チェーンを検索."""
        chains = []

        def dfs(current: str, path: list[str], depth: int):
            if depth >= max_depth:
                chains.append(path)
                return

            node = self.nodes.get(current)
            if not node or not node.cites:
                chains.append(path)
                return

            for cited in node.cites[:3]:  # 最大3つまで
                dfs(cited, path + [cited], depth + 1)

        if paper_id in self.nodes:
            dfs(paper_id, [paper_id], 0)

        return chains

    def to_networkx(self):
        """NetworkXグラフに変換."""
        try:
            import networkx as nx

            G = nx.DiGraph()

            for node in self.nodes.values():
                G.add_node(node.paper_id, title=node.title, year=node.year)

            for node in self.nodes.values():
                for cited_id in node.cites:
                    if cited_id in self.nodes:
                        G.add_edge(node.paper_id, cited_id)

            return G

        except ImportError:
            logger.warning("networkx not installed")
            return None

    def generate_report(self) -> str:
        """レポートを生成."""
        stats = self.get_stats()
        influential = self.find_influential_papers(5)

        lines = [
            "# Citation Network Report",
            "",
            "## Overview",
            f"- Total papers: {stats.total_papers}",
            f"- Total citations: {stats.total_citations}",
            f"- Average citations: {stats.avg_citations:.2f}",
            "",
            "## Most Influential Papers",
        ]

        for i, node in enumerate(influential, 1):
            lines.append(f"{i}. **{node.title}** ({node.year}) - {node.citations_count} citations")

        lines.extend([
            "",
            "## Year Distribution",
        ])

        for year, count in sorted(stats.citation_distribution.items()):
            lines.append(f"- {year}: {count} papers")

        return "\n".join(lines)
