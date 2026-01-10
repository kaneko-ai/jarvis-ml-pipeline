"""Tests for trace module."""

import json
from datetime import datetime
from unittest.mock import patch

import pytest
from jarvis_core.trace import (
    TraceStep,
    RunTrace,
    start_trace,
    get_current_trace,
    trace_step,
)


class TestTraceStep:
    def test_to_dict(self):
        step = TraceStep(
            step_id="step_1",
            name="test_step",
            started_at=datetime(2024, 1, 1, 10, 0, 0),
            ended_at=datetime(2024, 1, 1, 10, 0, 1),
            status="success",
            artifact_id="art_1",
            metadata={"key": "value"},
        )
        d = step.to_dict()
        assert d["step_id"] == "step_1"
        assert d["name"] == "test_step"
        assert d["status"] == "success"
        assert d["artifact_id"] == "art_1"
        assert d["duration_ms"] == 1000  # 1 second

    def test_duration_ms_none_when_not_ended(self):
        step = TraceStep(
            step_id="step_1",
            name="test_step",
            started_at=datetime.now(),
        )
        assert step.duration_ms is None


class TestRunTrace:
    def test_init(self):
        trace = RunTrace("test_workflow", run_id="run_123")
        assert trace.workflow == "test_workflow"
        assert trace.run_id == "run_123"
        assert trace.status == "running"
        assert len(trace.steps) == 0

    def test_start_and_end_step(self):
        trace = RunTrace("test_workflow")
        step_id = trace.start_step("step_name", {"meta": "data"})
        
        assert len(trace.steps) == 1
        assert trace.steps[0].name == "step_name"
        assert trace.steps[0].status == "running"
        
        trace.end_step(step_id, "success", artifact_id="art_1")
        
        assert trace.steps[0].status == "success"
        assert trace.steps[0].artifact_id == "art_1"
        assert trace.steps[0].ended_at is not None

    def test_finish(self):
        trace = RunTrace("test_workflow")
        step_id = trace.start_step("step_name")
        # Don't end the step manually
        
        trace.finish("success")
        
        assert trace.status == "success"
        assert trace.ended_at is not None
        # Running step should be marked as aborted
        assert trace.steps[0].status == "aborted"

    def test_to_dict(self):
        trace = RunTrace("test_workflow", run_id="run_1")
        trace.start_step("step_1")
        trace.finish()
        
        d = trace.to_dict()
        assert d["workflow"] == "test_workflow"
        assert d["run_id"] == "run_1"
        assert len(d["steps"]) == 1

    def test_save(self, tmp_path):
        trace = RunTrace("test_workflow", run_id="run_1")
        trace.start_step("step_1")
        trace.finish()
        
        path = trace.save(str(tmp_path))
        
        assert (tmp_path / "workflows" / "run_trace.json").exists()
        
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data["workflow"] == "test_workflow"


class TestGlobalTrace:
    def test_start_and_get_trace(self):
        trace = start_trace("global_workflow")
        current = get_current_trace()
        
        assert current is trace
        assert current.workflow == "global_workflow"

    def test_trace_step_decorator(self):
        start_trace("decorator_test")
        
        @trace_step("decorated_step", {"info": "test"})
        def my_function():
            return "result"
        
        result = my_function()
        
        assert result == "result"
        trace = get_current_trace()
        assert len(trace.steps) == 1
        assert trace.steps[0].name == "decorated_step"
        assert trace.steps[0].status == "success"

    def test_trace_step_decorator_with_error(self):
        start_trace("error_test")
        
        @trace_step("error_step")
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        trace = get_current_trace()
        assert trace.steps[0].status == "failed"
        assert "Test error" in trace.steps[0].error
