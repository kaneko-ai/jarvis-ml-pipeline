"""Tests for V4.2 Sprint 2-3 modules."""

import sys
import tempfile
from pathlib import Path

import pytest

# PR-59: Mark all tests in this file as core
pytestmark = pytest.mark.core

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Sprint 2 Tests


class TestTaskGraph:
    """道G tests."""

    def test_task_execution(self):
        from jarvis_core.runtime.task_graph import TaskGraph

        graph = TaskGraph(max_workers=1)
        graph.add_task("t1", "task1", lambda: "result1")
        graph.add_task("t2", "task2", lambda: "result2", dependencies=["t1"])

        results = graph.execute(parallel=False)
        assert results["t1"] == "result1"
        assert results["t2"] == "result2"

    def test_parallel_same_result(self):
        from jarvis_core.runtime.task_graph import TaskGraph

        def make_graph():
            g = TaskGraph(max_workers=2)
            g.add_task("a", "task_a", lambda: 1)
            g.add_task("b", "task_b", lambda: 2, dependencies=["a"])
            return g

        # Sequential
        g1 = make_graph()
        r1 = g1.execute(parallel=False)

        # Parallel
        g2 = make_graph()
        r2 = g2.execute(parallel=True)

        assert r1 == r2


class TestStreamingBundle:
    """道F tests."""

    def test_checkpoint_resume(self):
        from jarvis_core.runtime.streaming_bundle import StreamingBundle

        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = StreamingBundle(tmpdir)

            # Save checkpoint
            cp = bundle.save_checkpoint(
                completed_tasks=["t1", "t2"],
                pending_tasks=["t3"],
                task_results={"t1": "r1"},
                manifest_hash="abc123",
            )
            assert cp.checkpoint_id is not None

            # Load checkpoint
            loaded = bundle.load_checkpoint()
            assert loaded.completed_tasks == ["t1", "t2"]
            assert bundle.can_resume("abc123")
            assert not bundle.can_resume("different")


class TestIncrementalIndex:
    """道E tests."""

    def test_skip_processed(self):
        from jarvis_core.index.incremental_state import IncrementalState
        from jarvis_core.index.pipeline import IndexPipeline, PipelineStage

        pipeline = IndexPipeline()
        pipeline.register_stage(PipelineStage.INGEST, lambda x: x)

        state = IncrementalState()
        inputs = ["doc1", "doc2", "doc3"]

        # First run
        r1 = pipeline.run_stage(PipelineStage.INGEST, inputs, state)
        assert r1.skipped_count == 0

        # Second run - should skip all
        r2 = pipeline.run_stage(PipelineStage.INGEST, inputs, state)
        assert r2.skipped_count == 3

    def test_dedup(self):
        from jarvis_core.index.dedup import dedupe_chunks

        chunks = ["hello world", "hello world", "different text"]
        unique = dedupe_chunks(chunks)
        assert len(unique) == 2


class TestMultiLevelCache:
    """道H tests."""

    def test_l1_cache(self):
        from jarvis_core.cache.multi_level import CacheLevel, MultiLevelCache

        cache = MultiLevelCache()
        cache.put("key1", "value1", write_l2=False)

        val, level = cache.get("key1")
        assert val == "value1"
        assert level == CacheLevel.L1_MEMORY

    def test_cache_key_determinism(self):
        from jarvis_core.cache.key_contract import compute_cache_key

        k1 = compute_cache_key("hash1", "stage1", "1.0", "gpt-4")
        k2 = compute_cache_key("hash1", "stage1", "1.0", "gpt-4")
        k3 = compute_cache_key("hash1", "stage1", "1.0", "gpt-3.5")

        assert k1 == k2  # Same inputs -> same key
        assert k1 != k3  # Different model -> different key


class TestCircuitBreaker:
    """道K tests."""

    def test_circuit_states(self):
        from jarvis_core.runtime.circuit_breaker import CircuitBreaker, FailureReason

        breaker = CircuitBreaker(failure_threshold=3)
        assert breaker.can_execute()

        # Record failures
        for _ in range(3):
            breaker.record_failure(FailureReason.NETWORK)

        # Should be open now
        assert not breaker.can_execute()

    def test_classify_failure(self):
        from jarvis_core.runtime.circuit_breaker import FailureReason, classify_failure

        assert classify_failure(TimeoutError("timed out")) == FailureReason.TIMEOUT
        assert classify_failure(ConnectionError("network")) == FailureReason.NETWORK


class TestPerfReport:
    """道M(min) tests."""

    def test_report_schema(self):
        from jarvis_core.perf.report import generate_perf_report

        report = generate_perf_report("test_run", "test_workflow")
        data = report.to_dict()

        # Check fixed schema
        assert "schema_version" in data
        assert "spans" in data
        assert "slo" in data
        assert "budget" in data
        assert "cache" in data


# Sprint 3 Tests


class TestHybridRouter:
    """道I tests."""

    def test_routing_decision(self):
        from jarvis_core.retrieval.hybrid_router import HybridRouter, RouteDecision

        router = HybridRouter()

        # Technical short query -> BM25
        result = router.route("CD73 expression")
        assert result.decision == RouteDecision.BM25_ONLY

        # Conceptual query -> Dense
        result = router.route("How does the immune system work?")
        assert result.decision == RouteDecision.DENSE_ONLY

        # Budget constraint -> BM25
        result = router.route("any query", budget_remaining=0.1)
        assert result.decision == RouteDecision.BM25_ONLY


class TestTwoStageRetriever:
    """道I tests."""

    def test_budget_skip_rerank(self):
        from jarvis_core.retrieval.two_stage import TwoStageRetriever

        retriever = TwoStageRetriever(
            stage1_fn=lambda q, k: [{"id": f"d{i}", "score": 0.5} for i in range(k)],
            stage2_fn=lambda q, c: c,
            budget_threshold=0.5,
        )

        # Low budget - skip rerank
        result = retriever.retrieve("query", budget_remaining=0.3)
        assert result.rerank_skipped


class TestParetoPlanner:
    """道J tests."""

    def test_pareto_selection(self):
        from jarvis_core.cost_planner.pareto import ParetoPlanner

        planner = ParetoPlanner(budget_limit=1.0, min_quality=0.6)

        # Full budget
        plan = planner.plan(budget_remaining=1.0)
        assert plan["estimated_quality"] >= 0.6

        # Limited budget
        plan_limited = planner.plan(budget_remaining=0.2)
        assert plan_limited["estimated_cost"] <= 0.3


class TestPIIScan:
    """道L tests."""

    def test_scan_email(self):
        from jarvis_core.security.pii_scan import PIIScanner, PIIType

        scanner = PIIScanner()
        matches = scanner.scan("Contact: test@example.com for info")

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.EMAIL

    def test_redaction(self):
        from jarvis_core.security.redaction import redact_text

        text = "Email: user@test.com, Phone: 123-456-7890"
        redacted = redact_text(text)

        assert "user@test.com" not in redacted
        assert "123-456-7890" not in redacted
        assert "█" in redacted


class TestStoragePolicy:
    """道L tests."""

    def test_policy_check(self):
        from jarvis_core.security.storage_policy import check_storage_policy

        data = {
            "text": "Email: test@example.com",
            "password": "secret123",
        }
        result = check_storage_policy(data)

        assert not result.compliant
        assert len(result.violations) > 0


class TestDashboard:
    """道M(full) tests."""

    def test_dashboard_schema(self):
        from jarvis_core.perf.dashboard import generate_dashboard

        dashboard = generate_dashboard("test_run", "test_workflow")
        data = dashboard.to_dict()

        # Check fixed schema
        assert data["schema_version"] == "1.0"
        assert "performance" in data
        assert "cost" in data
        assert "cache" in data
        assert "quality" in data
        assert "slo" in data
        assert "budget" in data

    def test_scorecard(self):
        from jarvis_core.perf.dashboard import generate_scorecard

        scorecard = generate_scorecard("test_run")
        assert scorecard.run_id == "test_run"
