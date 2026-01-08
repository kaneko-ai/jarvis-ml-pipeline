"""Tests for V4.0 Integration Architecture.

Tests V4-A through V4-E modules.
"""

from jarvis_core.artifacts.adapters import (
    adapt_gap_analysis,
    adapt_to_artifact,
)
from jarvis_core.artifacts.schema import (
    ArtifactBase,
    EvidenceRef,
    Fact,
    Inference,
    create_artifact,
)
from jarvis_core.audit.report import generate_audit_report
from jarvis_core.bundle_v2 import BundleV2, create_bundle_v2
from jarvis_core.paper_vector import (
    ConceptVector,
    ImpactVector,
    MetadataVector,
    MethodVector,
    PaperVector,
    TemporalVector,
)
from jarvis_core.scoring.registry import (
    ScoreRegistry,
    get_score_info,
    normalize_score,
    validate_score_names,
)
from jarvis_core.truth_validation.claim_fact import (
    ClaimFactChecker,
    enforce_evidence_ref,
)
from jarvis_core.workflows.canonical import (
    run_literature_to_plan,
    run_plan_to_grant,
    run_plan_to_paper,
    run_plan_to_talk,
)
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
# if str(ROOT) not in sys.path:
#     sys.path.insert(0, str(ROOT))


def _create_test_vectors():
    return [
        PaperVector(
            paper_id="p1",
            source_locator="pdf:1.pdf",
            metadata=MetadataVector(year=2020),
            concept=ConceptVector(concepts={"CD73": 0.9}),
            method=MethodVector(methods={"Western blot": 0.8}),
            temporal=TemporalVector(novelty=0.6),
            impact=ImpactVector(future_potential=0.5),
        ),
        PaperVector(
            paper_id="p2",
            source_locator="pdf:2.pdf",
            metadata=MetadataVector(year=2022),
            concept=ConceptVector(concepts={"PD-1": 0.8}),
            method=MethodVector(methods={"scRNA-seq": 0.9}),
            temporal=TemporalVector(novelty=0.8),
            impact=ImpactVector(future_potential=0.7),
        ),
    ]

class TestArtifactSchema:
    """V4-A1 tests."""

    def test_fact_requires_evidence(self):
        with pytest.raises(ValueError):
            Fact(statement="Test", evidence_refs=[])

    def test_fact_with_evidence(self):
        ref = EvidenceRef(chunk_id="c1", source_locator="pdf:1")
        fact = Fact(statement="Test", evidence_refs=[ref])
        assert len(fact.evidence_refs) == 1

    def test_inference_marked_estimated(self):
        inf = Inference(statement="Test", method="heuristic")
        d = inf.to_dict()
        assert d["estimated"] is True

    def test_artifact_to_dict(self):
        artifact = ArtifactBase(kind="test")
        d = artifact.to_dict()
        assert d["kind"] == "test"

    def test_artifact_validation(self):
        artifact = ArtifactBase(kind="test", metrics={"bad": 2.0})
        issues = artifact.validate()
        assert len(issues) > 0

    def test_create_artifact_factory(self):
        artifact = create_artifact(
            kind="test",
            inferences=[{"statement": "Test", "method": "heuristic"}],
            source_module="test_module",
        )
        assert artifact.kind == "test"
        assert len(artifact.inferences) == 1

class TestAdapters:
    """V4-A2 tests."""

    def test_adapt_gap_analysis(self):
        result = {"concept": "CD73", "gap_score": 0.7, "reason": "High gap"}
        artifact = adapt_gap_analysis(result)
        assert artifact.kind == "gap_analysis"
        assert len(artifact.inferences) > 0

    def test_adapt_to_artifact_unknown(self):
        artifact = adapt_to_artifact("unknown_module", {"data": 1})
        assert artifact.kind == "unknown_module"

    def test_adapt_preserves_raw_data(self):
        result = {"score": 0.5}
        artifact = adapt_to_artifact("test", result)
        assert "result" in artifact.raw_data or "score" in artifact.raw_data

class TestScoreRegistry:
    """V4-A3 tests."""

    def test_normalize_score(self):
        score = normalize_score("roi_score", 0.5)
        assert 0 <= score <= 1

    def test_default_scores_registered(self):
        registry = ScoreRegistry()
        assert registry.is_registered("roi_score")
        assert registry.is_registered("gap_score")

    def test_validate_unregistered(self):
        issues = validate_score_names({"unknown_score": 0.5})
        assert "unknown_score" in issues

    def test_get_score_info(self):
        info = get_score_info("difficulty")
        assert info.direction == "lower_better"

class TestClaimFactChecker:
    """V4-B2 tests."""

    def test_alignment_with_evidence(self):
        ref = EvidenceRef(chunk_id="c1", source_locator="pdf:1", text_snippet="CD73 is important")
        fact = Fact(statement="CD73 plays a key role", evidence_refs=[ref])

        checker = ClaimFactChecker()
        result = checker.check_alignment("CD73 is important for immunity", [fact])
        assert result.status in ["aligned", "partial"]

    def test_misalignment(self):
        ref = EvidenceRef(chunk_id="c1", source_locator="pdf:1", text_snippet="PD-1 inhibition")
        fact = Fact(statement="PD-1 pathway", evidence_refs=[ref])

        checker = ClaimFactChecker()
        result = checker.check_alignment("CD73 regulation", [fact])
        assert result.status in ["misaligned", "partial"]

    def test_enforce_evidence_ref(self):
        level, stmt = enforce_evidence_ref("Test", has_evidence=True)
        assert level == "fact"

        level, stmt = enforce_evidence_ref("Test", has_evidence=False)
        assert level == "inference"
        assert "推定" in stmt

class TestAuditReport:
    """V4-D2 tests."""

    def test_generate_report(self):
        ref = EvidenceRef(chunk_id="c1", source_locator="pdf:1")
        artifact = ArtifactBase(
            kind="test",
            facts=[Fact(statement="Test", evidence_refs=[ref])],
            inferences=[Inference(statement="Inference", method="heuristic")],
        )
        report = generate_audit_report(artifact)
        assert report.fact_count == 1
        assert report.inference_count == 1

    def test_markdown_output(self):
        artifact = ArtifactBase(kind="test")
        report = generate_audit_report(artifact)
        md = report.to_markdown()
        assert "Audit Report" in md

class TestWorkflows:
    """V4-C1 tests."""

    def test_literature_to_plan(self):
        vectors = _create_test_vectors()
        artifact = run_literature_to_plan(vectors, ["CD73"])
        assert artifact.kind == "research_plan"

    def test_plan_to_grant(self):
        vectors = _create_test_vectors()
        plan = run_literature_to_plan(vectors, ["CD73"])
        artifact = run_plan_to_grant(plan, vectors, ["CD73", "immune"])
        assert artifact.kind == "grant_optimization"

    def test_plan_to_paper(self):
        vectors = _create_test_vectors()
        plan = run_literature_to_plan(vectors, ["CD73"])
        artifact = run_plan_to_paper(plan, vectors)
        assert artifact.kind == "paper_structure"

    def test_plan_to_talk(self):
        vectors = _create_test_vectors()
        plan = run_literature_to_plan(vectors, ["CD73"])
        artifact = run_plan_to_talk(plan, vectors, 15)
        assert artifact.kind == "presentation"

class TestBundleV2:
    """V4-D1 tests."""

    def test_create_bundle(self):
        artifact = ArtifactBase(kind="test")
        bundle = create_bundle_v2([artifact])
        assert len(bundle.artifacts) == 1

    def test_export_and_load(self):
        artifact = ArtifactBase(kind="test")
        bundle = create_bundle_v2([artifact])

        with tempfile.TemporaryDirectory() as tmpdir:
            bundle.export(tmpdir)

            # Check files exist
            assert (Path(tmpdir) / "bundle.json").exists()
            assert (Path(tmpdir) / "audit.md").exists()

            # Load back
            loaded = BundleV2.load(tmpdir)
            assert len(loaded.evidence_chunks) >= 0

    def test_add_evidence(self):
        bundle = BundleV2()
        bundle.add_evidence("chunk1", "Evidence text")
        assert "chunk1" in bundle.evidence_chunks
