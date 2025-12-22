#!/usr/bin/env python
"""Replay a previous run.

Per RP-03, this script replays execution using cached results.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_run_info(run_dir: Path) -> dict:
    """Load run information from logs directory."""
    info = {"run_id": run_dir.name}

    # Load config if exists
    config_path = run_dir / "run_config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            info["config"] = json.load(f)

    # Load events
    events_path = run_dir / "events.jsonl"
    if events_path.exists():
        events = []
        with open(events_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        info["events"] = events
        info["event_count"] = len(events)

    return info


def replay_run(run_id: str, logs_dir: str = "logs/runs") -> dict:
    """Replay a previous run.

    For now, this just loads the run info and validates it can be replayed.
    Full replay requires the cache to have tool results.

    Args:
        run_id: ID of the run to replay.
        logs_dir: Directory containing run logs.

    Returns:
        Replay result.
    """
    run_dir = Path(logs_dir) / run_id

    if not run_dir.exists():
        return {"success": False, "error": f"Run directory not found: {run_dir}"}

    info = load_run_info(run_dir)

    # Check for cache hits in events
    cache_hits = 0
    cache_misses = 0

    for event in info.get("events", []):
        if event.get("cache_hit") is True:
            cache_hits += 1
        elif event.get("cache_hit") is False:
            cache_misses += 1

    return {
        "success": True,
        "run_id": run_id,
        "event_count": info.get("event_count", 0),
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "config": info.get("config"),
    }


def main():
    parser = argparse.ArgumentParser(description="Replay a previous run")
    parser.add_argument("run_id", help="Run ID to replay")
    parser.add_argument("--logs-dir", default="logs/runs", help="Logs directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    result = replay_run(args.run_id, args.logs_dir)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print(f"Run: {result['run_id']}")
            print(f"Events: {result['event_count']}")
            print(f"Cache hits: {result['cache_hits']}")
            print(f"Cache misses: {result['cache_misses']}")
        else:
            print(f"Error: {result['error']}")
            sys.exit(1)


if __name__ == "__main__":
    main()
