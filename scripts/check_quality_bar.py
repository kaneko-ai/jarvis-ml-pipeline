"""Quality Bar Checker.

Per RP-204, checks if metrics meet quality bar thresholds.
"""
from __future__ import annotations

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any


# Default thresholds from QUALITY_BAR.md
DEFAULT_THRESHOLDS = {
    "success_rate": 0.80,
    "claim_precision": 0.70,
    "citation_precision": 0.60,
    "entity_hit_rate": 0.60,
}


def load_metrics(metrics_path: str) -> Dict[str, float]:
    """Load metrics from JSON file."""
    path = Path(metrics_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics not found: {metrics_path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_quality_bar(
    metrics: Dict[str, float],
    thresholds: Dict[str, float] = None,
) -> Dict[str, Any]:
    """Check metrics against quality bar.

    Args:
        metrics: Actual metrics.
        thresholds: Target thresholds.

    Returns:
        Result dict with pass/fail per metric and overall.
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    results = {}
    all_passed = True

    for key, target in thresholds.items():
        actual = metrics.get(key, 0)
        passed = actual >= target
        results[key] = {
            "target": target,
            "actual": actual,
            "passed": passed,
        }
        if not passed:
            all_passed = False

    return {
        "passed": all_passed,
        "results": results,
    }


def format_report(check_result: Dict[str, Any]) -> str:
    """Format check result as report."""
    lines = ["Quality Bar Check", "=" * 40, ""]

    for key, data in check_result["results"].items():
        status = "✓" if data["passed"] else "✗"
        lines.append(
            f"{status} {key}: {data['actual']:.2%} "
            f"(target: {data['target']:.2%})"
        )

    lines.append("")
    if check_result["passed"]:
        lines.append("✓ All quality bars met!")
    else:
        lines.append("✗ Quality bar not met")

    return "\n".join(lines)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Check quality bar")
    parser.add_argument(
        "--metrics",
        type=str,
        default="reports/eval/latest/metrics.json",
    )
    parser.add_argument("--threshold-file", type=str, default=None)

    args = parser.parse_args()

    # Load metrics
    metrics = load_metrics(args.metrics)

    # Load custom thresholds if provided
    thresholds = None
    if args.threshold_file:
        with open(args.threshold_file) as f:
            thresholds = json.load(f)

    # Check
    result = check_quality_bar(metrics, thresholds)

    # Report
    print(format_report(result))

    # Exit code
    if result["passed"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
