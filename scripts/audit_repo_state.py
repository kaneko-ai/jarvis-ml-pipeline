#!/usr/bin/env python3
"""Repository state audit for ops_extract proof-driven checkpoints."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "audit_repo_state.md"


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _contains_all(text: str, needles: Iterable[str]) -> bool:
    return all(needle in text for needle in needles)


def run_audit() -> list[CheckResult]:
    schema_validate = _read(ROOT / "jarvis_core" / "ops_extract" / "schema_validate.py")
    orchestrator = _read(ROOT / "jarvis_core" / "ops_extract" / "orchestrator.py")
    drive_sync = _read(ROOT / "jarvis_core" / "ops_extract" / "drive_sync.py")
    doctor = _read(ROOT / "jarvis_core" / "ops_extract" / "doctor.py")
    preflight = _read(ROOT / "jarvis_core" / "ops_extract" / "preflight.py")

    results: list[CheckResult] = []
    results.append(
        CheckResult(
            name="validate_run_contracts_strict_exists",
            status=(
                "present" if "def validate_run_contracts_strict" in schema_validate else "missing"
            ),
            detail="schema_validate.py:def validate_run_contracts_strict",
        )
    )
    results.append(
        CheckResult(
            name="orchestrator_calls_strict_validator",
            status=(
                "present"
                if _contains_all(
                    orchestrator, ("validate_run_contracts_strict(", "write_contract_files")
                )
                else "missing"
            ),
            detail="orchestrator.py uses strict contract validation in write_contract_files stage",
        )
    )
    results.append(
        CheckResult(
            name="drive_sync_targets_manifest_outputs",
            status=(
                "present"
                if _contains_all(drive_sync, ("def _target_files_from_manifest", "outputs", "path"))
                else "missing"
            ),
            detail="drive_sync.py:_target_files_from_manifest references manifest outputs[].path",
        )
    )
    results.append(
        CheckResult(
            name="doctor_has_next_commands_section",
            status="present" if "## Next Commands" in doctor else "missing",
            detail='doctor.py writes "## Next Commands"',
        )
    )
    results.append(
        CheckResult(
            name="preflight_has_queue_backlog_hard_check",
            status=(
                "present"
                if _contains_all(preflight, ('"check_sync_queue_backlog"', "hard=True"))
                else "missing"
            ),
            detail="preflight.py executes check_sync_queue_backlog with hard=True",
        )
    )

    telemetry_files = [
        ROOT / "jarvis_core" / "ops_extract" / "telemetry" / "models.py",
        ROOT / "jarvis_core" / "ops_extract" / "telemetry" / "sampler.py",
        ROOT / "jarvis_core" / "ops_extract" / "telemetry" / "progress.py",
        ROOT / "jarvis_core" / "ops_extract" / "telemetry" / "eta.py",
    ]
    for path in telemetry_files:
        results.append(
            CheckResult(
                name=f"telemetry_file:{path.name}",
                status="present" if path.exists() else "missing",
                detail=str(path.relative_to(ROOT)),
            )
        )
    return results


def write_report(results: list[CheckResult]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# OpsExtract Repository Audit",
        "",
        "| Check | Status | Detail |",
        "|---|---|---|",
    ]
    for row in results:
        lines.append(f"| {row.name} | {row.status} | {row.detail} |")
    lines.append("")
    lines.append(
        f"Summary: present={sum(1 for r in results if r.status == 'present')} "
        f"missing={sum(1 for r in results if r.status == 'missing')}"
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    results = run_audit()
    write_report(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
