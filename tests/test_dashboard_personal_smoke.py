from __future__ import annotations

import sys
from pathlib import Path

from jarvis_core.ops_extract.dashboard.actions import run_cli
from jarvis_core.ops_extract.dashboard.app import _discover_runs, _format_eta, _load_jsonl


def test_dashboard_helpers_smoke(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_dir = runs_dir / "r1"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_metadata.json").write_text(
        '{"created_at":"2026-01-01T00:00:00+00:00","status":"success"}',
        encoding="utf-8",
    )
    rows = _discover_runs(runs_dir)
    assert rows and rows[0]["run_id"] == "r1"
    assert _format_eta(65) == "00:01:05"
    assert _load_jsonl(run_dir / "missing.jsonl") == []


def test_dashboard_actions_run_cli() -> None:
    rc, out, err = run_cli([sys.executable, "-c", "print('ok')"], timeout_sec=10)
    assert rc == 0
    assert "ok" in out
    assert err == ""
