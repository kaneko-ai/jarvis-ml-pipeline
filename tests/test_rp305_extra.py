"""Tests for additional RP implementations.

Core tests for RP-305, RP-322, RP-385, RP-439, etc.
"""
import pytest
from datetime import datetime

pytestmark = pytest.mark.core


class TestSemanticDedup:
    """Tests for RP-305 Semantic Deduplication."""

    def test_text_based_dedup(self):
        """Should deduplicate based on text."""
        from jarvis_core.retrieval.semantic_dedup import SemanticDeduplicator

        dedup = SemanticDeduplicator()

        chunks = [
            {"chunk_id": "1", "text": "Hello world", "doc_id": "a"},
            {"chunk_id": "2", "text": "Hello world", "doc_id": "b"},
            {"chunk_id": "3", "text": "Different text", "doc_id": "a"},
        ]

        deduped = dedup.deduplicate(chunks)

        # Should remove one duplicate
        assert len(deduped) == 2


class TestTemporalKG:
    """Tests for RP-323 Temporal Knowledge Graph."""

    def test_add_temporal_triple(self):
        """Should add temporal triple."""
        from jarvis_tools.kg.temporal_kg import TemporalKnowledgeGraph

        tkg = TemporalKnowledgeGraph()

        triple = tkg.add_triple(
            subject="CD73",
            predicate="inhibits",
            obj="T cell activation",
            valid_from=datetime(2020, 1, 1),
        )

        assert triple.subject == "CD73"
        assert triple.valid_from == datetime(2020, 1, 1)

    def test_query_as_of(self):
        """Should query at specific time."""
        from jarvis_tools.kg.temporal_kg import TemporalKnowledgeGraph

        tkg = TemporalKnowledgeGraph()

        # Add two triples with different time ranges
        tkg.add_triple(
            "CD73", "expressed_in", "tumor",
            valid_from=datetime(2015, 1, 1),
            valid_to=datetime(2020, 1, 1),
        )
        tkg.add_triple(
            "CD73", "expressed_in", "immune cells",
            valid_from=datetime(2020, 1, 1),
        )

        # Query as of 2018
        results = tkg.query_as_of("CD73", datetime(2018, 1, 1))
        assert len(results) >= 1


class TestDashboardAPI:
    """Tests for RP-385 Dashboard API."""

    def test_get_stats(self):
        """Should get dashboard stats."""
        import sys
        # Skip if FastAPI causes issues
        try:
            from jarvis_web.dashboard import DashboardAPI
        except Exception:
            pytest.skip("jarvis_web import issue")

        api = DashboardAPI()
        stats = api.get_stats()

        assert hasattr(stats, "total_runs")
        assert hasattr(stats, "successful_runs")


class TestObservability:
    """Tests for RP-439 Observability Stack."""

    def test_tracer_span(self):
        """Should create spans."""
        from jarvis_core.observability import Tracer

        tracer = Tracer(service_name="test")

        with tracer.span("test_operation") as span:
            assert span.operation == "test_operation"

        assert span.end_time is not None

    def test_metrics_counter(self):
        """Should track counters."""
        from jarvis_core.observability import MetricsCollector

        metrics = MetricsCollector()

        metrics.counter("requests_total", 1)
        metrics.counter("requests_total", 1)

        all_metrics = metrics.get_metrics()
        assert len(all_metrics) >= 2

    def test_logger(self):
        """Should log messages."""
        from jarvis_core.observability import Logger

        logger = Logger(name="test")

        logger.info("Test message", extra="data")
        logger.error("Error message")

        assert len(logger._logs) == 2
