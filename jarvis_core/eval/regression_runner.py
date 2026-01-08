"""Regression Runner.

Per V4-A05, this runs regression benchmarks and detects degradation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .metrics_truth import TruthMetrics, calculate_truth_metrics


@dataclass
class RegressionResult:
    """Result of regression run."""

    run_id: str
    timestamp: datetime
    metrics: TruthMetrics
    baseline_metrics: TruthMetrics | None
    is_regression: bool
    regression_reasons: list[str]
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics.to_dict(),
            "baseline_metrics": self.baseline_metrics.to_dict() if self.baseline_metrics else None,
            "is_regression": self.is_regression,
            "regression_reasons": self.regression_reasons,
            "metadata": self.metadata,
        }


def run_regression(
    predictions: list[dict],
    baseline_path: str | None = None,
    thresholds: dict[str, float] = None,
) -> RegressionResult:
    """Run regression test.

    Args:
        predictions: Current predictions to evaluate.
        baseline_path: Path to baseline metrics JSON.
        thresholds: Acceptable degradation thresholds.

    Returns:
        RegressionResult with comparison.
    """
    thresholds = thresholds or {
        "unsupported_fact_rate": 0.05,  # Max 5% degradation
        "fact_precision": 0.05,
        "fact_recall": 0.05,
    }

    # Calculate current metrics
    current = calculate_truth_metrics(predictions)

    # Load baseline if exists
    baseline = None
    if baseline_path and Path(baseline_path).exists():
        with open(baseline_path, encoding="utf-8") as f:
            data = json.load(f)
            baseline = TruthMetrics(
                unsupported_fact_rate=data.get("unsupported_fact_rate", 0),
                downgrade_rate=data.get("downgrade_rate", 0),
                fact_precision=data.get("fact_precision", 1),
                fact_recall=data.get("fact_recall", 1),
                total_claims=data.get("total_claims", 0),
                facts_with_evidence=data.get("facts_with_evidence", 0),
                facts_without_evidence=data.get("facts_without_evidence", 0),
                inferences=data.get("inferences", 0),
                unsupported=data.get("unsupported", 0),
                flags=[],
            )

    # Check for regression
    is_regression = False
    reasons = []

    if baseline:
        # Higher unsupported rate is bad
        delta = current.unsupported_fact_rate - baseline.unsupported_fact_rate
        if delta > thresholds.get("unsupported_fact_rate", 0.05):
            is_regression = True
            reasons.append(f"unsupported_fact_rate increased: {baseline.unsupported_fact_rate:.2%} → {current.unsupported_fact_rate:.2%}")

        # Lower precision is bad
        delta = baseline.fact_precision - current.fact_precision
        if delta > thresholds.get("fact_precision", 0.05):
            is_regression = True
            reasons.append(f"fact_precision decreased: {baseline.fact_precision:.2%} → {current.fact_precision:.2%}")

        # Lower recall is bad
        delta = baseline.fact_recall - current.fact_recall
        if delta > thresholds.get("fact_recall", 0.05):
            is_regression = True
            reasons.append(f"fact_recall decreased: {baseline.fact_recall:.2%} → {current.fact_recall:.2%}")

    return RegressionResult(
        run_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
        timestamp=datetime.now(),
        metrics=current,
        baseline_metrics=baseline,
        is_regression=is_regression,
        regression_reasons=reasons,
    )


def save_baseline(metrics: TruthMetrics, path: str) -> None:
    """Save metrics as baseline."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics.to_dict(), f, indent=2)


def generate_regression_report(result: RegressionResult) -> str:
    """Generate markdown regression report."""
    lines = [
        "# Regression Report",
        "",
        f"**Run ID**: {result.run_id}",
        f"**Timestamp**: {result.timestamp.isoformat()}",
        f"**Status**: {'❌ REGRESSION DETECTED' if result.is_regression else '✅ PASSED'}",
        "",
        "## Current Metrics",
        f"- Unsupported FACT Rate: {result.metrics.unsupported_fact_rate:.2%}",
        f"- Downgrade Rate: {result.metrics.downgrade_rate:.2%}",
        f"- FACT Precision: {result.metrics.fact_precision:.2%}",
        f"- FACT Recall: {result.metrics.fact_recall:.2%}",
        "",
    ]

    if result.baseline_metrics:
        lines.extend([
            "## Baseline Comparison",
            f"- Unsupported FACT Rate: {result.baseline_metrics.unsupported_fact_rate:.2%}",
            f"- FACT Precision: {result.baseline_metrics.fact_precision:.2%}",
            f"- FACT Recall: {result.baseline_metrics.fact_recall:.2%}",
            "",
        ])

    if result.regression_reasons:
        lines.extend([
            "## Regression Reasons",
            "",
        ])
        for reason in result.regression_reasons:
            lines.append(f"- {reason}")

    return "\n".join(lines)
