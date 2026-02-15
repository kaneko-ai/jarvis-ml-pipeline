from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_JS = ROOT / "dashboard" / "assets" / "app.js"


def test_personal_core_api_map_has_no_forbidden_keys() -> None:
    content = APP_JS.read_text(encoding="utf-8")
    forbidden = [
        "research_rank:",
        "research_paper:",
        "submission_build:",
        "submission_latest:",
        "submission_email:",
        "submission_changelog:",
        "schedules_list:",
        "schedules_create:",
        "schedules_update:",
        "schedules_run:",
    ]
    for key in forbidden:
        assert key not in content, f"Forbidden API key still exists: {key}"


def test_personal_core_api_map_has_required_keys() -> None:
    content = APP_JS.read_text(encoding="utf-8")
    required = [
        "health:",
        "health_cron:",
        "capabilities:",
        "runs_list:",
        "runs_detail:",
        "runs_files:",
        "runs_events:",
        "qa_report:",
        "feedback_risk:",
        "feedback_import:",
        "decision_simulate:",
    ]
    for key in required:
        assert key in content, f"Required API key missing: {key}"
