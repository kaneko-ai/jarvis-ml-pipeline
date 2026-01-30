"""Shared utilities for writing generation."""

from __future__ import annotations

from pathlib import Path


def load_overview(run_dir: Path) -> str:
    overview_path = run_dir / "notes" / "00_RUN_OVERVIEW.md"
    if overview_path.exists():
        return overview_path.read_text(encoding="utf-8")
    return ""