from __future__ import annotations

from pathlib import Path

import pytest

from jarvis_core.ops_extract.run_lock import acquire_run_lock, release_run_lock


def test_run_lock_prevents_double_run(tmp_path: Path):
    run_dir = tmp_path / "run"
    lock_path = acquire_run_lock(run_dir)
    try:
        with pytest.raises(RuntimeError):
            acquire_run_lock(run_dir)
    finally:
        release_run_lock(lock_path)
