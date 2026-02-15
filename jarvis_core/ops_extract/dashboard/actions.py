"""Dashboard action helpers."""

from __future__ import annotations

import subprocess
import sys
from typing import Sequence


def run_cli(cmd: Sequence[str], timeout_sec: int = 60) -> tuple[int, str, str]:
    """Run a CLI command safely and return (rc, stdout, stderr)."""
    if not cmd:
        return 2, "", "empty_command"
    normalized = [str(part) for part in cmd]
    if normalized[0] == "javisctl":
        normalized = [sys.executable, "-m", "jarvis_core.ops_extract.cli.javisctl", *normalized[1:]]
    try:
        proc = subprocess.run(
            normalized,
            capture_output=True,
            text=True,
            check=False,
            timeout=max(1, int(timeout_sec)),
        )
        return int(proc.returncode), proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return 124, stdout, f"timeout_after_{timeout_sec}s\n{stderr}".strip()
    except Exception as exc:
        return 1, "", str(exc)
