"""Tests for V4.1 Sprint 1 modules."""
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# PR-59: Mark all tests in this file as core
pytestmark = pytest.mark.core

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestGoldsetSchema:
    """V4-A01 tests."""

    def test_create_entry(self):
        from jarvis_core.eval.goldset_schema import GoldsetEntry, GoldsetLabel
        entry = GoldsetEntry(
            claim_id="test1",
            claim_text="Test claim",
            expected_label=GoldsetLabel.FACT,
            evidence_text="Test evidence",
        )
        assert entry.claim_id == "test1"

    def test_validate_goldset(self):
        from jarvis_core.eval.goldset_schema import create_sample_goldset, validate_goldset
        sample = create_sample_goldset()
        is_valid, issues = validate_goldset(sample)
        assert is_valid

    def test_save_load_goldset(self):
        from jarvis_core.eval.goldset_schema import (
            create_sample_goldset,
            load_goldset,
            save_goldset,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "goldset.jsonl"
            sample = create_sample_goldset()
            save_goldset(sample, str(path))
            loaded = load_goldset(str(path))
            assert len(loaded) == len(sample)


class TestTruthMetrics:
    """V4-A03 tests."""

    def test_calculate_metrics(self):
        from jarvis_core.eval.metrics_truth import calculate_truth_metrics
        predictions = [
            {"claim": "Claim 1", "label": "fact", "has_evidence": True},
            {"claim": "Claim 2", "label": "fact", "has_evidence": False},
            {"claim": "Claim 3", "label": "inference", "has_evidence": False},
        ]
        metrics = calculate_truth_metrics(predictions)
        assert metrics.total_claims == 3
        assert metrics.facts_with_evidence == 1
        assert metrics.unsupported_fact_rate > 0

    def test_is_passing(self):
        from jarvis_core.eval.metrics_truth import TruthMetrics
        metrics = TruthMetrics(
            unsupported_fact_rate=0.05,
            downgrade_rate=0.1,
            fact_precision=0.9,
            fact_recall=0.9,
            total_claims=10,
            facts_with_evidence=8,
            facts_without_evidence=1,
            inferences=1,
            unsupported=0,
            flags=[],
        )
        assert metrics.is_passing(max_unsupported_rate=0.1)


class TestRegressionRunner:
    """V4-A05 tests."""

    def test_run_regression(self):
        from jarvis_core.eval.regression_runner import run_regression
        predictions = [
            {"claim": "Claim 1", "label": "fact", "has_evidence": True},
        ]
        result = run_regression(predictions)
        assert result.run_id is not None
        assert not result.is_regression


class TestContentAddressedStore:
    """V4-B01 tests."""

    def test_compute_hash(self):
        from jarvis_core.store.content_addressed import compute_hash
        h1 = compute_hash("test content")
        h2 = compute_hash("test content")
        assert h1 == h2

    def test_store_retrieve(self):
        from jarvis_core.store.content_addressed import ContentAddressedStore
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ContentAddressedStore(tmpdir)
            h = store.store("test content", "text")
            content = store.retrieve(h)
            assert content == "test content"


class TestProvenanceGraph:
    """V4-B02 tests."""

    def test_add_nodes_edges(self):
        from jarvis_core.provenance.graph import NodeType, ProvenanceGraph
        graph = ProvenanceGraph()
        graph.add_node("source1", NodeType.SOURCE)
        graph.add_node("chunk1", NodeType.CHUNK)
        graph.add_edge("source1", "chunk1")
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1

    def test_get_ancestors(self):
        from jarvis_core.provenance.graph import NodeType, ProvenanceGraph
        graph = ProvenanceGraph()
        graph.add_node("source1", NodeType.SOURCE)
        graph.add_node("chunk1", NodeType.CHUNK)
        graph.add_node("fact1", NodeType.FACT)
        graph.add_edge("source1", "chunk1")
        graph.add_edge("chunk1", "fact1")
        ancestors = graph.get_ancestors("fact1")
        assert "chunk1" in ancestors


class TestManifestV2:
    """V4-B03 tests."""

    def test_create_manifest(self):
        from jarvis_core.provenance.manifest_v2 import create_manifest
        manifest = create_manifest(query="test", concepts=["CD73"])
        assert manifest.query == "test"
        assert "CD73" in manifest.concepts

    def test_save_load(self):
        from jarvis_core.provenance.manifest_v2 import ManifestV2
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "manifest.json"
            m = ManifestV2(run_id="test", created_at=datetime.now())
            m.save(str(path))
            loaded = ManifestV2.load(str(path))
            assert loaded.run_id == "test"


class TestReplay:
    """V4-B04 tests."""

    def test_replay_result(self):
        from jarvis_core.replay.reproduce import ReplayResult
        result = ReplayResult(
            original_run_id="orig1",
            replay_run_id="replay1",
            is_identical=True,
            diff_reasons=[],
            output_diff={},
        )
        assert result.is_identical


class TestTraceSpans:
    """V4-C01 tests."""

    def test_span_tracking(self):
        from jarvis_core.perf.trace_spans import SpanTracker
        tracker = SpanTracker()
        span_id = tracker.start_span("test_span")
        tracker.end_span(span_id, item_count=10)
        assert len(tracker.spans) == 1
        assert tracker.spans[0].item_count == 10


class TestSLOPolicy:
    """V4-C02 tests."""

    def test_check_slo(self):
        from jarvis_core.perf.slo_policy import SLOStatus, check_slo
        status = SLOStatus(elapsed_seconds=30, tokens_used=10000)
        is_passing, violations = check_slo(status, mode="quick")
        assert is_passing


class TestBudgetManager:
    """V4-C10 tests."""

    def test_budget_tracking(self):
        from jarvis_core.runtime.budget import BudgetLimits, BudgetManager
        limits = BudgetLimits(max_tokens=1000)
        manager = BudgetManager(limits)
        manager.add_tokens(500)
        assert manager.usage.tokens_used == 500

    def test_budget_exceeded(self):
        from jarvis_core.runtime.budget import BudgetLimits, BudgetManager, BudgetType
        limits = BudgetLimits(max_tokens=100)
        manager = BudgetManager(limits)
        manager.add_tokens(200)
        ok, exceeded = manager.check_all()
        assert not ok
        assert exceeded == BudgetType.TOKENS


class TestTriage:
    """V4-D01 tests."""

    def test_triage_by_risk(self):
        from jarvis_core.review.triage import calculate_risk_score

        # Test risk calculation directly
        item_with_evidence = {"content": "test", "has_evidence": True, "confidence": 0.9}
        score1, reasons1 = calculate_risk_score(item_with_evidence, "fact")
        assert score1 == 0.0

        item_without_evidence = {"content": "test", "has_evidence": False, "confidence": 0.9}
        score2, reasons2 = calculate_risk_score(item_without_evidence, "fact")
        assert score2 > 0

    def test_triage_inference(self):
        from jarvis_core.review.triage import calculate_risk_score

        item = {"content": "降格 test"}
        score, reasons = calculate_risk_score(item, "inference")
        assert score > 0
        assert "Downgraded from FACT" in reasons

