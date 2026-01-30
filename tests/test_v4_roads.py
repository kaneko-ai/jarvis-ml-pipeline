"""Tests for V4.0 道1-5 modules."""

from jarvis_core.paper_vector import (
    BiologicalAxisVector,
    ConceptVector,
    ImpactVector,
    MetadataVector,
    MethodVector,
    PaperVector,
    TemporalVector,
)
import tempfile
from pathlib import Path
import pytest


# PR-59: Mark all tests in this file as core
pytestmark = pytest.mark.core

ROOT = Path(__file__).resolve().parents[1]
# if str(ROOT) not in sys.path:
#     sys.path.insert(0, str(ROOT))


def _create_test_vectors():
    return [
        PaperVector(
            paper_id="p1",
            source_locator="pdf:1",
            metadata=MetadataVector(year=2020),
            concept=ConceptVector(concepts={"CD73": 0.9, "PD-1": 0.3}),
            method=MethodVector(methods={"Western blot": 0.8}),
            temporal=TemporalVector(novelty=0.6),
            impact=ImpactVector(future_potential=0.5),
            biological_axis=BiologicalAxisVector(immune_activation=0.7),
        ),
        PaperVector(
            paper_id="p2",
            source_locator="pdf:2",
            metadata=MetadataVector(year=2022),
            concept=ConceptVector(concepts={"PD-1": 0.8, "CTLA-4": 0.5}),
            method=MethodVector(methods={"scRNA-seq": 0.9}),
            temporal=TemporalVector(novelty=0.8),
            impact=ImpactVector(future_potential=0.7),
            biological_axis=BiologicalAxisVector(immune_activation=0.8),
        ),
        PaperVector(
            paper_id="p3",
            source_locator="pdf:3",
            metadata=MetadataVector(year=2021),
            concept=ConceptVector(concepts={"CD73": 0.7, "CTLA-4": 0.4}),
            method=MethodVector(methods={"Western blot": 0.5}),
            temporal=TemporalVector(novelty=0.5),
            impact=ImpactVector(future_potential=0.4),
            biological_axis=BiologicalAxisVector(immune_activation=0.6),
        ),
    ]


class TestCLI:
    """V4-P01 tests."""

    def test_run_workflow(self):
        from jarvis_core.cli_v4.main import run_workflow

        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_workflow("literature_to_plan", [], "test", ["CD73"], tmpdir)
            assert result["status"] == "success"

    def test_list_resources(self):
        from jarvis_core.cli_v4.main import list_resources

        list_resources("workflows")  # Should not raise


class TestConfig:
    """V4-P02 tests."""

    def test_load_default(self):
        from jarvis_core.config_utils import get_default_config

        config = get_default_config()
        assert config.output_dir == "output"

    def test_load_config(self):
        from jarvis_core.config_utils import load_config

        config = load_config()
        assert config is not None


class TestErrors:
    """V4-P06 tests."""

    def test_validation_error(self):
        from jarvis_core.errors import ValidationError

        err = ValidationError("test")
        assert err.exit_code == 10

    def test_evidence_error(self):
        from jarvis_core.errors import EvidenceError

        err = EvidenceError("test")
        assert err.exit_code == 20


class TestTrace:
    """V4-P05 tests."""

    def test_run_trace(self):
        from jarvis_core.trace import RunTrace

        trace = RunTrace("test_workflow")
        step_id = trace.start_step("step1")
        trace.end_step(step_id, "success")
        trace.finish()
        assert trace.status == "success"
        assert len(trace.steps) == 1


class TestRegistry:
    """V4-P13 tests."""

    def test_list_modules(self):
        from jarvis_core.module_registry import list_modules

        modules = list_modules()
        assert len(modules) > 0

    def test_get_module(self):
        from jarvis_core.module_registry import get_module

        mod = get_module("gap_analysis")
        assert mod is not None


class TestTruthEnforce:
    """V4-T01 tests."""

    def test_enforce_fact_evidence(self):
        from jarvis_core.artifacts.schema import EvidenceRef, Fact
        from jarvis_core.truth.enforce import enforce_fact_evidence

        ref = EvidenceRef(chunk_id="c1", source_locator="pdf:1")
        facts = [
            Fact(statement="With evidence", evidence_refs=[ref]),
        ]
        valid, downgraded, flags = enforce_fact_evidence(facts)
        assert len(valid) == 1
        assert len(downgraded) == 0


class TestTruthAlignment:
    """V4-T02 tests."""

    def test_alignment_check(self):
        from jarvis_core.artifacts.schema import EvidenceRef, Fact
        from jarvis_core.truth.alignment import check_alignment_v2

        ref = EvidenceRef(
            chunk_id="c1", source_locator="pdf:1", text_snippet="CD73 is expressed in tumors"
        )
        facts = [Fact(statement="CD73 expression in cancer", evidence_refs=[ref])]
        result = check_alignment_v2("CD73 expressed in tumor cells", facts)
        assert result.status in ["aligned", "partial"]


class TestTruthRelevance:
    """V4-T03 tests."""

    def test_score_relevance(self):
        from jarvis_core.truth.relevance import score_relevance

        result = score_relevance("CD73 function", "CD73 plays a role in immune regulation")
        assert result["score"] >= 0


class TestTruthContradiction:
    """V4-T04 tests."""

    def test_detect_contradictions(self):
        from jarvis_core.artifacts.schema import EvidenceRef, Fact
        from jarvis_core.truth.contradiction import detect_contradictions

        ref = EvidenceRef(chunk_id="c1", source_locator="pdf:1")
        facts = [
            Fact(statement="CD73 increases tumor growth", evidence_refs=[ref]),
            Fact(statement="CD73 decreases tumor invasion", evidence_refs=[ref]),
        ]
        results = detect_contradictions(facts)
        assert len(results) >= 1


class TestTruthConfidence:
    """V4-T05 tests."""

    def test_calibrate_confidence(self):
        from jarvis_core.truth.confidence import calibrate_confidence

        result = calibrate_confidence(0.8, "test", evidence_count=3)
        assert 0 <= result["value"] <= 1


class TestMapSimilarity:
    """V4-M01 tests."""

    def test_explain_similarity(self):
        from jarvis_core.map.similarity_explain import explain_similarity

        vectors = _create_test_vectors()
        result = explain_similarity(vectors[0], vectors[1])
        assert "similarity_score" in result


class TestMapBridges:
    """V4-M02 tests."""

    def test_find_bridges(self):
        from jarvis_core.map.bridges import find_bridge_papers

        vectors = _create_test_vectors()
        bridges = find_bridge_papers([vectors[0]], [vectors[1]], vectors)
        assert isinstance(bridges, list)


class TestMapClusters:
    """V4-M03 tests."""

    def test_build_clusters(self):
        from jarvis_core.map.clusters import build_cluster_map

        vectors = _create_test_vectors()
        result = build_cluster_map(vectors)
        assert "clusters" in result


class TestMapNeighborhood:
    """V4-M04 tests."""

    def test_query_neighborhood(self):
        from jarvis_core.map.neighborhood import query_neighborhood

        vectors = _create_test_vectors()
        neighbors = query_neighborhood(vectors[0], vectors)
        assert isinstance(neighbors, list)


class TestMapPathFinder:
    """V4-M05 tests."""

    def test_find_path(self):
        from jarvis_core.map.path_finder import find_concept_path

        vectors = _create_test_vectors()
        path = find_concept_path(vectors[0], vectors[1], vectors)
        assert path is None or "path" in path


class TestMapTimeline:
    """V4-M06 tests."""

    def test_build_timeline(self):
        from jarvis_core.map.timeline_map import build_timeline_map

        vectors = _create_test_vectors()
        result = build_timeline_map(vectors)
        assert "years" in result


class TestObsidianSync:
    """V4-I01 tests."""

    def test_sync_note(self):
        from jarvis_core.integrations.obsidian_sync import ObsidianSync

        with tempfile.TemporaryDirectory() as tmpdir:
            syncer = ObsidianSync(tmpdir)
            status = syncer.sync_note("test", "# Test\nContent")
            assert status == "created"
            status2 = syncer.sync_note("test", "# Test\nContent")
            assert status2 == "unchanged"


class TestManifestWatch:
    """V4-I02 tests."""

    def test_manifest_add(self):
        from jarvis_core.integrations.watch import ManifestWatcher

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            watcher = ManifestWatcher(str(manifest_path))
            watcher.add_entry("test.pdf", "pdf")
            assert len(watcher.entries) == 1