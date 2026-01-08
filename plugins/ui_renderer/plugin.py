"""
JARVIS UI Plugin - Dashboard Renderer

ダッシュボード用の結果レンダリング。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List

from jarvis_core.contracts.types import (
    Artifacts, ArtifactsDelta, RuntimeConfig, TaskContext
)


@dataclass
class DashboardWidget:
    """ダッシュボードウィジェット."""
    widget_id: str
    widget_type: str  # chart, table, text, graph
    title: str
    data: Dict[str, Any]
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardBundle:
    """ダッシュボードバンドル."""
    bundle_id: str
    title: str
    widgets: List[DashboardWidget] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "title": self.title,
            "widgets": [
                {"id": w.widget_id, "type": w.widget_type,
                 "title": w.title, "data": w.data, "config": w.config}
                for w in self.widgets
            ],
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class ChartRenderer:
    """チャートレンダラー."""

    def render_bar_chart(self,
                         labels: List[str],
                         values: List[float],
                         title: str = "Bar Chart") -> DashboardWidget:
        """棒グラフをレンダリング."""
        return DashboardWidget(
            widget_id=f"chart_{title.replace(' ', '_').lower()}",
            widget_type="chart",
            title=title,
            data={
                "type": "bar",
                "labels": labels,
                "datasets": [{"data": values}]
            },
            config={"responsive": True}
        )

    def render_line_chart(self,
                          labels: List[str],
                          datasets: List[Dict[str, Any]],
                          title: str = "Line Chart") -> DashboardWidget:
        """折れ線グラフをレンダリング."""
        return DashboardWidget(
            widget_id=f"chart_{title.replace(' ', '_').lower()}",
            widget_type="chart",
            title=title,
            data={
                "type": "line",
                "labels": labels,
                "datasets": datasets
            },
            config={"responsive": True}
        )

    def render_pie_chart(self,
                         labels: List[str],
                         values: List[float],
                         title: str = "Pie Chart") -> DashboardWidget:
        """円グラフをレンダリング."""
        return DashboardWidget(
            widget_id=f"chart_{title.replace(' ', '_').lower()}",
            widget_type="chart",
            title=title,
            data={
                "type": "pie",
                "labels": labels,
                "datasets": [{"data": values}]
            },
            config={"responsive": True}
        )

    def render_radar_chart(self,
                           labels: List[str],
                           values: List[float],
                           title: str = "Radar Chart") -> DashboardWidget:
        """レーダーチャートをレンダリング."""
        return DashboardWidget(
            widget_id=f"chart_{title.replace(' ', '_').lower()}",
            widget_type="chart",
            title=title,
            data={
                "type": "radar",
                "labels": labels,
                "datasets": [{"data": values}]
            },
            config={"responsive": True}
        )


class TableRenderer:
    """テーブルレンダラー."""

    def render_table(self,
                     headers: List[str],
                     rows: List[List[Any]],
                     title: str = "Table") -> DashboardWidget:
        """テーブルをレンダリング."""
        return DashboardWidget(
            widget_id=f"table_{title.replace(' ', '_').lower()}",
            widget_type="table",
            title=title,
            data={
                "headers": headers,
                "rows": rows
            },
            config={"sortable": True, "filterable": True}
        )

    def render_paper_table(self, papers: List[Dict[str, Any]]) -> DashboardWidget:
        """論文テーブルをレンダリング."""
        headers = ["タイトル", "著者", "年", "ジャーナル", "スコア"]
        rows = []

        for p in papers:
            rows.append([
                p.get("title", "")[:100],
                ", ".join(p.get("authors", [])[:3]),
                p.get("year", ""),
                p.get("journal", ""),
                f"{p.get('score', 0):.2f}"
            ])

        return self.render_table(headers, rows, "論文一覧")

    def render_claim_table(self, claims: List[Dict[str, Any]]) -> DashboardWidget:
        """Claimテーブルをレンダリング."""
        headers = ["ID", "主張", "タイプ", "根拠数", "信頼度"]
        rows = []

        for c in claims:
            rows.append([
                c.get("claim_id", ""),
                c.get("claim_text", "")[:150],
                c.get("claim_type", ""),
                len(c.get("evidence", [])),
                f"{c.get('confidence', 0):.2f}"
            ])

        return self.render_table(headers, rows, "主張一覧")


class GraphRenderer:
    """グラフ（ネットワーク）レンダラー."""

    def render_knowledge_graph(self, kg: Dict[str, Any]) -> DashboardWidget:
        """知識グラフをレンダリング."""
        nodes = []
        edges = []

        for eid, entity in kg.get("entities", {}).items():
            nodes.append({
                "id": eid,
                "label": entity.get("name", ""),
                "group": entity.get("type", "")
            })

        for rel in kg.get("relations", []):
            edges.append({
                "from": rel.get("source", ""),
                "to": rel.get("target", ""),
                "label": rel.get("type", "")
            })

        return DashboardWidget(
            widget_id="knowledge_graph",
            widget_type="graph",
            title="知識グラフ",
            data={"nodes": nodes, "edges": edges},
            config={"physics": True, "hierarchical": False}
        )


class SummaryRenderer:
    """要約レンダラー."""

    def render_summary(self, summary: str, title: str = "要約") -> DashboardWidget:
        """要約テキストをレンダリング."""
        return DashboardWidget(
            widget_id=f"summary_{title.replace(' ', '_').lower()}",
            widget_type="text",
            title=title,
            data={"content": summary, "format": "markdown"},
            config={}
        )

    def render_provenance(self, claims: List[Dict[str, Any]]) -> DashboardWidget:
        """根拠付きテキストをレンダリング."""
        content = "## 根拠付き主張\n\n"

        for claim in claims[:10]:
            content += f"### {claim.get('claim_id', '')}\n"
            content += f"{claim.get('claim_text', '')}\n\n"

            evidence = claim.get("evidence", [])
            if evidence:
                content += "**根拠:**\n"
                for e in evidence[:3]:
                    content += f"- {e.get('doc_id', '')}: {e.get('text', '')[:100]}\n"
            content += "\n"

        return DashboardWidget(
            widget_id="provenance_summary",
            widget_type="text",
            title="根拠付き主張",
            data={"content": content, "format": "markdown"},
            config={}
        )


class UIPlugin:
    """UI統合プラグイン."""

    def __init__(self):
        self.chart_renderer = ChartRenderer()
        self.table_renderer = TableRenderer()
        self.graph_renderer = GraphRenderer()
        self.summary_renderer = SummaryRenderer()
        self.is_active = False

    def activate(self, runtime: RuntimeConfig, config: Dict[str, Any]) -> None:
        self.is_active = True

    def run(self, context: TaskContext, artifacts: Artifacts) -> ArtifactsDelta:
        """UIバンドルを生成."""
        delta: ArtifactsDelta = {}

        widgets = []

        # 1. Summary widget
        if artifacts.summaries:
            first_summary = list(artifacts.summaries.values())[0] if artifacts.summaries else ""
            widgets.append(self.summary_renderer.render_summary(first_summary, "概要"))

        # 2. Paper table
        if artifacts.papers:
            paper_data = [
                {
                    "title": p.title,
                    "authors": p.authors,
                    "year": p.year,
                    "journal": p.journal,
                    "score": artifacts.scores.get(f"{p.doc_id}_importance",
                             type('', (), {'value': 0})()).value
                }
                for p in artifacts.papers
            ]
            widgets.append(self.table_renderer.render_paper_table(paper_data))

        # 3. Claim table
        if artifacts.claims:
            claim_data = [c.to_dict() for c in artifacts.claims]
            widgets.append(self.table_renderer.render_claim_table(claim_data))

        # 4. Score chart
        if artifacts.scores:
            labels = list(artifacts.scores.keys())[:10]
            values = [artifacts.scores[k].value for k in labels]
            widgets.append(self.chart_renderer.render_bar_chart(
                labels, values, "スコア分布"
            ))

        # 5. Knowledge graph
        if "knowledge_graph" in artifacts.graphs:
            widgets.append(self.graph_renderer.render_knowledge_graph(
                artifacts.graphs["knowledge_graph"]
            ))

        # 6. Provenance
        if artifacts.claims:
            claim_data = [c.to_dict() for c in artifacts.claims]
            widgets.append(self.summary_renderer.render_provenance(claim_data))

        # Create bundle
        bundle = DashboardBundle(
            bundle_id=f"bundle_{context.run_id}",
            title=f"JARVIS分析結果: {context.goal[:50]}",
            widgets=widgets,
            metadata={
                "goal": context.goal,
                "domain": context.domain,
                "papers_count": len(artifacts.papers),
                "claims_count": len(artifacts.claims)
            }
        )

        delta["dashboard_bundle"] = bundle.to_dict()

        return delta

    def deactivate(self) -> None:
        self.is_active = False


def get_ui_plugin() -> UIPlugin:
    return UIPlugin()
