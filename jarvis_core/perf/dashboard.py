"""Dashboard & Scorecard.

Per V4.2 Sprint 3, this provides full dashboard output with fixed schema.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class DashboardData:
    """Full dashboard data with fixed schema."""

    schema_version: str = "1.0"

    # Run info
    run_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    workflow: str = ""

    # Performance
    total_duration_ms: float = 0.0
    span_stats: dict[str, dict] = field(default_factory=dict)
    top_slow_stages: list[dict] = field(default_factory=list)

    # Cost breakdown
    cost_breakdown: dict[str, float] = field(default_factory=dict)
    total_cost: float = 0.0

    # Cache statistics
    cache_hit_rate: float = 0.0
    cache_stats: dict[str, int] = field(default_factory=dict)

    # Quality metrics
    truth_metrics: dict[str, float] = field(default_factory=dict)
    regression_status: str = "unknown"

    # SLO status
    slo_status: str = "passed"
    slo_violations: list[str] = field(default_factory=list)

    # Budget status
    budget_usage_percent: float = 0.0
    budget_breakdown: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to fixed-schema dict."""
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "workflow": self.workflow,
            "performance": {
                "total_duration_ms": round(self.total_duration_ms, 2),
                "span_stats": self.span_stats,
                "top_slow_stages": self.top_slow_stages,
            },
            "cost": {
                "breakdown": self.cost_breakdown,
                "total": round(self.total_cost, 6),
            },
            "cache": {
                "hit_rate": round(self.cache_hit_rate, 4),
                "stats": self.cache_stats,
            },
            "quality": {
                "truth_metrics": self.truth_metrics,
                "regression_status": self.regression_status,
            },
            "slo": {
                "status": self.slo_status,
                "violations": self.slo_violations,
            },
            "budget": {
                "usage_percent": round(self.budget_usage_percent, 2),
                "breakdown": self.budget_breakdown,
            },
        }

    def save(self, path: str) -> None:
        """Save dashboard to JSON."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


def generate_dashboard(
    run_id: str,
    workflow: str = "",
    span_tracker: Any = None,
    cache: Any = None,
    budget_manager: Any = None,
    truth_metrics: Any = None,
    regression_result: Any = None,
    slo_status: Any = None,
    cost_model: Any = None,
) -> DashboardData:
    """Generate full dashboard from components.

    Args:
        run_id: Run identifier.
        workflow: Workflow name.
        span_tracker: SpanTracker instance.
        cache: MultiLevelCache instance.
        budget_manager: BudgetManager instance.
        truth_metrics: TruthMetrics instance.
        regression_result: RegressionResult instance.
        slo_status: SLOStatus instance.
        cost_model: CostModel instance.

    Returns:
        DashboardData with all metrics.
    """
    dashboard = DashboardData(
        run_id=run_id,
        timestamp=datetime.now(),
        workflow=workflow,
    )

    # Span statistics
    if span_tracker:
        summary = span_tracker.get_summary()
        dashboard.span_stats = summary
        dashboard.total_duration_ms = sum(s.get("total_ms", 0) for s in summary.values())

        # Top slow stages
        sorted_stages = sorted(
            summary.items(),
            key=lambda x: x[1].get("total_ms", 0),
            reverse=True,
        )
        dashboard.top_slow_stages = [
            {"stage": k, "duration_ms": v.get("total_ms", 0)} for k, v in sorted_stages[:5]
        ]

    # Cache statistics
    if cache:
        stats = cache.get_stats()
        dashboard.cache_stats = {
            "l1_hits": stats.get("l1_hits", 0),
            "l2_hits": stats.get("l2_hits", 0),
            "misses": stats.get("misses", 0),
        }
        dashboard.cache_hit_rate = stats.get("hit_rate", 0)

    # Budget usage
    if budget_manager:
        status = budget_manager.get_status()
        dashboard.budget_breakdown = {
            k: v.get("percent", 0) for k, v in status.items() if isinstance(v, dict)
        }
        if "tokens" in status:
            dashboard.budget_usage_percent = status["tokens"].get("percent", 0)

    # Truth metrics
    if truth_metrics:
        dashboard.truth_metrics = truth_metrics.to_dict()

    # Regression status
    if regression_result:
        dashboard.regression_status = "failed" if regression_result.is_regression else "passed"

    # SLO status
    if slo_status:
        dashboard.slo_violations = [v.value for v in slo_status.violations]
        dashboard.slo_status = "failed" if slo_status.violations else "passed"

    # Cost breakdown
    if cost_model and span_tracker:
        costs = cost_model.estimate_from_spans(span_tracker.get_summary())
        dashboard.cost_breakdown = costs
        dashboard.total_cost = costs.get("total", 0)

    return dashboard


def format_dashboard_md(dashboard: DashboardData) -> str:
    """Format dashboard as markdown."""
    lines = [
        "# Dashboard",
        "",
        f"**Run ID**: {dashboard.run_id}",
        f"**Workflow**: {dashboard.workflow}",
        f"**Timestamp**: {dashboard.timestamp.isoformat()}",
        "",
        "## Summary",
        f"- **Total Duration**: {dashboard.total_duration_ms:.0f}ms",
        f"- **Total Cost**: ${dashboard.total_cost:.4f}",
        f"- **Cache Hit Rate**: {dashboard.cache_hit_rate:.1%}",
        f"- **Budget Used**: {dashboard.budget_usage_percent:.1f}%",
        "",
        "## Status",
        f"- **SLO**: {dashboard.slo_status.upper()}",
        f"- **Regression**: {dashboard.regression_status.upper()}",
        "",
    ]

    if dashboard.slo_violations:
        lines.append("### SLO Violations")
        for v in dashboard.slo_violations:
            lines.append(f"- {v}")
        lines.append("")

    lines.append("## Top Slow Stages")
    lines.append("| Stage | Duration (ms) |")
    lines.append("|-------|---------------|")
    for stage in dashboard.top_slow_stages:
        lines.append(f"| {stage['stage']} | {stage['duration_ms']:.0f} |")

    return "\n".join(lines)


@dataclass
class Scorecard:
    """Quality scorecard for releases."""

    run_id: str
    timestamp: datetime
    gates_passed: int
    gates_failed: int
    gates: list[dict]

    def save(self, path: str) -> None:
        """Save scorecard."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "run_id": self.run_id,
                    "timestamp": self.timestamp.isoformat(),
                    "gates_passed": self.gates_passed,
                    "gates_failed": self.gates_failed,
                    "gates": self.gates,
                },
                f,
                indent=2,
            )


def generate_scorecard(
    run_id: str,
    truth_metrics: Any = None,
    regression_result: Any = None,
    slo_status: Any = None,
) -> Scorecard:
    """Generate quality scorecard."""
    gates = []

    # Gate 1: Unsupported FACT rate
    if truth_metrics:
        gate1_passed = truth_metrics.unsupported_fact_rate <= 0.1
        gates.append(
            {
                "name": "Unsupported FACT Rate ≤ 10%",
                "passed": gate1_passed,
                "value": f"{truth_metrics.unsupported_fact_rate:.1%}",
            }
        )

    # Gate 2: No regression
    if regression_result:
        gate2_passed = not regression_result.is_regression
        gates.append(
            {
                "name": "No Quality Regression",
                "passed": gate2_passed,
                "value": (
                    "Passed" if gate2_passed else ", ".join(regression_result.regression_reasons)
                ),
            }
        )

    # Gate 3: SLO compliance
    if slo_status:
        gate3_passed = len(slo_status.violations) == 0
        gates.append(
            {
                "name": "SLO Compliance",
                "passed": gate3_passed,
                "value": (
                    "Passed" if gate3_passed else str(len(slo_status.violations)) + " violations"
                ),
            }
        )

    passed = sum(1 for g in gates if g["passed"])
    failed = len(gates) - passed

    return Scorecard(
        run_id=run_id,
        timestamp=datetime.now(),
        gates_passed=passed,
        gates_failed=failed,
        gates=gates,
    )