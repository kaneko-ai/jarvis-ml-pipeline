#!/usr/bin/env python3
"""Launcher script for ops_extract Streamlit dashboard."""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path


def _resolve_run_dir(*, run_id: str | None, run_dir: str | None) -> Path:
    if run_dir:
        return Path(run_dir)
    if run_id:
        return Path("logs") / "runs" / str(run_id)
    raise ValueError("either --run-id or --run-dir is required")


def _missing_dashboard_extras() -> list[str]:
    required = ["streamlit", "plotly", "psutil"]
    missing = [name for name in required if importlib.util.find_spec(name) is None]
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch ops_extract dashboard")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-id")
    group.add_argument("--run-dir")
    args = parser.parse_args()

    missing = _missing_dashboard_extras()
    if missing:
        print("dashboard extras are missing:", ", ".join(missing))
        print("install with: uv pip install -e .[dashboard]")
        return 2

    run_dir = _resolve_run_dir(run_id=args.run_id, run_dir=args.run_dir)
    app = (
        Path(__file__).resolve().parents[1] / "jarvis_core" / "ops_extract" / "dashboard" / "app.py"
    )
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app),
        "--server.headless",
        "true",
        "--",
        "--run-dir",
        str(run_dir),
    ]
    return subprocess.run(cmd, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
