"""Tests for scripts.quality_gate CI/legacy utilities."""

from __future__ import annotations

from pathlib import Path

from scripts.quality_gate import (
    GateResult,
    evaluate_ci_gates,
    evaluate_quality_gate,
    run_command,
)


def test_gate_result_defaults() -> None:
    gate = GateResult(name="ruff", passed=True, message="ok")
    assert gate.required is True
    assert gate.passed is True


def test_run_command_success_and_not_found() -> None:
    code, output = run_command(["python", "-c", "print('ok')"])
    assert code == 0
    assert "ok" in output

    bad_code, bad_output = run_command(["definitely_not_a_real_binary_td004"])
    assert bad_code == -1
    assert "Command not found" in bad_output


def test_evaluate_ci_gates_counts_required_and_optional_failures() -> None:
    summary = evaluate_ci_gates(
        [
            GateResult(name="ruff", passed=True, message="", required=True),
            GateResult(name="pytest", passed=False, message="boom", required=True),
            GateResult(name="bandit", passed=False, message="warn", required=False),
        ]
    )

    assert summary["required_failures"] == 1
    assert summary["optional_failures"] == 1
    assert summary["all_required_passed"] is False


def test_evaluate_quality_gate_run_dir_mode(tmp_path: Path) -> None:
    (tmp_path / "summary.json").write_text('{"papers": 2}', encoding="utf-8")
    (tmp_path / "stats.json").write_text('{"chunks": 3}', encoding="utf-8")
    (tmp_path / "report.md").write_text("Answer with citation [1]", encoding="utf-8")
    (tmp_path / "warnings.jsonl").write_text('{"code":"W"}\n', encoding="utf-8")

    result = evaluate_quality_gate(tmp_path)

    assert result["gate_passed"] is True
    assert result["papers_found"] == 2
    assert result["papers_processed"] == 3
    assert result["warnings_count"] == 1
