from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ERRORS_JS = ROOT / "dashboard" / "assets" / "errors.js"
UI_JS = ROOT / "dashboard" / "assets" / "ui.js"
RUN_HTML = ROOT / "dashboard" / "run.html"


def test_not_implemented_message_is_defined() -> None:
    errors_content = ERRORS_JS.read_text(encoding="utf-8")
    assert "NOT_IMPLEMENTED_MESSAGE" in errors_content
    assert "未実装：バックエンドAPIが存在しません" in errors_content


def test_not_implemented_banner_renderer_exists() -> None:
    ui_content = UI_JS.read_text(encoding="utf-8")
    assert "renderNotImplementedBanner" in ui_content
    assert "未実装：バックエンドAPIが存在しません" in ui_content


def test_run_page_uses_not_implemented_banner() -> None:
    run_content = RUN_HTML.read_text(encoding="utf-8")
    assert "submission-not-implemented" in run_content
    assert "renderNotImplementedBanner" in run_content
