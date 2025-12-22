#!/usr/bin/env python
"""Check Core Test Collection Count.

Per PR-60: Ensures core test count matches baseline.
"""
from __future__ import annotations

import subprocess
import sys
import re
from pathlib import Path


BASELINE_FILE = Path("docs/STATE_BASELINE.md")
EXPECTED_KEY = "core_test_collected"


def get_baseline_count() -> int:
    """Get expected count from STATE_BASELINE.md."""
    if not BASELINE_FILE.exists():
        return -1

    content = BASELINE_FILE.read_text(encoding="utf-8")
    match = re.search(rf"{EXPECTED_KEY}:\s*(\d+)", content)
    if match:
        return int(match.group(1))
    return -1


def get_actual_count() -> int:
    """Get actual collected test count."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-m", "core", "-q"],
        capture_output=True,
        text=True,
    )

    # Parse output: "88 tests collected"
    match = re.search(r"(\d+)\s+tests?\s+collected", result.stdout)
    if match:
        return int(match.group(1))

    # Fallback: count lines with "::" (test items)
    lines = [l for l in result.stdout.split("\n") if "::" in l]
    return len(lines)


def main():
    baseline = get_baseline_count()
    actual = get_actual_count()

    print(f"Baseline: {baseline}")
    print(f"Collected: {actual}")

    if baseline == -1:
        print(f"\nWARNING: No baseline found in {BASELINE_FILE}")
        print(f"Add '{EXPECTED_KEY}: {actual}' to establish baseline")
        sys.exit(0)  # Don't fail on first run

    if actual != baseline:
        print(f"\n❌ FAILED: Expected {baseline} core tests, found {actual}")
        print(f"   If this is intentional, update {BASELINE_FILE}")
        sys.exit(1)

    print(f"\n✓ Core test count matches baseline")
    sys.exit(0)


if __name__ == "__main__":
    main()
