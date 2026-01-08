"""Run Until Success.

Per RP-191, runs until success or attempt exhaustion.
"""
from __future__ import annotations

import sys
import argparse
import json
from typing import Optional


def run_until_success(
    goal: str,
    category: str = "immuno",
    max_attempts: int = 3,
    quality_bar_path: Optional[str] = None,
) -> dict:
    """Run until success or attempts exhausted.

    Args:
        goal: Query/goal description.
        category: Query category (e.g., immuno).
        max_attempts: Maximum attempts.
        quality_bar_path: Optional path to quality bar config.

    Returns:
        Result dict with status, run_ids, and summary.
    """
    from jarvis_core.runtime.repair_policy import RepairPolicy
    from jarvis_core.runtime.repair_loop import RepairLoop, StopReason

    run_ids = []
    attempt = 0

    # Create policy
    policy = RepairPolicy(max_attempts=max_attempts)

    # Placeholder run function (would integrate with run_task)
    def run_fn(config):
        nonlocal attempt
        attempt += 1
        run_id = f"run_{attempt}"
        run_ids.append(run_id)

        # In real implementation, this calls run_task
        return {
            "run_id": run_id,
            "status": "success" if attempt >= max_attempts else "partial",
        }

    def quality_fn(result):
        return result.get("status") == "success"

    loop = RepairLoop(policy, run_fn, quality_fn)
    result = loop.run({"goal": goal, "category": category})

    return {
        "status": "success" if result.stop_reason == StopReason.SUCCESS else "failed",
        "stop_reason": result.stop_reason.value,
        "attempts": result.attempts,
        "run_ids": run_ids,
        "final_result": result.final_result,
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run until success")
    parser.add_argument("--goal", type=str, required=True, help="Query/goal")
    parser.add_argument("--category", type=str, default="immuno")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--quality-bar", type=str, default=None)
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    result = run_until_success(
        goal=args.goal,
        category=args.category,
        max_attempts=args.attempts,
        quality_bar_path=args.quality_bar,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Status: {result['status']}")
        print(f"Stop Reason: {result['stop_reason']}")
        print(f"Attempts: {result['attempts']}")
        print(f"Run IDs: {', '.join(result['run_ids'])}")

    # Exit codes per RP-191
    if result["status"] == "success":
        sys.exit(0)
    elif result["stop_reason"] == "max_attempts":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
