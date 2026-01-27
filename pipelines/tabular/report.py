"""
Tabular Report Module

実行サマリ出力（json/markdown）
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


@dataclass
class RunReport:
    """実行レポート."""

    run_id: str
    task: str
    dataset: Dict[str, Any]
    metrics: Dict[str, float]
    submission_checks: Dict[str, bool]
    config_path: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        """Markdown形式で出力."""
        lines = [
            f"# Run Report: {self.run_id}",
            "",
            f"**Task**: {self.task}",
            f"**Timestamp**: {self.timestamp}",
            f"**Config**: {self.config_path}",
            "",
            "## Dataset",
            "| Key | Value |",
            "|-----|-------|",
        ]

        for k, v in self.dataset.items():
            lines.append(f"| {k} | {v} |")

        lines.extend(
            [
                "",
                "## Metrics",
                "| Metric | Value |",
                "|--------|-------|",
            ]
        )

        for k, v in self.metrics.items():
            lines.append(f"| {k} | {v:.4f} |")

        lines.extend(
            [
                "",
                "## Submission Checks",
            ]
        )

        for k, v in self.submission_checks.items():
            status = "✅" if v else "❌"
            lines.append(f"- {k}: {status}")

        return "\n".join(lines)


def generate_report(
    run_id: str,
    task: str,
    dataset_info: Dict[str, Any],
    metrics: Dict[str, float],
    submission_checks: Dict[str, bool],
    config_path: str,
    output_dir: str,
) -> RunReport:
    """
    レポートを生成・保存.

    Args:
        run_id: 実行ID
        task: タスク種別
        dataset_info: データセット情報
        metrics: メトリクス
        submission_checks: 提出チェック結果
        config_path: 設定ファイルパス
        output_dir: 出力ディレクトリ

    Returns:
        RunReport
    """
    report = RunReport(
        run_id=run_id,
        task=task,
        dataset=dataset_info,
        metrics=metrics,
        submission_checks=submission_checks,
        config_path=config_path,
        timestamp=datetime.now().isoformat(),
    )

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # JSON保存
    json_path = out_path / "report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

    # Markdown保存
    md_path = out_path / "report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report.to_markdown())

    logger.info(f"Report saved: {out_path}")

    return report
