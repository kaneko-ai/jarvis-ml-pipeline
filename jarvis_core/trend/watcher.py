"""
JARVIS Trend Watcher

論文・技術・実装トレンドの定期収集と週次レポート生成
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .ranker import RankScore, TrendRanker
from .sources.base import TrendItem, TrendSource

logger = logging.getLogger(__name__)


@dataclass
class TrendReport:
    """週次トレンドレポート."""

    report_id: str
    generated_at: str
    period_start: str
    period_end: str
    items: list[TrendItem] = field(default_factory=list)
    ranked_items: list[tuple[TrendItem, RankScore]] = field(default_factory=list)
    issues: list[dict[str, Any]] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Markdown形式でレポートを生成."""
        lines = [
            f"# Trend Report: {self.report_id}",
            "",
            f"**Generated**: {self.generated_at}",
            f"**Period**: {self.period_start} ~ {self.period_end}",
            "",
            "## Top Trends",
            "",
        ]

        for i, (item, score) in enumerate(self.ranked_items[:10], 1):
            lines.append(f"### {i}. {item.title}")
            lines.append("")
            lines.append(f"- **Source**: {item.source}")
            lines.append(f"- **Score**: {score.total:.2f}")
            lines.append(f"- **Novelty**: {score.novelty:.2f}")
            lines.append(f"- **Relevance**: {score.relevance:.2f}")
            if item.abstract:
                lines.append("")
                lines.append(f"> {item.abstract[:300]}...")
            lines.append("")

        if self.issues:
            lines.append("## Improvement Issues")
            lines.append("")
            for issue in self.issues[:5]:
                lines.append(f"- **{issue.get('title', 'N/A')}**: {issue.get('description', '')}")

        return "\n".join(lines)

    def save(self, output_dir: str = "reports/trends") -> Path:
        """レポートを保存."""
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)

        # Markdown
        md_path = path / f"{self.report_id}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self.to_markdown())

        # JSON
        json_path = path / f"{self.report_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "report_id": self.report_id,
                    "generated_at": self.generated_at,
                    "period_start": self.period_start,
                    "period_end": self.period_end,
                    "items_count": len(self.items),
                    "issues": self.issues,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        return md_path


class TrendWatcher:
    """トレンドウォッチャー.

    arXiv / PubMed / Zenn / DAIR.AI 等から並列収集。
    """

    def __init__(self, sources: list[TrendSource] | None = None, ranker: TrendRanker | None = None):
        """
        初期化.

        Args:
            sources: トレンドソースリスト
            ranker: ランカー
        """
        self.sources = sources or []
        self.ranker = ranker or TrendRanker()

    def add_source(self, source: TrendSource) -> None:
        """ソースを追加."""
        self.sources.append(source)

    def collect(
        self, queries: list[str], max_per_source: int = 50, period_days: int = 7
    ) -> list[TrendItem]:
        """
        全ソースからトレンドを収集.

        Args:
            queries: 検索クエリリスト
            max_per_source: ソースごとの最大取得数
            period_days: 何日前までを対象とするか

        Returns:
            TrendItemリスト
        """
        all_items: list[TrendItem] = []

        for source in self.sources:
            try:
                items = source.fetch(queries, max_results=max_per_source)
                all_items.extend(items)
                logger.info(f"Collected {len(items)} items from {source.name}")
            except Exception as e:
                logger.error(f"Failed to collect from {source.name}: {e}")

        # 重複除去
        seen_ids = set()
        unique_items = []
        for item in all_items:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                unique_items.append(item)

        logger.info(f"Total unique items: {len(unique_items)}")
        return unique_items

    def generate_report(
        self, items: list[TrendItem], period_start: str, period_end: str
    ) -> TrendReport:
        """
        トレンドレポートを生成.

        Args:
            items: TrendItemリスト
            period_start: 期間開始
            period_end: 期間終了

        Returns:
            TrendReport
        """
        # ランキング
        ranked = self.ranker.rank(items)

        # Issue生成
        issues = self._generate_issues(ranked[:10])

        report = TrendReport(
            report_id=f"trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now().isoformat(),
            period_start=period_start,
            period_end=period_end,
            items=items,
            ranked_items=ranked,
            issues=issues,
        )

        return report

    def _generate_issues(
        self, top_items: list[tuple[TrendItem, RankScore]]
    ) -> list[dict[str, Any]]:
        """改善Issueを生成（DoD駆動）."""
        issues = []

        for item, score in top_items:
            if score.relevance > 0.7:
                issues.append(
                    {
                        "title": f"Review: {item.title[:50]}...",
                        "description": f"High relevance ({score.relevance:.2f}) trend detected",
                        "source": item.source,
                        "item_id": item.id,
                        "dod": [
                            "Abstract reviewed",
                            "Relevance to JARVIS assessed",
                            "Decision logged to Experience",
                        ],
                    }
                )

        return issues
