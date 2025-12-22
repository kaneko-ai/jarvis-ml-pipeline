"""Diff Regression.

Per RP-209, generates diff between regression runs.
"""
from __future__ import annotations

import json
import argparse
from pathlib import Path
from typing import Dict, Any, List


def load_summary(summary_path: str) -> Dict[str, Any]:
    """Load regression summary."""
    path = Path(summary_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def compare_metrics(prev: Dict[str, Any], curr: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Compare metrics between runs."""
    diffs = []

    keys = ["success_rate", "avg_claim_precision", "avg_citation_precision"]

    for key in keys:
        prev_val = prev.get(key, 0)
        curr_val = curr.get(key, 0)
        delta = curr_val - prev_val

        status = "improved" if delta > 0.01 else ("regressed" if delta < -0.01 else "stable")

        diffs.append({
            "metric": key,
            "previous": prev_val,
            "current": curr_val,
            "delta": delta,
            "status": status,
        })

    return diffs


def generate_diff_summary(
    prev_dir: str,
    curr_dir: str,
    output_path: str = None,
) -> str:
    """Generate diff summary markdown.

    Args:
        prev_dir: Previous run directory.
        curr_dir: Current run directory.
        output_path: Optional output file path.

    Returns:
        Markdown summary.
    """
    prev = load_summary(Path(prev_dir) / "summary.json")
    curr = load_summary(Path(curr_dir) / "summary.json")

    diffs = compare_metrics(prev, curr)

    lines = ["# Regression Diff", "", "## Metrics Comparison", ""]
    lines.append("| Metric | Previous | Current | Delta | Status |")
    lines.append("|--------|----------|---------|-------|--------|")

    for d in diffs:
        delta_str = f"+{d['delta']:.2%}" if d["delta"] > 0 else f"{d['delta']:.2%}"
        lines.append(
            f"| {d['metric']} | {d['previous']:.2%} | {d['current']:.2%} | "
            f"{delta_str} | {d['status']} |"
        )

    lines.append("")

    # Overall verdict
    improved = sum(1 for d in diffs if d["status"] == "improved")
    regressed = sum(1 for d in diffs if d["status"] == "regressed")

    if regressed > 0:
        lines.append(f"⚠️ **{regressed} metric(s) regressed**")
    elif improved > 0:
        lines.append(f"✅ **{improved} metric(s) improved**")
    else:
        lines.append("➡️ **No significant changes**")

    content = "\n".join(lines)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(content, encoding="utf-8")

    return content


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Diff regression results")
    parser.add_argument("--prev", type=str, default="reports/eval/prev")
    parser.add_argument("--curr", type=str, default="reports/eval/latest")
    parser.add_argument("--output", type=str, default=None)

    args = parser.parse_args()

    diff = generate_diff_summary(args.prev, args.curr, args.output)
    print(diff)


if __name__ == "__main__":
    main()
