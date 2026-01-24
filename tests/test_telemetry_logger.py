"""Tests for telemetry.logger module."""

from jarvis_core.telemetry.logger import (
    JsonlTelemetryLogger,
    init_logger,
    get_logger,
)
from jarvis_core.telemetry.schema import TelemetryEvent


class TestJsonlTelemetryLogger:
    def test_init_creates_directory(self, tmp_path):
        logs_dir = tmp_path / "logs" / "runs"
        logger = JsonlTelemetryLogger("run-123", str(logs_dir))

        assert logger.run_dir.exists()
        assert logger.run_id == "run-123"

    def test_next_step_increments(self, tmp_path):
        logger = JsonlTelemetryLogger("run-1", str(tmp_path))

        step1 = logger._next_step()
        step2 = logger._next_step()
        step3 = logger._next_step()

        assert step1 == 1
        assert step2 == 2
        assert step3 == 3

    def test_log_event_writes_file(self, tmp_path):
        logger = JsonlTelemetryLogger("run-1", str(tmp_path))

        event = logger.log_event(
            event="TestEvent",
            event_type="test",
            trace_id="trace-1",
            level="INFO",
        )

        assert event is not None
        assert logger.events_file.exists()

    def test_log_telemetry_event(self, tmp_path):
        logger = JsonlTelemetryLogger("run-1", str(tmp_path))

        event = TelemetryEvent.create(
            run_id="run-1",
            trace_id="trace-1",
            step_id=1,
            event="Test",
            event_type="test",
        )

        logger.log(event)

        assert logger.events_file.exists()

    def test_flush_and_close(self, tmp_path):
        logger = JsonlTelemetryLogger("run-1", str(tmp_path))

        # Should not raise
        logger.flush()
        logger.close()


class TestGlobalLoggerFunctions:
    def test_init_and_get_logger(self, tmp_path):
        logger = init_logger("global-run", str(tmp_path))

        assert logger is not None
        assert get_logger() == logger
