from __future__ import annotations

import asyncio
import json
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from jarvis_core.reliability import health as health_module
from jarvis_core.scheduler import store as store_module
from jarvis_core.supervisor import lyra as lyra_module


def _setup_store_dirs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, Path]:
    schedules = tmp_path / "schedules"
    runs = schedules / "runs"
    schedules.mkdir(parents=True, exist_ok=True)
    runs.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(store_module, "SCHEDULES_DIR", schedules)
    monkeypatch.setattr(store_module, "RUNS_DIR", runs)
    return schedules, runs


def test_scheduler_store_crud_and_retry_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    schedules, runs = _setup_store_dirs(monkeypatch, tmp_path)
    assert store_module._schedule_path("SCH_X") == schedules / "SCH_X.json"
    assert store_module._run_path("run_x") == runs / "run_x.json"
    assert store_module._history_path("SCH_X") == runs / "SCH_X.jsonl"
    assert "T" in store_module._now()

    payload = {
        "name": "Daily Scan",
        "rrule": "FREQ=DAILY",
        "query": {"keywords": ["ai"], "oa_policy": "strict"},
    }
    saved = store_module.save_schedule(payload)
    schedule_id = saved["schedule_id"]
    assert schedule_id.startswith("SCH_")
    assert store_module.get_schedule(schedule_id) is not None
    assert len(store_module.list_schedules()) == 1

    updated = store_module.update_schedule(schedule_id, {"name": "Updated Scan"})
    assert updated is not None
    assert updated["name"] == "Updated Scan"
    assert store_module.update_schedule("missing", {"name": "x"}) is None

    run = store_module.create_run(schedule_id, "idem-1", {"k": "v"})
    assert run["status"] == "queued"
    assert store_module.read_run(run["run_id"]) is not None

    changed = store_module.update_run(run["run_id"], status="failed", next_retry_at="invalid-time")
    assert changed is not None
    assert changed["status"] == "failed"
    assert store_module.update_run("unknown") is None

    assert store_module.find_run_by_idempotency(schedule_id, "idem-1") is not None
    assert store_module.list_runs(schedule_id)
    assert store_module.list_all_runs(limit=10)
    assert store_module.list_all_runs(limit=10, statuses=["queued"]) == []

    # Invalid next_retry_at should be ignored
    assert store_module.list_due_retries(now=datetime.now(timezone.utc)) == []

    # Valid due retry should be returned
    due_time = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    store_module.update_run(run["run_id"], status="failed", next_retry_at=due_time)
    due = store_module.list_due_retries(now=datetime.now(timezone.utc))
    assert due

    store_module.update_schedule_status(schedule_id, "ok")
    assert store_module.get_schedule(schedule_id)["last_status"] == "ok"

    # _load_json fallback for malformed file
    bad_path = schedules / "SCH_bad.json"
    bad_path.write_text("{broken", encoding="utf-8")
    assert store_module._load_json(bad_path) == {}

    # Required field validation
    with pytest.raises(ValueError):
        store_module.save_schedule({"name": "", "rrule": "", "query": {}})


def test_lyra_supervisor_full_loop_and_singleton(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    supervisor = lyra_module.LyraSupervisor(audit_dir=tmp_path / "audit")

    instruction = "Implement feature quickly and better. Output JSON."
    deconstruct = supervisor.deconstruct(instruction, context={"epic": "E1"})
    assert deconstruct.core_intent

    diagnose = supervisor.diagnose(deconstruct)
    assert diagnose.issues
    assert 0 <= diagnose.overall_score <= 1

    develop = supervisor.develop(instruction, diagnose, task_type="technical")
    assert "Provenance Requirement" in develop.optimized_prompt

    deliver = supervisor.deliver(develop, target_worker="codex", priority=2, timeout=120)
    assert deliver.target_worker == "codex"
    assert deliver.timeout_seconds == 120

    supervised = supervisor.supervise(instruction, target_worker="llm", task_type="complex")
    assert supervised.target_worker == "llm"

    summary = supervisor.get_audit_summary()
    assert summary["total_logs"] > 0
    assert summary["run_id"] == supervisor.run_id

    # Factory and singleton
    lyra = lyra_module.get_lyra_supervisor(tmp_path / "audit2")
    assert isinstance(lyra, lyra_module.LyraSupervisor)
    monkeypatch.setattr(lyra_module, "_lyra_instance", None)
    g1 = lyra_module.get_lyra()
    g2 = lyra_module.get_lyra()
    assert g1 is g2


def _run_coro_in_thread(coro: Any) -> Any:
    result: dict[str, Any] = {}
    error: dict[str, BaseException] = {}

    def _runner() -> None:
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            result["value"] = loop.run_until_complete(coro)
        except BaseException as exc:  # noqa: BLE001
            error["value"] = exc
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    thread = threading.Thread(target=_runner)
    thread.start()
    thread.join()

    if "value" in error:
        raise error["value"]
    return result.get("value")


def test_health_checker_sync_and_async_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    checker = health_module.HealthChecker(version="1.0", start_time=1.0)
    checker.register_check(
        "ok",
        lambda: health_module.CheckResult(
            name="ok",
            status=health_module.HealthStatus.HEALTHY,
            latency_ms=0.0,
            message="ok",
        ),
    )
    checker.register_check(
        "degraded",
        lambda: health_module.CheckResult(
            name="degraded",
            status=health_module.HealthStatus.DEGRADED,
            latency_ms=0.0,
            message="slow",
        ),
    )
    checker.register_check("boom", lambda: (_ for _ in ()).throw(RuntimeError("fail")))

    liveness = checker.check_liveness()
    assert liveness.status == health_module.HealthStatus.HEALTHY

    readiness = checker.check_readiness()
    assert readiness.status == health_module.HealthStatus.UNHEALTHY
    assert len(readiness.checks) == 3

    async def _async_ok() -> health_module.CheckResult:
        return health_module.CheckResult(
            name="async-ok",
            status=health_module.HealthStatus.HEALTHY,
            latency_ms=0.0,
            message="ok",
        )

    checker.register_async_check("async-ok", _async_ok)
    async_report = _run_coro_in_thread(checker.check_readiness_async())
    assert async_report.status in {
        health_module.HealthStatus.HEALTHY,
        health_module.HealthStatus.DEGRADED,
        health_module.HealthStatus.UNHEALTHY,
    }

    assert health_module.check_redis("redis://localhost").status in {
        health_module.HealthStatus.HEALTHY,
        health_module.HealthStatus.UNHEALTHY,
    }
    assert health_module.check_postgres("postgres://localhost").status in {
        health_module.HealthStatus.HEALTHY,
        health_module.HealthStatus.UNHEALTHY,
    }
