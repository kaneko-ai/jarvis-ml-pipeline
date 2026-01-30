"""Performance Report.

Per V4.2 Sprint 2, this outputs Span/SLO/Budget/Cache statistics in fixed schema.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class PerfReport:
    """Performance report with fixed schema."""

    # Metadata
    run_id: str
    timestamp: datetime
    workflow: str = ""

    # Span statistics
    span_stats: dict[str, dict] = field(default_factory=dict)
    total_duration_ms: float = 0.0

    # SLO status
    slo_violations: list[str] = field(default_factory=list)
    slo_status: str = "passed"  # passed, warning, failed

    # Budget usage
    budget_usage: dict[str, dict] = field(default_factory=dict)

    # Cache statistics
    cache_stats: dict[str, Any] = field(default_factory=dict)

    # Index statistics
    index_stats: dict[str, dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to fixed-schema dict."""
        return {
            "schema_version": "1.0",
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "workflow": self.workflow,
            "spans": {
                "by_name": self.span_stats,
                "total_duration_ms": round(self.total_duration_ms, 2),
            },
            "slo": {
                "status": self.slo_status,
                "violations": self.slo_violations,
            },
            "budget": self.budget_usage,
            "cache": self.cache_stats,
            "index": self.index_stats,
        }

    def save(self, path: str) -> None:
        """Save report to JSON."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


def generate_perf_report(
    run_id: str,
    workflow: str = "",
    span_tracker: Any | None = None,
    slo_status: Any | None = None,
    budget_manager: Any | None = None,
    cache: Any | None = None,
    index_pipeline: Any | None = None,
) -> PerfReport:
    """Generate performance report from components.

    Args:
        run_id: Run identifier.
        workflow: Workflow name.
        span_tracker: SpanTracker instance.
        slo_status: SLOStatus instance.
        budget_manager: BudgetManager instance.
        cache: MultiLevelCache instance.
        index_pipeline: IndexPipeline instance.

    Returns:
        PerfReport with collected statistics.
    """
    report = PerfReport(
        run_id=run_id,
        timestamp=datetime.now(),
        workflow=workflow,
    )

    # Collect span statistics
    if span_tracker:
        summary = span_tracker.get_summary()
        report.span_stats = summary
        report.total_duration_ms = sum(s.get("total_ms", 0) for s in summary.values())

    # Collect SLO status
    if slo_status:
        report.slo_violations = [v.value for v in slo_status.violations]
        if slo_status.violations:
            report.slo_status = "failed"

    # Collect budget usage
    if budget_manager:
        report.budget_usage = budget_manager.get_status()

    # Collect cache statistics
    if cache:
        report.cache_stats = cache.get_stats()

    # Collect index statistics
    if index_pipeline:
        report.index_stats = index_pipeline.get_summary()

    return report


def format_perf_report_md(report: PerfReport) -> str:
    """Format report as markdown."""
    lines = [
        "# Performance Report",
        "",
        f"**Run ID**: {report.run_id}",
        f"**Timestamp**: {report.timestamp.isoformat()}",
        f"**Workflow**: {report.workflow}",
        f"**Total Duration**: {report.total_duration_ms:.0f}ms",
        "",
        "## SLO Status",
        f"**Status**: {report.slo_status.upper()}",
    ]

    if report.slo_violations:
        lines.append("**Violations**:")
        for v in report.slo_violations:
            lines.append(f"  - {v}")
    lines.append("")

    lines.append("## Span Summary")
    lines.append("| Stage | Count | Duration (ms) |")
    lines.append("|-------|-------|---------------|")
    for name, stats in report.span_stats.items():
        lines.append(f"| {name} | {stats.get('count', 0)} | {stats.get('total_ms', 0):.0f} |")
    lines.append("")

    if report.cache_stats:
        lines.append("## Cache Statistics")
        lines.append(f"- L1 Hits: {report.cache_stats.get('l1_hits', 0)}")
        lines.append(f"- L2 Hits: {report.cache_stats.get('l2_hits', 0)}")
        lines.append(f"- Misses: {report.cache_stats.get('misses', 0)}")
        lines.append(f"- Hit Rate: {report.cache_stats.get('hit_rate', 0):.1%}")
        lines.append("")

    if report.budget_usage:
        lines.append("## Budget Usage")
        for resource, data in report.budget_usage.items():
            if isinstance(data, dict) and "percent" in data:
                lines.append(f"- {resource}: {data['percent']:.1f}%")

    return "\n".join(lines)
