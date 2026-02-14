#!/usr/bin/env python
"""Run Viewer.

Per RP-37, displays events.jsonl in human-readable format.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_events(events_file: Path) -> list:
    """Load events from JSONL."""
    events = []
    with open(events_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    return events


def format_event(event: dict) -> str:
    """Format a single event."""
    ts = event.get("ts", "")[:19]  # Trim microseconds
    level = event.get("level", "INFO")
    evt = event.get("event", "?")
    tool = event.get("tool", "")
    agent = event.get("agent", "")

    level_icon = {"INFO": "ℹ️", "WARN": "⚠️", "ERROR": "❌"}.get(level, "•")

    detail = tool if tool else agent if agent else ""
    if detail:
        detail = f"[{detail}]"

    return f"{ts} {level_icon} {evt} {detail}"


def main():
    parser = argparse.ArgumentParser(description="View run events")
    parser.add_argument("--run-id", type=str, help="Run ID")
    parser.add_argument("--logs-dir", type=str, default="logs/runs")
    parser.add_argument("--filter-event", type=str, help="Filter by event name")
    parser.add_argument("--filter-level", type=str, help="Filter by level (ERROR, WARN)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    logs_path = Path(args.logs_dir)

    if args.run_id:
        run_dir = logs_path / args.run_id
    else:
        # Find latest
        runs = sorted(logs_path.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        if not runs:
            print("No runs found", file=sys.stderr)
            sys.exit(1)
        run_dir = runs[0]

    events_file = run_dir / "events.jsonl"
    if not events_file.exists():
        print(f"No events.jsonl in {run_dir}", file=sys.stderr)
        sys.exit(1)

    events = load_events(events_file)

    # Apply filters
    if args.filter_event:
        events = [e for e in events if args.filter_event in e.get("event", "")]
    if args.filter_level:
        events = [e for e in events if e.get("level") == args.filter_level]

    # Output
    print(f"=== Run: {run_dir.name} ===")
    print(f"Events: {len(events)}")
    print()

    if args.json:
        print(json.dumps(events, indent=2, ensure_ascii=False))
    else:
        print("Timeline:")
        print("-" * 60)
        for event in events:
            print(format_event(event))
        print("-" * 60)

        # Summary
        errors = [e for e in events if e.get("level") == "ERROR"]
        warns = [e for e in events if e.get("level") == "WARN"]

        if errors:
            print(f"\n❌ Errors: {len(errors)}")
            for e in errors[:3]:
                payload = e.get("payload", {})
                print(f"  - {e.get('event')}: {payload.get('error', '')[:50]}")

        if warns:
            print(f"\n⚠️ Warnings: {len(warns)}")


if __name__ == "__main__":
    main()
