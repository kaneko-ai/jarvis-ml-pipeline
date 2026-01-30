"""Tests for telemetry.trace_context module."""

import pytest
from jarvis_core.telemetry.trace_context import (
    TraceContext,
    get_current_context,
    set_current_context,
    require_context,
    TraceContextManager,
    trace_tool,
)


class TestTraceContext:
    def test_create(self):
        ctx = TraceContext.create()

        assert ctx.run_id is not None
        assert ctx.trace_id is not None
        assert ctx.step_id == 0

    def test_create_with_run_id(self):
        ctx = TraceContext.create(run_id="custom_run")
        assert ctx.run_id == "custom_run"

    def test_with_step(self):
        ctx = TraceContext.create()
        new_ctx = ctx.with_step(5)

        assert new_ctx.step_id == 5
        assert new_ctx.parent_step_id == ctx.step_id
        assert new_ctx.run_id == ctx.run_id

    def test_with_tool(self):
        ctx = TraceContext.create()
        new_ctx = ctx.with_tool("search_tool")

        assert new_ctx.tool_name == "search_tool"
        assert new_ctx.run_id == ctx.run_id

    def test_to_dict(self):
        ctx = TraceContext(
            run_id="run1",
            trace_id="trace1",
            step_id=3,
            parent_step_id=2,
            tool_name="test_tool",
        )
        d = ctx.to_dict()

        assert d["run_id"] == "run1"
        assert d["trace_id"] == "trace1"
        assert d["step_id"] == 3
        assert d["parent_step_id"] == 2
        assert d["tool_name"] == "test_tool"


class TestContextFunctions:
    def test_set_and_get_context(self):
        ctx = TraceContext.create()
        set_current_context(ctx)

        current = get_current_context()
        assert current == ctx

    def test_require_context_when_set(self):
        ctx = TraceContext.create()
        set_current_context(ctx)

        result = require_context()
        assert result == ctx

    def test_require_context_when_not_set(self):
        # Clear context
        from jarvis_core.telemetry.trace_context import _current_context

        _current_context.set(None)

        with pytest.raises(RuntimeError, match="TraceContext required"):
            require_context()


class TestTraceContextManager:
    def test_init(self):
        manager = TraceContextManager()
        assert manager.context is not None
        assert manager._step_counter == 0

    def test_init_with_run_id(self):
        manager = TraceContextManager(run_id="custom")
        assert manager.context.run_id == "custom"

    def test_next_step(self):
        manager = TraceContextManager()

        ctx1 = manager.next_step()
        ctx2 = manager.next_step()

        assert ctx1.step_id == 1
        assert ctx2.step_id == 2

    def test_enter_tool(self):
        manager = TraceContextManager()
        ctx = manager.enter_tool("my_tool")

        assert ctx.tool_name == "my_tool"
        assert ctx.step_id == 1

    def test_context_manager(self):
        with TraceContextManager(run_id="test"):
            ctx = get_current_context()
            assert ctx is not None
            assert ctx.run_id == "test"

        # Context should be cleared after exit
        # Note: This may need adjustment based on implementation


class TestTraceTool:
    def test_trace_tool_decorator(self):
        # Set up context
        ctx = TraceContext.create()
        set_current_context(ctx)

        @trace_tool("decorated_tool")
        def my_func():
            return "result"

        result = my_func()

        assert result == "result"
        # Current context should have tool name
        current = get_current_context()
        assert current.tool_name == "decorated_tool"
