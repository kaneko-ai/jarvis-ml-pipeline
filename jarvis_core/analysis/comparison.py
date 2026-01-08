"""
JARVIS Comparison Analysis

8. 比較分析: 論文間の手法・結果比較表を自動生成
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ComparisonRow:
    """比較行."""
    paper_id: str
    title: str
    year: int
    method: str
    sample_size: str
    key_result: str
    limitations: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "year": self.year,
            "method": self.method,
            "sample_size": self.sample_size,
            "key_result": self.key_result,
            "limitations": self.limitations,
        }


@dataclass
class ComparisonTable:
    """比較表."""
    title: str
    columns: list[str]
    rows: list[ComparisonRow] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "columns": self.columns,
            "rows": [r.to_dict() for r in self.rows],
        }

    def to_markdown(self) -> str:
        """Markdown表に変換."""
        lines = [
            f"# {self.title}",
            "",
            "| Paper | Year | Method | Sample | Key Result | Limitations |",
            "|-------|------|--------|--------|------------|-------------|",
        ]

        for row in self.rows:
            lines.append(
                f"| {row.title[:30]}... | {row.year} | {row.method[:20]} | "
                f"{row.sample_size} | {row.key_result[:30]}... | {row.limitations[:20]} |"
            )

        return "\n".join(lines)

    def to_html(self) -> str:
        """HTML表に変換."""
        rows_html = ""
        for row in self.rows:
            rows_html += f"""
            <tr>
                <td>{row.title}</td>
                <td>{row.year}</td>
                <td>{row.method}</td>
                <td>{row.sample_size}</td>
                <td>{row.key_result}</td>
                <td>{row.limitations}</td>
            </tr>
            """

        return f"""
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Paper</th>
                    <th>Year</th>
                    <th>Method</th>
                    <th>Sample</th>
                    <th>Key Result</th>
                    <th>Limitations</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        """


class ComparisonAnalyzer:
    """比較分析器.
    
    論文間の手法・結果を比較
    """

    def __init__(self, llm_client=None):
        """初期化."""
        self.llm_client = llm_client

    def analyze(
        self,
        papers: list[dict[str, Any]],
        claims: list[dict[str, Any]] | None = None,
    ) -> ComparisonTable:
        """比較分析を実行.
        
        Args:
            papers: 論文リスト
            claims: 主張リスト（オプション）
        
        Returns:
            比較表
        """
        rows = []

        for paper in papers:
            # 各論文から情報を抽出
            row = self._extract_comparison_info(paper, claims)
            rows.append(row)

        table = ComparisonTable(
            title="Paper Comparison",
            columns=["Paper", "Year", "Method", "Sample", "Key Result", "Limitations"],
            rows=rows,
        )

        logger.info(f"Generated comparison table with {len(rows)} papers")
        return table

    def _extract_comparison_info(
        self,
        paper: dict[str, Any],
        claims: list[dict[str, Any]] | None,
    ) -> ComparisonRow:
        """論文から比較情報を抽出."""
        paper_id = paper.get("paper_id", "")

        # 関連するclaimを取得
        paper_claims = []
        if claims:
            paper_claims = [c for c in claims if c.get("paper_id") == paper_id]

        # 方法を推定
        method = "Not specified"
        abstract = paper.get("abstract", "").lower()
        if "randomized" in abstract:
            method = "RCT"
        elif "cohort" in abstract:
            method = "Cohort study"
        elif "meta-analysis" in abstract:
            method = "Meta-analysis"
        elif "review" in abstract:
            method = "Review"
        elif "in vitro" in abstract:
            method = "In vitro"
        elif "animal" in abstract or "mice" in abstract:
            method = "Animal study"

        # 主要な結果
        key_result = ""
        for claim in paper_claims:
            if claim.get("claim_type") == "finding":
                key_result = claim.get("claim_text", "")[:100]
                break

        if not key_result:
            key_result = paper.get("abstract", "")[:100]

        return ComparisonRow(
            paper_id=paper_id,
            title=paper.get("title", "Unknown"),
            year=paper.get("year", 0),
            method=method,
            sample_size="Not specified",
            key_result=key_result,
            limitations="See paper",
        )

    def generate_summary(self, table: ComparisonTable) -> str:
        """比較サマリーを生成."""
        years = [r.year for r in table.rows if r.year]
        methods = [r.method for r in table.rows]

        method_counts = {}
        for m in methods:
            method_counts[m] = method_counts.get(m, 0) + 1

        most_common_method = max(method_counts, key=method_counts.get) if method_counts else "Unknown"

        summary = f"""
## Comparison Summary

- **Total papers**: {len(table.rows)}
- **Year range**: {min(years) if years else 'N/A'} - {max(years) if years else 'N/A'}
- **Most common method**: {most_common_method}
- **Methods distribution**: {method_counts}
"""
        return summary
