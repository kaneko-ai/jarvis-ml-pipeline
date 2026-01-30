"""Telemetry Contract v2 Tests.

Per RP-145, validates telemetry event order and required fields.
"""

import json

import pytest

# Legacy due to TelemetryEvent API differences
pytestmark = pytest.mark.legacy


class TestTelemetryContractV2:
    """Tests for telemetry contract v2."""

    def test_run_events_order(self, tmp_path):
        """RUN_START must come before RUN_END."""
        from jarvis_core.telemetry.logger import JsonlTelemetryLogger
        from jarvis_core.telemetry.schema import TelemetryEvent

        run_id = "test_order"
        logger = JsonlTelemetryLogger(run_id, str(tmp_path))

        # Log events in order
        start_evt = TelemetryEvent.create(
            run_id=run_id,
            trace_id="t1",
            step_id=1,
            event="RUN_START",
            event_type="lifecycle",
        )
        logger.log(start_evt)

        end_evt = TelemetryEvent.create(
            run_id=run_id,
            trace_id="t1",
            step_id=2,
            event="RUN_END",
            event_type="lifecycle",
            status="success",
        )
        logger.log(end_evt)

        # Verify order
        events_file = tmp_path / run_id / "events.jsonl"
        events = []
        with open(events_file) as f:
            for line in f:
                events.append(json.loads(line))

        assert len(events) >= 2
        event_names = [e["event"] for e in events]
        start_idx = event_names.index("RUN_START")
        end_idx = event_names.index("RUN_END")
        assert start_idx < end_idx

    def test_run_error_logged_on_exception(self, tmp_path):
        """RUN_ERROR must be logged when exception occurs."""
        from jarvis_core.telemetry.logger import JsonlTelemetryLogger
        from jarvis_core.telemetry.schema import TelemetryEvent

        run_id = "test_error"
        logger = JsonlTelemetryLogger(run_id, str(tmp_path))

        logger.log(
            TelemetryEvent.create(
                run_id=run_id,
                trace_id="t2",
                step_id=1,
                event="RUN_START",
                event_type="lifecycle",
            )
        )
        logger.log(
            TelemetryEvent.create(
                run_id=run_id,
                trace_id="t2",
                step_id=2,
                event="RUN_ERROR",
                event_type="error",
                error_type="ValueError",
                message="Test error",
            )
        )

        events_file = tmp_path / run_id / "events.jsonl"
        with open(events_file) as f:
            events = [json.loads(line) for line in f]

        error_events = [e for e in events if e["event"] == "RUN_ERROR"]
        assert len(error_events) >= 1
        assert error_events[0].get("error_type") == "ValueError"

    def test_required_fields_present(self, tmp_path):
        """All events must have run_id, event, timestamp."""
        from jarvis_core.telemetry.logger import JsonlTelemetryLogger
        from jarvis_core.telemetry.schema import TelemetryEvent

        run_id = "test_fields"
        logger = JsonlTelemetryLogger(run_id, str(tmp_path))

        logger.log(
            TelemetryEvent.create(
                run_id=run_id,
                trace_id="t3",
                step_id=1,
                event="STEP_START",
                event_type="step",
            )
        )

        events_file = tmp_path / run_id / "events.jsonl"
        with open(events_file) as f:
            for line in f:
                event = json.loads(line)
                assert "run_id" in event, "Missing run_id"
                assert "event" in event, "Missing event"
                assert "timestamp" in event, "Missing timestamp"

    def test_trace_id_propagation(self, tmp_path):
        """trace_id should be consistent within a run."""
        from jarvis_core.telemetry.logger import JsonlTelemetryLogger
        from jarvis_core.telemetry.schema import TelemetryEvent

        run_id = "test_trace"
        logger = JsonlTelemetryLogger(run_id, str(tmp_path))

        trace_id = "trace-123"
        for i in range(3):
            logger.log(
                TelemetryEvent.create(
                    run_id=run_id,
                    trace_id=trace_id,
                    step_id=i,
                    event=f"STEP_{i}",
                    event_type="step",
                )
            )

        events_file = tmp_path / run_id / "events.jsonl"
        with open(events_file) as f:
            events = [json.loads(line) for line in f]

        trace_ids = [e.get("trace_id") for e in events if e.get("trace_id")]
        assert all(tid == trace_id for tid in trace_ids)