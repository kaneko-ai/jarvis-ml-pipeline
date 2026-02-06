from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from jarvis_core.contracts.types import Artifacts, Claim, EvidenceLink, Paper, Score, TaskContext
from jarvis_core.evaluation.evidence_validator import EvidenceValidator, validate_evidence_link
from jarvis_core.evidence.llm_classifier import LLMBasedClassifier, LLMConfig
from jarvis_core.evidence.schema import EvidenceLevel, PICOExtraction, StudyType
from jarvis_core.stages import output_quality as oq


def _make_artifacts() -> Artifacts:
    artifacts = Artifacts()
    artifacts.papers = [
        Paper(
            doc_id="doc-1",
            title="Paper",
            abstract="TNF alpha 20 reduction",
            sections={"methods": "Methods text"},
            chunks={"chunk-1": "TNF alpha 20 reduction in group A."},
        )
    ]
    artifacts.claims = [
        Claim(
            claim_id="claim-1",
            claim_text="TNF alpha 20 reduction",
            evidence=[
                EvidenceLink(
                    doc_id="doc-1",
                    section="abstract",
                    chunk_id="chunk-1",
                    start=0,
                    end=10,
                    confidence=0.9,
                    text="TNF alpha 20 reduction",
                )
            ],
            confidence=0.9,
        )
    ]
    artifacts.scores = {"quality": Score(name="quality", value=0.8, explanation="ok")}
    artifacts.summaries = {"summary": "short summary"}
    artifacts.metadata["comparison"] = {"baseline": 0.7, "current": 0.8}
    artifacts.metadata["experiment_proposals"] = [{"id": "exp-1"}]
    artifacts.metadata["protocols"] = [{"id": "proto-1"}]
    return artifacts


def test_llm_classifier_classify_and_parse_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    clf = LLMBasedClassifier(LLMConfig(model="test-model"))

    monkeypatch.setattr(clf, "_initialize", lambda: False)
    grade = clf.classify(title="t", abstract="a")
    assert grade.classifier_source == "llm_unavailable"

    monkeypatch.setattr(clf, "_initialize", lambda: True)
    empty = clf.classify()
    assert empty.level == EvidenceLevel.UNKNOWN

    class _FakeLLM:
        def generate(self, *_args: Any, **_kwargs: Any) -> str:
            return json.dumps(
                {
                    "study_type": "randomized trial",
                    "evidence_level": "1b",
                    "confidence": 88,
                    "reasoning": "well designed",
                }
            )

    clf._initialized = True
    clf._llm = _FakeLLM()
    ok = clf.classify(title="trial", abstract="randomized")
    assert ok.level == EvidenceLevel.LEVEL_1B
    assert ok.study_type == StudyType.RCT
    assert ok.confidence == 0.88

    broken = clf._parse_response("not-json")
    assert broken.level == EvidenceLevel.UNKNOWN
    assert clf._extract_json('```json {"a":1} ```') == '{"a":1}'
    assert clf._parse_evidence_level("2a") == EvidenceLevel.LEVEL_2A
    assert clf._parse_study_type("prospective cohort") == StudyType.COHORT_PROSPECTIVE
    assert clf._parse_study_type("guideline") == StudyType.GUIDELINE


def test_llm_classifier_extract_pico(monkeypatch: pytest.MonkeyPatch) -> None:
    clf = LLMBasedClassifier()
    monkeypatch.setattr(clf, "_initialize", lambda: False)
    assert clf.extract_pico("abstract") == PICOExtraction()

    class _FakeLLM:
        def generate(self, *_args: Any, **_kwargs: Any) -> str:
            return json.dumps(
                {
                    "population": "adults",
                    "intervention": "drug A",
                    "comparator": "placebo",
                    "outcome": "survival",
                }
            )

    monkeypatch.setattr(clf, "_initialize", lambda: True)
    clf._llm = _FakeLLM()
    pico = clf.extract_pico("abstract text")
    assert pico.population == "adults"
    assert pico.outcome == "survival"


def test_evidence_validator_single_and_batch_validation() -> None:
    paper = Paper(
        doc_id="doc-1",
        title="Paper",
        abstract="TNF alpha 20 reduction with treatment",
        sections={"results": "TNF alpha 20 reduction with treatment"},
        chunks={"chunk-a": "TNF alpha 20 reduction with treatment"},
    )
    validator = EvidenceValidator({"doc-1": paper})

    valid_claim = Claim(
        claim_id="c1",
        claim_text="TNF alpha 20 reduction",
        evidence=[
            EvidenceLink(
                doc_id="doc-1",
                section="results",
                chunk_id="chunk-a",
                start=0,
                end=12,
                confidence=0.9,
                text="TNF alpha 20 reduction",
            )
        ],
    )
    result = validator.validate_evidence_link(valid_claim)
    assert result.valid is True

    invalid_claim = Claim(
        claim_id="c2",
        claim_text="CD73 improves by 99",
        evidence=[
            EvidenceLink(
                doc_id="missing-doc",
                section="",
                chunk_id="",
                start=10,
                end=5,
                confidence=0.5,
                text="unrelated 11",
            )
        ],
    )
    invalid = validator.validate_evidence_link(invalid_claim)
    assert invalid.valid is False
    assert invalid.reasons
    assert invalid.warnings

    summary = validator.validate_all_claims([valid_claim, invalid_claim])
    assert summary["total"] == 2
    assert summary["invalid"] >= 1

    wrapped = validate_evidence_link(valid_claim, {"doc-1": paper})
    assert wrapped.valid is True


def test_output_stage_functions_render_and_quality(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    context = TaskContext(goal="test-goal", domain="bio", run_id="run-123")
    artifacts = _make_artifacts()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(oq, "log_audit", lambda *_args, **_kwargs: None)

    class _DummyReport:
        def to_dict(self) -> dict[str, Any]:
            return {"passed": True}

    class _DummyGates:
        def run_all(self, **_kwargs: Any) -> _DummyReport:
            return _DummyReport()

        def check_provenance(self, _claims: list[Claim]) -> Any:
            return SimpleNamespace(passed=True, threshold=0.95, actual=1.0, message="ok")

    monkeypatch.setattr("jarvis_core.evaluation.get_quality_gates", lambda *_a, **_k: _DummyGates())
    monkeypatch.setattr(
        "jarvis_core.ops.get_audit_logger",
        lambda: SimpleNamespace(
            get_summary=lambda: {
                "run_id": "run-123",
                "entries": 3,
                "errors": 0,
                "avg_provenance_rate": 1.0,
            }
        ),
    )

    for fn in [
        oq.stage_output_render_dashboard,
        oq.stage_output_evidence_highlight,
        oq.stage_output_score_bar,
        oq.stage_output_comparison_view,
        oq.stage_output_design_view,
        oq.stage_output_export_bundle,
        oq.stage_quality_gate_provenance_check,
        oq.stage_quality_gate_final_audit,
    ]:
        artifacts = fn(context, artifacts)

    assert "dashboard" in artifacts.metadata
    assert "evidence_highlights" in artifacts.metadata
    assert "score_bars" in artifacts.metadata
    assert "comparison_view" in artifacts.metadata
    assert "design_view" in artifacts.metadata
    assert "export_bundle" in artifacts.metadata
    assert "provenance_check" in artifacts.metadata
    assert "final_audit" in artifacts.metadata

    bundle_file = tmp_path / "artifacts" / "run-123" / "export_bundle.json"
    docs_file = tmp_path / "artifacts" / "run-123" / "docs_store.json"
    assert bundle_file.exists()
    assert docs_file.exists()
