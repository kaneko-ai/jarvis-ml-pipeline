"""Live Evaluation Runner.

Per RP-17, this runs periodic evaluations for drift detection.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List


def run_live_eval(
    queries: List[str],
    output_dir: str = "reports/live",
    date: Optional[str] = None,
) -> dict:
    """Run a live evaluation session.

    Args:
        queries: List of test queries.
        output_dir: Output directory.
        date: Date string (defaults to today).

    Returns:
        Evaluation summary.
    """
    date = date or datetime.now().strftime("%Y-%m-%d")
    report_dir = Path(output_dir) / date
    report_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for query in queries:
        start = datetime.now()

        # Placeholder: would call run_task here
        result = {
            "query": query,
            "timestamp": start.isoformat(),
            "latency_ms": 0,
            "retrieval_success": True,
            "claim_count": 0,
            "citation_count": 0,
        }

        results.append(result)

    # Compute summary metrics
    summary = {
        "date": date,
        "query_count": len(queries),
        "avg_latency_ms": sum(r["latency_ms"] for r in results) / len(results) if results else 0,
        "retrieval_success_rate": sum(1 for r in results if r["retrieval_success"]) / len(results) if results else 0,
    }

    # Save results
    with open(report_dir / "results.jsonl", "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(report_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


# Default live queries (subset for monitoring)
DEFAULT_LIVE_QUERIES = [
    "CD73 immunotherapy",
    "PD-1 checkpoint",
    "CAR-T therapy",
]
