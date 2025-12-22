"""Profile Run.

Per RP-223, profiles run latency by stage.
"""
from __future__ import annotations

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime


def load_events(events_path: str) -> List[Dict[str, Any]]:
    """Load events from JSONL."""
    path = Path(events_path)
    if not path.exists():
        return []

    events = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))

    return events


def compute_stage_durations(events: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    """Compute duration per stage from events."""
    # Track start times
    stage_starts: Dict[str, str] = {}
    durations: Dict[str, List[float]] = defaultdict(list)

    for event in events:
        action = event.get("event", event.get("action", ""))
        timestamp = event.get("timestamp", "")

        if "_START" in action:
            stage = action.replace("_START", "")
            stage_starts[stage] = timestamp

        elif "_END" in action:
            stage = action.replace("_END", "")
            if stage in stage_starts:
                try:
                    start = datetime.fromisoformat(
                        stage_starts[stage].replace("Z", "+00:00")
                    )
                    end = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    duration = (end - start).total_seconds()
                    durations[stage].append(duration)
                except Exception:
                    pass

    return dict(durations)


def compute_percentiles(values: List[float]) -> Dict[str, float]:
    """Compute p50 and p95."""
    if not values:
        return {"p50": 0, "p95": 0}

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    p50_idx = int(n * 0.5)
    p95_idx = int(n * 0.95)

    return {
        "p50": sorted_vals[min(p50_idx, n - 1)],
        "p95": sorted_vals[min(p95_idx, n - 1)],
        "avg": sum(values) / n,
    }


def profile_run(
    run_id: str,
    runs_dir: str = "data/runs",
) -> Dict[str, Any]:
    """Profile a single run.

    Args:
        run_id: Run ID.
        runs_dir: Runs directory.

    Returns:
        Profile dict with stage durations.
    """
    events_path = Path(runs_dir) / run_id / "events.jsonl"
    if not events_path.exists():
        # Try logs dir
        events_path = Path("logs/runs") / run_id / "events.jsonl"

    events = load_events(str(events_path))
    durations = compute_stage_durations(events)

    profile = {
        "run_id": run_id,
        "stages": {},
    }

    for stage, times in durations.items():
        profile["stages"][stage] = {
            "count": len(times),
            **compute_percentiles(times),
        }

    # Find slowest stages
    sorted_stages = sorted(
        profile["stages"].items(),
        key=lambda x: x[1].get("p95", 0),
        reverse=True,
    )

    profile["slowest_stages"] = [s[0] for s in sorted_stages[:3]]

    return profile


def format_profile(profile: Dict[str, Any]) -> str:
    """Format profile as text."""
    lines = [f"Profile: {profile['run_id']}", "=" * 40, ""]

    for stage, data in profile.get("stages", {}).items():
        lines.append(f"{stage}:")
        lines.append(f"  Count: {data['count']}")
        lines.append(f"  P50: {data['p50']:.2f}s")
        lines.append(f"  P95: {data['p95']:.2f}s")
        lines.append("")

    if profile.get("slowest_stages"):
        lines.append(f"Slowest: {', '.join(profile['slowest_stages'])}")

    return "\n".join(lines)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Profile run latency")
    parser.add_argument("--run-id", type=str, required=True)
    parser.add_argument("--runs-dir", type=str, default="data/runs")
    parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    profile = profile_run(args.run_id, args.runs_dir)

    if args.json:
        print(json.dumps(profile, indent=2))
    else:
        print(format_profile(profile))


if __name__ == "__main__":
    main()
