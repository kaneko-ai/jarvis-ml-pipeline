from __future__ import annotations

import json
from pathlib import Path

from jarvis_core.bundle.assembler import BundleAssembler


def _base_context() -> dict:
    return {
        "run_id": "r1",
        "task_id": "t1",
        "goal": "test goal",
        "query": "test goal",
        "pipeline": "test",
        "timestamp": "2026-02-16T00:00:00+00:00",
        "seed": 42,
        "model": "mock",
    }


def _base_artifacts() -> dict:
    return {
        "papers": [],
        "claims": [],
        "evidence": [],
        "scores": {},
        "answer": "ok",
        "citations": [],
        "warnings": [],
    }


def _result_status(run_dir: Path) -> str:
    payload = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    return str(payload["status"])


def test_status_success_when_gate_passed(tmp_path: Path):
    assembler = BundleAssembler(tmp_path / "run_success")
    assembler.build(
        _base_context(),
        _base_artifacts(),
        quality_report={"gate_passed": True, "fail_reasons": []},
    )
    assert _result_status(tmp_path / "run_success") == "success"


def test_status_needs_retry_when_non_fatal(tmp_path: Path):
    assembler = BundleAssembler(tmp_path / "run_retry")
    assembler.build(
        _base_context(),
        _base_artifacts(),
        quality_report={
            "gate_passed": False,
            "fail_reasons": [{"code": "CITATION_MISSING", "msg": "missing citation"}],
        },
    )
    assert _result_status(tmp_path / "run_retry") == "needs_retry"


def test_status_failed_when_fatal(tmp_path: Path):
    assembler = BundleAssembler(tmp_path / "run_failed")
    assembler.build(
        _base_context(),
        _base_artifacts(),
        quality_report={
            "gate_passed": False,
            "fail_reasons": [{"code": "INPUT_INVALID", "msg": "bad input"}],
        },
    )
    assert _result_status(tmp_path / "run_failed") == "failed"


def test_quality_report_none_is_needs_retry_and_records_reason(tmp_path: Path):
    run_dir = tmp_path / "run_none"
    assembler = BundleAssembler(run_dir)
    assembler.build(_base_context(), _base_artifacts(), quality_report=None)

    assert _result_status(run_dir) == "needs_retry"
    eval_summary = json.loads((run_dir / "eval_summary.json").read_text(encoding="utf-8"))
    assert eval_summary["gate_passed"] is False
    assert any(reason.get("code") == "VERIFY_NOT_RUN" for reason in eval_summary["fail_reasons"])

    warning_rows = [
        json.loads(line)
        for line in (run_dir / "warnings.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(row.get("code") == "VERIFY_NOT_RUN" for row in warning_rows)
    report_text = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "VERIFY_NOT_RUN" in report_text
