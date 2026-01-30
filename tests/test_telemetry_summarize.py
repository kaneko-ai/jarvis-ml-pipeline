"""Tests for telemetry summarizer."""

import json
from pathlib import Path
from jarvis_core.telemetry import summarize


def create_dummy_events(path: Path):
    events = [
        {"action": "RUN_START", "timestamp": "2024-01-01T10:00:00Z", "run_id": "r1"},
        {"action": "FETCH_RESULT", "success": True, "step_id": "s1"},
        {"action": "FETCH_RESULT", "success": False, "step_id": "s2"},
        {"action": "CLAIM_GENERATED", "step_id": "s3"},
        {"action": "CITATION_ADDED", "step_id": "s4"},
        {"action": "STEP_FAILED", "step_id": "s5", "error": "Timeout"},
        {"action": "RETRY", "step_id": "s5"},
        {"action": "WARN", "message": "Low memory"},
        {"action": "RUN_ERROR", "error_type": "Critical", "message": "Crash"},
        {"action": "RUN_END", "timestamp": "2024-01-01T10:00:10Z", "status": "failed"},
    ]
    with open(path, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")


class TestRunSummarizer:
    def test_summarize_events(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        create_dummy_events(events_path)

        summary = summarize.summarize_events(str(events_path))

        assert summary.run_id == "r1"
        assert summary.status == "failed"
        assert summary.duration_seconds == 10.0
        assert summary.docs_fetched == 1
        assert summary.claims_generated == 1
        assert summary.citations_added == 1
        assert summary.failed_steps == 1
        assert summary.retry_count == 1
        assert len(summary.top_failures) == 2  # STEP_FAILED and RUN_ERROR
        assert len(summary.warnings) == 1

    def test_file_not_found(self):
        import pytest

        with pytest.raises(FileNotFoundError):
            summarize.summarize_events("nonexistent.jsonl")

    def test_format_summary(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        create_dummy_events(events_path)
        summary = summarize.summarize_events(str(events_path))

        text = summarize.format_summary(summary)

        assert "Run Summary: r1" in text
        assert "Status:      failed" in text
        assert "Docs Fetched:     1" in text
        assert "Top Failures" in text
        assert "Timeout" in text
        assert "Warnings" in text