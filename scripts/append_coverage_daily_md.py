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


if __name__ == "__main__":
    print("Script structure OK")
