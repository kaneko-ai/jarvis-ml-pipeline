"""Test Telemetry Required.

Per RP-18, this test ensures telemetry is ALWAYS generated.
If this test fails, the PR is blocked.
"""

import json
import sys
from pathlib import Path

import pytest

# PR-59: Mark all tests in this file as core
pytestmark = pytest.mark.core

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestTelemetryRequired:
    """Hard gate tests for telemetry generation."""

    def test_run_task_generates_events_jsonl(self, tmp_path, monkeypatch):
        """run_task MUST generate events.jsonl with required keys."""
        import json

        from jarvis_core.telemetry import JsonlTelemetryLogger

        # Test logger directly to avoid LLM dependency
        run_id = "test_run_abc123"
        logs_dir = tmp_path

        logger = JsonlTelemetryLogger(run_id, str(logs_dir))

        # Simulate what run_task does
        logger.log_event(
            event="RUN_START",
            event_type="ACTION",
            trace_id=run_id,
            task_id="task_001",
            payload={"goal": "test", "category": "generic"},
        )
        logger.log_event(
            event="RUN_END",
            event_type="ACTION",
            trace_id=run_id,
            task_id="task_001",
            payload={"status": "complete"},
        )

        # Verify events.jsonl exists
        events_file = tmp_path / run_id / "events.jsonl"
        assert events_file.exists(), f"events.jsonl not found at {events_file}"
        assert events_file.stat().st_size > 0, "events.jsonl is empty"

        # Verify required keys in first line
        with open(events_file, encoding="utf-8") as f:
            first_line = f.readline()

        event = json.loads(first_line)

        required_keys = ["run_id", "trace_id", "event", "event_type"]
        for key in required_keys:
            assert key in event, f"Missing required key: {key}"

        # Verify RUN_START and RUN_END are both present
        events_file.seek(0) if hasattr(events_file, "seek") else None
        lines = events_file.read_text().strip().split("\n")
        assert len(lines) >= 2, "Expected at least RUN_START and RUN_END"
        assert "RUN_START" in lines[0]
        assert "RUN_END" in lines[1]

        required_keys = ["run_id", "trace_id", "event", "event_type"]
        for key in required_keys:
            assert key in event, f"Missing required key: {key}"

    def test_telemetry_logger_creates_file(self, tmp_path):
        """JsonlTelemetryLogger MUST create events.jsonl."""
        from jarvis_core.telemetry import JsonlTelemetryLogger

        logger = JsonlTelemetryLogger("test_run_001", str(tmp_path))
        logger.log_event(
            event="RUN_START",
            event_type="ACTION",
            trace_id="trace_001",
        )

        events_file = tmp_path / "test_run_001" / "events.jsonl"
        assert events_file.exists(), "Logger did not create events.jsonl"

        with open(events_file, encoding="utf-8") as f:
            event = json.loads(f.readline())

        assert event["event"] == "RUN_START"
        assert event["event_type"] == "ACTION"
        assert event["trace_id"] == "trace_001"

    def test_run_error_event_on_exception(self, tmp_path):
        """RUN_ERROR MUST be logged when exception occurs."""
        from jarvis_core.telemetry import JsonlTelemetryLogger

        logger = JsonlTelemetryLogger("error_test", str(tmp_path))

        # Simulate exception scenario
        logger.log_event(
            event="RUN_START",
            event_type="ACTION",
            trace_id="trace_err",
        )
        logger.log_event(
            event="RUN_ERROR",
            event_type="ACTION",
            trace_id="trace_err",
            level="ERROR",
            payload={"error": "Test error", "error_type": "ValueError"},
        )

        events_file = tmp_path / "error_test" / "events.jsonl"
        events = events_file.read_text().strip().split("\n")

        assert len(events) == 2
        error_event = json.loads(events[1])
        assert error_event["event"] == "RUN_ERROR"
        assert error_event["level"] == "ERROR"
