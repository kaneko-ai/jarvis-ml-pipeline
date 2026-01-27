#!/usr/bin/env python3
"""
Append daily coverage snapshot to docs/coverage_daily.md

Usage:
    python scripts/append_coverage_daily_md.py \
        --md docs/coverage_daily.md \
        --report artifacts/coverage_daily_term.txt

Environment Variables:
    COVERAGE_PHASE: 1 or 2 (default: 1)
    GITHUB_SHA: commit SHA (from GitHub Actions)
    GITHUB_REPOSITORY: owner/repo (from GitHub Actions)
    GITHUB_RUN_ID: workflow run ID (from GitHub Actions)
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo


TOTAL_RE = re.compile(r"^TOTAL\s+\d+\s+\d+\s+(\d+)%\s*$", re.MULTILINE)
TOTAL_RE_BRANCH = re.compile(
    r"^TOTAL\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)%\s*$", re.MULTILINE
)


@dataclass(frozen=True)
class Snapshot:
    """Immutable snapshot data."""

    date_jst: str
    phase: str
    total_pct: str
    commit_sha: str
    run_url: str
    notes: str = ""


def parse_total_percent(report_text: str) -> str:
    """Extract total coverage percentage from report output."""
    match = TOTAL_RE.search(report_text)
    if match:
        return f"{match.group(1)}%"

    match = TOTAL_RE_BRANCH.search(report_text)
    if match:
        return f"{match.group(1)}%"

    for line in report_text.splitlines():
        if line.strip().startswith("TOTAL"):
            parts = line.split()
            for part in reversed(parts):
                if part.endswith("%"):
                    return part

    raise ValueError(
        "Could not find TOTAL coverage percent in report output.\n"
        f"Report content:\n{report_text[:500]}"
    )


def get_previous_coverage(md_path: Path) -> Optional[str]:
    """Get the most recent coverage value from the MD file."""
    if not md_path.exists():
        return None

    content = md_path.read_text(encoding="utf-8")
    matches = re.findall(r"total_coverage:\s*(\d+%)", content)
    return matches[-1] if matches else None


def calculate_delta(current: str, previous: Optional[str]) -> str:
    """Calculate coverage delta string."""
    if not previous:
        return ""

    try:
        curr_val = int(current.rstrip("%"))
        prev_val = int(previous.rstrip("%"))
        delta = curr_val - prev_val
        if delta > 0:
            return f" (+{delta}%)"
        if delta < 0:
            return f" ({delta}%)"
        return " (±0%)"
    except ValueError:
        return ""


def ensure_header(md_path: Path) -> None:
    """Ensure the MD file exists with proper header."""
    if md_path.exists():
        content = md_path.read_text(encoding="utf-8").strip()
        if content and "# Daily Coverage Snapshot" in content:
            return

    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(
        "# Daily Coverage Snapshot\n\n"
        "> **Authority**: REFERENCE (Level 4, Non-binding)  \n"
        "> **Purpose**: 毎日1回のカバレッジ計測結果を時系列で蓄積する  \n"
        "> **Timezone**: Asia/Tokyo（JST）\n\n"
        "---\n\n"
        "## Log\n\n"
        "<!-- newest entries are appended at the end -->\n"
        "<!-- DO NOT EDIT MANUALLY -->\n",
        encoding="utf-8",
    )


def append_entry(md_path: Path, snap: Snapshot, delta: str) -> None:
    """Append a new entry to the MD file."""
    entry_lines = [
        f"\n### {snap.date_jst}",
        f"- phase: {snap.phase}",
        f"- total_coverage: {snap.total_pct}{delta}",
        f"- commit: `{snap.commit_sha}`",
    ]

    if snap.run_url:
        entry_lines.append(f"- workflow_run: {snap.run_url}")

    if snap.notes:
        entry_lines.append(f"- notes: {snap.notes}")

    entry_lines.append("")

    entry = "\n".join(entry_lines)

    current_content = md_path.read_text(encoding="utf-8")
    md_path.write_text(current_content + entry, encoding="utf-8")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Append daily coverage snapshot to MD file"
    )
    parser.add_argument(
        "--md",
        default="docs/coverage_daily.md",
        help="Path to coverage_daily.md",
    )
    parser.add_argument(
        "--report",
        default="artifacts/coverage_daily_term.txt",
        help="Path to coverage report text file",
    )
    parser.add_argument(
        "--phase",
        default=os.environ.get("COVERAGE_PHASE", "1"),
        help="Coverage phase (1 or 2)",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional notes to include",
    )
    args = parser.parse_args()

    md_path = Path(args.md)
    report_path = Path(args.report)

    if not report_path.exists():
        print(f"ERROR: Report file not found: {report_path}", file=sys.stderr)
        return 1

    ensure_header(md_path)

    try:
        report_text = report_path.read_text(encoding="utf-8")
        total_pct = parse_total_percent(report_text)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    jst = ZoneInfo("Asia/Tokyo")
    date_jst = datetime.now(tz=jst).strftime("%Y-%m-%d")

    commit_sha = os.environ.get("GITHUB_SHA", "")[:12] or "local"

    run_url = ""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    if repo and run_id:
        run_url = f"https://github.com/{repo}/actions/runs/{run_id}"

    previous_coverage = get_previous_coverage(md_path)
    delta = calculate_delta(total_pct, previous_coverage)

    snap = Snapshot(
        date_jst=date_jst,
        phase=str(args.phase),
        total_pct=total_pct,
        commit_sha=commit_sha,
        run_url=run_url,
        notes=args.notes,
    )

    append_entry(md_path, snap, delta)

    print(f"Appended coverage snapshot: {date_jst} - {total_pct}{delta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
