"""Eval Balance Check.

Per PR-90, ensures frozen sets have balanced S1-S5 distribution.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List
from collections import defaultdict


# Minimum counts per category
MIN_COUNTS = {
    "S1": 5,
    "S2": 5,
    "S3": 5,
    "S4": 5,
    "S5": 5,
}


def check_balance(frozen_file: str) -> tuple[bool, Dict[str, int], List[str]]:
    """Check if frozen file has balanced distribution.

    Returns:
        (passed, category_counts, violations)
    """
    path = Path(frozen_file)
    if not path.exists():
        return False, {}, [f"File not found: {frozen_file}"]

    counts: Dict[str, int] = defaultdict(int)

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                category = entry.get("category", "unknown")
                counts[category] += 1

    violations = []
    for cat, min_count in MIN_COUNTS.items():
        actual = counts.get(cat, 0)
        if actual < min_count:
            violations.append(f"{cat}: {actual} < {min_count} (min)")

    passed = len(violations) == 0
    return passed, dict(counts), violations


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Check eval balance")
    parser.add_argument("--frozen", type=str, default="docs/evals/frozen_immuno_v2.jsonl")
    parser.add_argument("--min-per-category", type=int, default=5)

    args = parser.parse_args()

    # Update minimums
    for cat in MIN_COUNTS:
        MIN_COUNTS[cat] = args.min_per_category

    passed, counts, violations = check_balance(args.frozen)

    print(f"Frozen: {args.frozen}")
    print(f"Counts: {counts}")

    if passed:
        print("\n✓ Balance check passed")
        sys.exit(0)
    else:
        print("\n✗ Balance violations:")
        for v in violations:
            print(f"  - {v}")
        sys.exit(1)


if __name__ == "__main__":
    main()
