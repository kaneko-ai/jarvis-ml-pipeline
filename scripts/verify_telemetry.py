#!/usr/bin/env python
"""Verify Telemetry Generation.

Per RP-18, this script verifies that events.jsonl was generated correctly.
Exit 0 = success, Exit 1 = failure.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_KEYS = ["run_id", "trace_id", "event", "event_type"]


def find_latest_run(logs_dir: str = "logs/runs") -> Path | None:
    """Find the latest run directory."""
    logs_path = Path(logs_dir)
    if not logs_path.exists():
        return None

    runs = sorted(logs_path.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0] if runs else None


def verify_events_file(events_file: Path) -> tuple[bool, list[str]]:
    """Verify events.jsonl has required keys.

    Returns:
        (success, errors)
    """
    errors = []

    if not events_file.exists():
        errors.append(f"File not found: {events_file}")
        return False, errors

    if events_file.stat().st_size == 0:
        errors.append(f"File is empty: {events_file}")
        return False, errors

    try:
        with open(events_file, "r", encoding="utf-8") as f:
            first_line = f.readline()

        if not first_line.strip():
            errors.append("First line is empty")
            return False, errors

        event = json.loads(first_line)

        for key in REQUIRED_KEYS:
            if key not in event:
                errors.append(f"Missing required key: {key}")

    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
        return False, errors

    return len(errors) == 0, errors


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Verify telemetry generation")
    parser.add_argument("--run-id", help="Specific run ID to verify")
    parser.add_argument("--logs-dir", default="logs/runs", help="Logs directory")

    args = parser.parse_args()

    if args.run_id:
        run_dir = Path(args.logs_dir) / args.run_id
    else:
        run_dir = find_latest_run(args.logs_dir)

    if run_dir is None:
        print("ERROR: No runs found", file=sys.stderr)
        sys.exit(1)

    events_file = run_dir / "events.jsonl"
    print(f"Checking: {events_file}")

    success, errors = verify_events_file(events_file)

    if success:
        print("✓ Telemetry verification PASSED")
        print(f"  Run ID: {run_dir.name}")
        print(f"  Events file: {events_file}")
        sys.exit(0)
    else:
        print("✗ Telemetry verification FAILED", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
