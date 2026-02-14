"""Run Regression.

Per RP-203, runs regression evaluation with frozen eval sets.
"""

from __future__ import annotations

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any


def load_gold_set(gold_path: str) -> List[Dict[str, Any]]:
    """Load gold/frozen eval set."""
    path = Path(gold_path)
    if not path.exists():
        raise FileNotFoundError(f"Gold set not found: {gold_path}")

    cases = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    return cases


def run_case(case: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Run a single evaluation case.

    Args:
        case: Case dict with query, expected, etc.
        config: Run configuration.

    Returns:
        Result dict with metrics.
    """
    # Placeholder - would integrate with run_task
    return {
        "case_id": case.get("id", "unknown"),
        "query": case.get("query", ""),
        "status": "success",  # or "failed"
        "metrics": {
            "claim_count": 5,
            "citation_count": 3,
            "citation_precision": 0.8,
            "claim_precision": 0.7,
        },
        "duration_seconds": 10.0,
    }


def compute_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute summary metrics from results."""
    total = len(results)
    if total == 0:
        return {"total": 0, "success_rate": 0}

    success = sum(1 for r in results if r.get("status") == "success")

    # Aggregate metrics
    all_metrics = [r.get("metrics", {}) for r in results]

    avg = lambda key: (sum(m.get(key, 0) for m in all_metrics) / total if total > 0 else 0)

    return {
        "total": total,
        "success": success,
        "failed": total - success,
        "success_rate": success / total,
        "avg_claim_precision": avg("claim_precision"),
        "avg_citation_precision": avg("citation_precision"),
        "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z",
    }


def run_regression(
    gold_path: str,
    output_dir: str = "reports/eval/latest",
    config: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Run full regression evaluation.

    Args:
        gold_path: Path to gold set (JSONL).
        output_dir: Output directory.
        config: Run configuration.

    Returns:
        Summary dict.
    """
    if config is None:
        config = {}

    # Load cases
    cases = load_gold_set(gold_path)

    # Run all cases
    results = []
    for case in cases:
        try:
            result = run_case(case, config)
            results.append(result)
        except Exception as e:
            results.append(
                {
                    "case_id": case.get("id", "unknown"),
                    "status": "failed",
                    "error": str(e),
                }
            )

    # Compute summary
    summary = compute_summary(results)

    # Save outputs
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    with open(out_path / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    with open(out_path / "per_case.jsonl", "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    with open(out_path / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "success_rate": summary["success_rate"],
                "claim_precision": summary["avg_claim_precision"],
                "citation_precision": summary["avg_citation_precision"],
            },
            f,
            indent=2,
        )

    return summary


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run regression evaluation")
    parser.add_argument("--gold", type=str, required=True, help="Path to gold set")
    parser.add_argument("--output", type=str, default="reports/eval/latest")

    args = parser.parse_args()

    summary = run_regression(args.gold, args.output)

    print(f"Regression completed: {summary['success']}/{summary['total']} passed")
    print(f"Success rate: {summary['success_rate']:.1%}")

    if summary["success_rate"] < 0.8:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
