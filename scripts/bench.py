"""Benchmark Runner.

Per RP-232, runs deterministic benchmarks for performance comparison.
"""

from __future__ import annotations

import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timezone


def run_benchmark(
    cases_path: str,
    iterations: int = 3,
    output_dir: str = "reports/bench/latest",
) -> Dict[str, Any]:
    """Run benchmark on cases.

    Args:
        cases_path: Path to benchmark cases (JSONL).
        iterations: Number of iterations per case.
        output_dir: Output directory.

    Returns:
        Benchmark results.
    """
    # Load cases from JSONL or JSON array for compatibility.
    path = Path(cases_path)
    cases = []
    if path.exists():
        raw = path.read_text(encoding="utf-8").strip()
        if raw:
            try:
                payload = json.loads(raw)
                if isinstance(payload, list):
                    cases = payload
                elif isinstance(payload, dict):
                    cases = [payload]
            except json.JSONDecodeError:
                for line in raw.splitlines():
                    if line.strip():
                        cases.append(json.loads(line))

    results = []

    for case in cases:
        case_times = []

        for i in range(iterations):
            start = time.time()

            # Placeholder - would run actual processing
            time.sleep(0.01)  # Simulate work

            elapsed = time.time() - start
            case_times.append(elapsed)

        results.append(
            {
                "case_id": case.get("id") or case.get("paper_id", "unknown"),
                "iterations": iterations,
                "times": case_times,
                "avg": sum(case_times) / len(case_times),
                "p50": sorted(case_times)[len(case_times) // 2],
                "p95": (
                    sorted(case_times)[int(len(case_times) * 0.95)]
                    if len(case_times) > 1
                    else case_times[0]
                ),
            }
        )

    # Aggregate
    all_avgs = [r["avg"] for r in results]
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cases": len(cases),
        "iterations": iterations,
        "overall_avg": sum(all_avgs) / len(all_avgs) if all_avgs else 0,
        "results": results,
    }

    # Save
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    with open(out_path / "bench_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run benchmark")
    parser.add_argument(
        "--cases",
        type=str,
        default="docs/evals/bench_cases.jsonl",
    )
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--output", type=str, default="reports/bench/latest")

    args = parser.parse_args()

    result = run_benchmark(args.cases, args.iterations, args.output)

    print(f"Benchmark completed: {result['cases']} cases")
    print(f"Overall avg: {result['overall_avg']:.3f}s")


if __name__ == "__main__":
    main()
