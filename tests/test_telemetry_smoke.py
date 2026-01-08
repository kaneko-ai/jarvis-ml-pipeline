"""Tests for RP-02 Telemetry."""

import sys
import tempfile
from pathlib import Path

import pytest

# PR-59: Mark all tests in this file as core
pytestmark = pytest.mark.core

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestTelemetrySchema:
    """RP-02 Telemetry schema tests."""

    def test_event_creation(self):
        from jarvis_core.telemetry import TelemetryEvent

        event = TelemetryEvent.create(
            run_id="run_001",
            trace_id="trace_001",
            step_id=1,
            event="TOOL_CALLED",
            event_type="ACTION",
            tool="search",
        )
        assert event.run_id == "run_001"
        assert event.event == "TOOL_CALLED"
        assert event.event_type == "ACTION"

    def test_event_to_dict(self):
        from jarvis_core.telemetry import TelemetryEvent

        event = TelemetryEvent.create(
            run_id="run_001",
            trace_id="trace_001",
            step_id=1,
            event="DONE",
            event_type="COORDINATION",
        )
        d = event.to_dict()
        assert "ts" in d
        assert d["run_id"] == "run_001"
        assert d["event"] == "DONE"


class TestTelemetryLogger:
    """RP-02 JSONL logger tests."""

    def test_logger_creates_file(self):
        from jarvis_core.telemetry import JsonlTelemetryLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = JsonlTelemetryLogger("test_run", tmpdir)
            logger.log_event(
                event="PLAN_CREATED",
                event_type="COORDINATION",
                trace_id="t1",
            )

            events_file = Path(tmpdir) / "test_run" / "events.jsonl"
            assert events_file.exists()

            content = events_file.read_text()
            assert "PLAN_CREATED" in content
            assert "test_run" in content

    def test_required_fields_present(self):
        import json

        from jarvis_core.telemetry import JsonlTelemetryLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = JsonlTelemetryLogger("test_run", tmpdir)
            logger.log_event(
                event="TOOL_CALLED",
                event_type="ACTION",
                trace_id="t1",
                tool="pubmed_search",
            )

            events_file = Path(tmpdir) / "test_run" / "events.jsonl"
            line = events_file.read_text().strip()
            data = json.loads(line)

            # Required fields per JARVIS_MASTER.md Section 8
            assert "run_id" in data
            assert "trace_id" in data
            assert "step_id" in data
            assert "event" in data
            assert "event_type" in data
            assert "ts" in data


class TestHashing:
    """RP-02 Hashing tests."""

    def test_prompt_hash_deterministic(self):
        from jarvis_core.telemetry import prompt_hash

        h1 = prompt_hash("Test prompt")
        h2 = prompt_hash("Test prompt")
        assert h1 == h2

    def test_prompt_hash_normalized(self):
        from jarvis_core.telemetry import prompt_hash

        h1 = prompt_hash("Test   prompt")
        h2 = prompt_hash("test prompt")
        assert h1 == h2  # Normalization makes them equal

    def test_input_hash_dict(self):
        from jarvis_core.telemetry import input_hash

        h1 = input_hash({"a": 1, "b": 2})
        h2 = input_hash({"b": 2, "a": 1})  # Different order
        assert h1 == h2  # Sort keys makes them equal
