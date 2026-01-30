"""Tests for telemetry.analyze module."""

import json

from jarvis_core.telemetry.analyze import (
    StepStats,
    FailureRecord,
    RunAnalysis,
    analyze_events,
    print_analysis,
)


class TestStepStats:
    def test_success_rate_with_data(self):
        stats = StepStats(step_type="test", count=10, success_count=8)
        assert stats.success_rate == 0.8

    def test_success_rate_zero_count(self):
        stats = StepStats(step_type="test", count=0)
        assert stats.success_rate == 0.0

    def test_avg_duration_with_data(self):
        stats = StepStats(step_type="test", count=5, total_duration_ms=500.0)
        assert stats.avg_duration_ms == 100.0

    def test_avg_duration_zero_count(self):
        stats = StepStats(step_type="test", count=0)
        assert stats.avg_duration_ms == 0.0


class TestFailureRecord:
    def test_creation(self):
        record = FailureRecord(
            event="tool_error",
            error_type="ValueError",
            error_message="Invalid input",
            step_id=5,
            tool="search",
        )
        assert record.event == "tool_error"
        assert record.error_type == "ValueError"
        assert record.step_id == 5


class TestRunAnalysis:
    def test_creation(self):
        analysis = RunAnalysis(
            run_id="test_run",
            total_events=100,
            step_stats={},
            top_failures=[],
            timeline=["event1", "event2"],
        )
        assert analysis.run_id == "test_run"
        assert analysis.total_events == 100


class TestAnalyzeEvents:
    def test_analyze_basic_events(self, tmp_path):
        events_file = tmp_path / "events.jsonl"
        events = [
            {
                "run_id": "run1",
                "event": "start",
                "event_type": "run",
                "level": "INFO",
                "ts": "2024-01-01T00:00:00",
            },
            {"event": "step", "event_type": "step", "level": "INFO", "ts": "2024-01-01T00:00:01"},
            {
                "event": "error",
                "event_type": "step",
                "level": "ERROR",
                "ts": "2024-01-01T00:00:02",
                "payload": {"error_type": "ValueError", "error": "test error"},
            },
        ]
        events_file.write_text("\n".join(json.dumps(e) for e in events))

        analysis = analyze_events(events_file)

        assert analysis.run_id == "run1"
        assert analysis.total_events == 3
        assert "step" in analysis.step_stats
        assert len(analysis.top_failures) == 1

    def test_analyze_empty_run_id(self, tmp_path):
        events_file = tmp_path / "events.jsonl"
        events = [{"event": "test", "event_type": "step", "level": "INFO", "ts": "2024-01-01"}]
        events_file.write_text(json.dumps(events[0]))

        analysis = analyze_events(events_file)
        assert analysis.run_id == "unknown"


class TestPrintAnalysis:
    def test_print_analysis(self, capsys):
        analysis = RunAnalysis(
            run_id="test_run",
            total_events=50,
            step_stats={"step": StepStats("step", count=10, success_count=9, error_count=1)},
            top_failures=[FailureRecord("error", "ValueError", "test error")],
            timeline=[],
        )

        print_analysis(analysis)

        captured = capsys.readouterr()
        assert "test_run" in captured.out
        assert "50" in captured.out