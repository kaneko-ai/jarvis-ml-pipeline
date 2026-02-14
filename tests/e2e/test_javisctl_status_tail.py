from __future__ import annotations

import json
from pathlib import Path

from jarvis_core.ops_extract.cli import javisctl


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_javisctl_status_and_tail(monkeypatch, capsys, tmp_path: Path):
    run_dir = tmp_path / "run"
    _write(run_dir / "run_metadata.json", '{"status":"success","finished_at":"2026-02-14T00:00:00+00:00"}')
    _write(run_dir / "sync_state.json", '{"state":"committed"}')
    _write(
        run_dir / "trace.jsonl",
        json.dumps({"stage_id": "preflight"}) + "\n" + json.dumps({"stage_id": "normalize_text"}) + "\n",
    )

    monkeypatch.setattr("sys.argv", ["javisctl", "status", "--run-dir", str(run_dir)])
    assert javisctl.main() == 0
    out = capsys.readouterr().out
    assert '"status": "success"' in out

    monkeypatch.setattr(
        "sys.argv",
        ["javisctl", "tail", "--run-dir", str(run_dir), "--lines", "1"],
    )
    assert javisctl.main() == 0
    out = capsys.readouterr().out
    assert "normalize_text" in out

