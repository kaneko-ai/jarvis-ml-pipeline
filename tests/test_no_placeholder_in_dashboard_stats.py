from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_PY = ROOT / "jarvis_web" / "dashboard.py"


def test_dashboard_stats_has_no_placeholder_literals() -> None:
    content = DASHBOARD_PY.read_text(encoding="utf-8")
    assert "Placeholder" not in content
    assert "papers_indexed=1000" not in content
