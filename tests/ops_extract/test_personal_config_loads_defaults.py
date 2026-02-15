from __future__ import annotations

from pathlib import Path

from jarvis_core.ops_extract.personal_config import load_personal_config


def test_personal_config_loads_defaults(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("JAVIS_LOGS_ROOT", raising=False)
    monkeypatch.delenv("JAVIS_RUNS_DIR", raising=False)
    monkeypatch.delenv("JAVIS_QUEUE_DIR", raising=False)
    monkeypatch.delenv("JAVIS_PAPER_COUNTER_PATH", raising=False)
    cfg = load_personal_config(repo_root=tmp_path)
    assert cfg["dashboard_default_mode"] == "personal"
    assert cfg["dashboard_autofollow_latest"] is True
    assert Path(cfg["runs_dir"]).is_absolute()
    assert Path(cfg["queue_dir"]).is_absolute()
    assert str(cfg["paper_counter_path"]).endswith(str(Path("logs") / "counters" / "papers.json"))
