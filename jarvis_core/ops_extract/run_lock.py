"""Run lock helpers for preventing duplicate ops_extract executions."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


def acquire_run_lock(run_dir: Path, *, force: bool = False) -> Path:
    lock_path = run_dir / ".lock"
    if lock_path.exists() and not force:
        raise RuntimeError(f"run_lock_exists:{lock_path}")
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "pid": os.getpid(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(lock_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return lock_path


def release_run_lock(lock_path: Path) -> None:
    try:
        lock_path.unlink(missing_ok=True)
    except OSError:
        return


@contextmanager
def run_lock_context(run_dir: Path, *, force: bool = False) -> Iterator[Path]:
    lock_path = acquire_run_lock(run_dir, force=force)
    try:
        yield lock_path
    finally:
        release_run_lock(lock_path)

