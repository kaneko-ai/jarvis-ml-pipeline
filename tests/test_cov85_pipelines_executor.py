from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from jarvis_core.contracts.types import Artifacts, Claim, EvidenceLink, TaskContext
from jarvis_core.pipelines.executor import (
    PipelineConfig,
    PipelineExecutor,
    StageResult,
    _parse_stages,
)


class _FakeObsLogger:
    def __init__(self) -> None:
        self.events = []

    def step_start(
        self, step: str, message: str = "stage start", data=None
    ) -> None:  # noqa: ANN001
        self.events.append(("step_start", step, message, data))

    def step_end(self, step: str, message: str = "step end", data=None) -> None:  # noqa: ANN001
        self.events.append(("step_end", step, message, data))

    def error(self, message: str, step: str | None = None, exc: Exception | None = None) -> None:
        self.events.append(("error", step, message, type(exc).__name__ if exc else None))


class _FakeRegistry:
    def __init__(self, handlers: dict[str, object]) -> None:
        self.handlers = handlers
        self.validated: list[str] = []

    def validate_pipeline(self, stages: list[str]) -> None:
        self.validated = list(stages)

    def get(self, name: str):
        return self.handlers[name]


def _claim_with_evidence() -> Claim:
    return Claim(
        claim_id="c1",
        claim_text="text",
        evidence=[
            EvidenceLink(
                doc_id="d1",
                section="Abstract",
                chunk_id="x",
                start=0,
                end=4,
                confidence=0.9,
                text="text",
            )
        ],
    )


def test_parse_stages_and_pipeline_config_from_dict() -> None:
    assert _parse_stages(["a", {"id": "b"}]) == ["a", "b"]

    cfg = PipelineConfig.from_dict(
        {
            "pipeline": "demo",
            "stages": [{"id": "s1"}, "s2"],
            "policies": {"cache": "none"},
            "version": 2,
        }
    )
    assert cfg.name == "demo"
    assert cfg.stages == ["s1", "s2"]
    assert cfg.policies["cache"] == "none"
    assert cfg.version == 2


def test_pipeline_config_from_yaml_success_and_importerror(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    yaml_path = tmp_path / "pipeline.yaml"
    yaml_path.write_text("pipeline: x\n", encoding="utf-8")

    monkeypatch.setattr("jarvis_core.pipelines.executor.HAS_YAML", True)
    monkeypatch.setattr(
        "jarvis_core.pipelines.executor.yaml.safe_load",
        lambda fp: {
            "name": "yaml-demo",
            "stages": [{"id": "a"}],
            "version": 3,
            "policies": {"p": 1},
        },
    )
    cfg = PipelineConfig.from_yaml(yaml_path)
    assert cfg.name == "yaml-demo"
    assert cfg.stages == ["a"]
    assert cfg.version == 3

    monkeypatch.setattr("jarvis_core.pipelines.executor.HAS_YAML", False)
    with pytest.raises(ImportError):
        PipelineConfig.from_yaml(yaml_path)


def test_pipeline_run_success_and_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = PipelineConfig.from_dict(
        {
            "pipeline": "ok-flow",
            "stages": ["s1", "s2"],
            "policies": {"provenance_required": True, "refuse_if_no_evidence": True},
        }
    )
    artifacts = Artifacts(claims=[_claim_with_evidence()], papers=[SimpleNamespace()])
    ctx = TaskContext(goal="test", run_id="run-ok")

    registry = _FakeRegistry(
        {
            "s1": lambda context, a: {"k1": "v1"},
            "s2": lambda context, a: Artifacts(),
        }
    )
    obs_logger = _FakeObsLogger()
    lyra = SimpleNamespace(supervise=lambda *args, **kwargs: SimpleNamespace(task_id="lyra-1"))

    monkeypatch.setattr("jarvis_core.pipelines.executor.get_stage_registry", lambda: registry)
    monkeypatch.setattr("jarvis_core.pipelines.executor.get_logger", lambda **kwargs: obs_logger)
    monkeypatch.setattr(
        "jarvis_core.pipelines.executor.metrics.record_run_start", lambda **kwargs: None
    )
    monkeypatch.setattr(
        "jarvis_core.pipelines.executor.metrics.record_run_end", lambda **kwargs: None
    )
    monkeypatch.setattr(
        "jarvis_core.pipelines.executor.metrics.record_step_duration", lambda *args, **kwargs: None
    )

    exe = PipelineExecutor(config=cfg, lyra=lyra)
    result = exe.run(ctx, artifacts)

    assert result.success is True
    assert result.outputs["k1"] == "v1"
    assert any("started" in log for log in result.logs)
    assert any("completed" in log for log in result.logs)
    assert registry.validated == ["s1", "s2"]

    summary = exe.get_summary()
    assert summary["pipeline"] == "ok-flow"
    assert summary["stages_success"] == 2
    assert summary["stages_executed"] == 2


def test_pipeline_run_stage_failure_and_provenance_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = PipelineConfig.from_dict(
        {
            "pipeline": "fail-flow",
            "stages": ["s1", "s2"],
            "policies": {"provenance_required": True, "refuse_if_no_evidence": True},
        }
    )
    ctx = TaskContext(goal="test", run_id="run-fail")

    # Stage failure should break when refuse_if_no_evidence is enabled.
    calls = {"s2": 0}

    def _raise(context, artifacts):  # noqa: ANN001
        raise RuntimeError("boom")

    def _s2(context, artifacts):  # noqa: ANN001
        calls["s2"] += 1
        return {"k2": "v2"}

    registry = _FakeRegistry({"s1": _raise, "s2": _s2})
    obs_logger = _FakeObsLogger()
    lyra = SimpleNamespace(supervise=lambda *args, **kwargs: SimpleNamespace(task_id="lyra-2"))

    monkeypatch.setattr("jarvis_core.pipelines.executor.get_stage_registry", lambda: registry)
    monkeypatch.setattr("jarvis_core.pipelines.executor.get_logger", lambda **kwargs: obs_logger)
    monkeypatch.setattr(
        "jarvis_core.pipelines.executor.metrics.record_run_start", lambda **kwargs: None
    )
    monkeypatch.setattr(
        "jarvis_core.pipelines.executor.metrics.record_run_end", lambda **kwargs: None
    )
    monkeypatch.setattr(
        "jarvis_core.pipelines.executor.metrics.record_step_duration", lambda *args, **kwargs: None
    )

    exe = PipelineExecutor(config=cfg, lyra=lyra)
    failed = exe.run(ctx, Artifacts(claims=[_claim_with_evidence()]))
    assert failed.success is False
    assert "Stage s1 failed" in (failed.error or "")
    assert calls["s2"] == 0

    # Provenance failure path (all claims without evidence).
    cfg2 = PipelineConfig.from_dict(
        {
            "pipeline": "prov-flow",
            "stages": ["s1"],
            "policies": {"provenance_required": True, "refuse_if_no_evidence": True},
        }
    )
    registry2 = _FakeRegistry({"s1": lambda context, a: {"ok": True}})
    monkeypatch.setattr("jarvis_core.pipelines.executor.get_stage_registry", lambda: registry2)
    exe2 = PipelineExecutor(config=cfg2, lyra=lyra)
    no_evidence = exe2.run(ctx, Artifacts(claims=[Claim(claim_id="x", claim_text="y")]))
    assert no_evidence.success is False
    assert "Provenance rate" in (no_evidence.error or "")


def test_execute_stage_outputs_for_dict_and_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = PipelineConfig.from_dict({"pipeline": "exec", "stages": ["s1"]})
    lyra = SimpleNamespace(supervise=lambda *args, **kwargs: SimpleNamespace(task_id="lyra-3"))
    registry = _FakeRegistry({"s1": lambda context, artifacts: {"a": 1}})

    monkeypatch.setattr("jarvis_core.pipelines.executor.get_stage_registry", lambda: registry)
    monkeypatch.setattr(
        "jarvis_core.pipelines.executor.metrics.record_step_duration", lambda *args, **kwargs: None
    )
    exe = PipelineExecutor(config=cfg, lyra=lyra)
    obs = _FakeObsLogger()

    ok = exe._execute_stage("s1", TaskContext(goal="g", run_id="run-exec"), Artifacts(), obs)
    assert isinstance(ok, StageResult)
    assert ok.success is True
    assert ok.outputs["a"] == 1
    assert any(e[0] == "step_end" for e in obs.events)

    registry.handlers["s1"] = lambda context, artifacts: (_ for _ in ()).throw(ValueError("bad"))
    ng = exe._execute_stage("s1", TaskContext(goal="g", run_id="run-exec"), Artifacts(), obs)
    assert ng.success is False
    assert "bad" in (ng.error or "")
