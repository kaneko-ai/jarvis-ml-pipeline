"""Preflight checks for ops_extract mode."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from jarvis_core.ingestion.yomitoku_cli import check_yomitoku_available

from .contracts import OpsExtractConfig
from .learning import load_block_rules


@dataclass
class PreflightReport:
    passed: bool
    errors: list[str]
    warnings: list[str]
    checks: list[dict[str, Any]]


def _check_disk_free(min_gb: float) -> tuple[bool, str]:
    usage = shutil.disk_usage(Path.cwd())
    free_gb = usage.free / (1024**3)
    ok = free_gb >= min_gb
    msg = f"disk_free_gb={free_gb:.2f}, required={min_gb:.2f}"
    return ok, msg


def _check_input_exists(paths: list[Path]) -> tuple[bool, str]:
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        return False, f"missing_inputs={missing}"
    return True, f"inputs={len(paths)}"


def _check_drive_auth(config: OpsExtractConfig) -> tuple[bool, str]:
    if not config.sync_enabled or config.sync_dry_run:
        return True, "sync_disabled_or_dry_run"
    if config.drive_access_token:
        return True, "drive_access_token_present"
    env_token = os.getenv("GOOGLE_DRIVE_ACCESS_TOKEN")
    if env_token:
        return True, "drive_access_token_from_env"
    return False, "drive_access_token_missing"


def _check_yomitoku_available() -> tuple[bool, str]:
    ok = check_yomitoku_available()
    return ok, "yomitoku_available" if ok else "yomitoku_missing"


def _check_storage_writable() -> tuple[bool, str]:
    writable = os.access(Path.cwd(), os.W_OK)
    return writable, "cwd_writable" if writable else "cwd_not_writable"


def _parse_rule_with_severity(raw_rule: str) -> tuple[str, bool]:
    rule = str(raw_rule).strip()
    if rule.startswith("hard:"):
        return rule.split(":", 1)[1].strip(), True
    if rule.startswith("warn:"):
        return rule.split(":", 1)[1].strip(), False
    return rule, True


def run_preflight_checks(
    *,
    input_paths: list[Path],
    config: OpsExtractConfig,
    lessons_path: Path | None = None,
) -> PreflightReport:
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[dict[str, Any]] = []
    force_warn = str(config.preflight_rule_mode).lower() == "warn"

    def execute(name: str, fn: Callable[[], tuple[bool, str]], *, hard: bool) -> None:
        effective_hard = hard and not force_warn
        ok, detail = fn()
        checks.append(
            {
                "name": name,
                "ok": ok,
                "detail": detail,
                "hard": effective_hard,
                "configured_hard": hard,
            }
        )
        if not ok and effective_hard:
            errors.append(f"{name}:{detail}")
        elif not ok:
            warnings.append(f"{name}:{detail}")

    execute(
        "check_input_exists",
        lambda: _check_input_exists(input_paths),
        hard=True,
    )
    execute(
        "check_disk_free",
        lambda: _check_disk_free(config.min_disk_free_gb),
        hard=True,
    )
    execute(
        "check_drive_auth",
        lambda: _check_drive_auth(config),
        hard=True,
    )

    block_rules = load_block_rules(lessons_path)
    for raw_rule in block_rules:
        rule, hard = _parse_rule_with_severity(raw_rule)
        if rule == "check_yomitoku_available":
            execute(rule, _check_yomitoku_available, hard=hard)
        elif rule == "check_storage_writable":
            execute(rule, _check_storage_writable, hard=hard)
        elif rule in {"check_network_state", "check_last_run_logs", "check_quota_limit"}:
            execute(rule, lambda: (True, "not_applicable"), hard=hard)
        else:
            warnings.append(f"unknown_preflight_rule:{rule}")

    passed = len(errors) == 0
    return PreflightReport(passed=passed, errors=errors, warnings=warnings, checks=checks)
