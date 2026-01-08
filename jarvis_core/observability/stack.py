"""Observability Stack.

Per RP-439, implements comprehensive observability.
"""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Span:
    """A trace span."""

    span_id: str
    trace_id: str
    parent_id: str | None
    operation: str
    start_time: float
    end_time: float | None
    tags: dict[str, str] = field(default_factory=dict)
    logs: list[dict[str, Any]] = field(default_factory=list)
    status: str = "ok"


@dataclass
class Metric:
    """A metric measurement."""

    name: str
    value: float
    timestamp: float
    tags: dict[str, str] = field(default_factory=dict)
    metric_type: str = "gauge"  # gauge, counter, histogram


class Tracer:
    """Distributed tracing.

    Per RP-439:
    - Jaeger-compatible tracing
    - Span management
    - Distributed context
    """

    def __init__(
        self,
        service_name: str = "jarvis",
        exporter=None,
    ):
        self.service_name = service_name
        self.exporter = exporter
        self._spans: dict[str, Span] = {}
        self._current_trace: str | None = None
        self._span_stack: list[str] = []

    def start_span(
        self,
        operation: str,
        trace_id: str | None = None,
        parent_id: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> Span:
        """Start a new span.

        Args:
            operation: Operation name.
            trace_id: Optional trace ID.
            parent_id: Optional parent span ID.
            tags: Optional tags.

        Returns:
            Started span.
        """
        import uuid

        span_id = str(uuid.uuid4())[:16]

        if trace_id is None:
            if self._current_trace:
                trace_id = self._current_trace
            else:
                trace_id = str(uuid.uuid4())[:16]
                self._current_trace = trace_id

        if parent_id is None and self._span_stack:
            parent_id = self._span_stack[-1]

        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_id=parent_id,
            operation=operation,
            start_time=time.time(),
            end_time=None,
            tags=tags or {},
        )

        span.tags["service"] = self.service_name

        self._spans[span_id] = span
        self._span_stack.append(span_id)

        return span

    def end_span(
        self,
        span: Span,
        status: str = "ok",
    ) -> None:
        """End a span.

        Args:
            span: Span to end.
            status: Final status.
        """
        span.end_time = time.time()
        span.status = status

        if span.span_id in self._span_stack:
            self._span_stack.remove(span.span_id)

        if self.exporter:
            self.exporter.export_span(span)

    @contextmanager
    def span(
        self,
        operation: str,
        tags: dict[str, str] | None = None,
    ):
        """Context manager for spans.

        Args:
            operation: Operation name.
            tags: Optional tags.
        """
        span = self.start_span(operation, tags=tags)
        try:
            yield span
            self.end_span(span, status="ok")
        except Exception as e:
            span.logs.append(
                {
                    "timestamp": time.time(),
                    "event": "error",
                    "message": str(e),
                }
            )
            self.end_span(span, status="error")
            raise


class MetricsCollector:
    """Metrics collection.

    Per RP-439:
    - Prometheus-compatible metrics
    - Custom metrics
    - Aggregation
    """

    def __init__(self):
        self._metrics: list[Metric] = []
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}

    def counter(
        self,
        name: str,
        value: float = 1,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Increment a counter.

        Args:
            name: Metric name.
            value: Increment value.
            tags: Optional tags.
        """
        key = f"{name}:{json.dumps(tags or {}, sort_keys=True)}"
        self._counters[key] = self._counters.get(key, 0) + value

        self._metrics.append(
            Metric(
                name=name,
                value=self._counters[key],
                timestamp=time.time(),
                tags=tags or {},
                metric_type="counter",
            )
        )

    def gauge(
        self,
        name: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Set a gauge value.

        Args:
            name: Metric name.
            value: Gauge value.
            tags: Optional tags.
        """
        key = f"{name}:{json.dumps(tags or {}, sort_keys=True)}"
        self._gauges[key] = value

        self._metrics.append(
            Metric(
                name=name,
                value=value,
                timestamp=time.time(),
                tags=tags or {},
                metric_type="gauge",
            )
        )

    def histogram(
        self,
        name: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Record a histogram value.

        Args:
            name: Metric name.
            value: Value to record.
            tags: Optional tags.
        """
        self._metrics.append(
            Metric(
                name=name,
                value=value,
                timestamp=time.time(),
                tags=tags or {},
                metric_type="histogram",
            )
        )

    def get_metrics(
        self,
        since: float | None = None,
    ) -> list[Metric]:
        """Get collected metrics.

        Args:
            since: Optional timestamp filter.

        Returns:
            List of metrics.
        """
        if since:
            return [m for m in self._metrics if m.timestamp >= since]
        return list(self._metrics)

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format.

        Returns:
            Prometheus exposition format string.
        """
        lines = []

        # Counters
        for key, value in self._counters.items():
            name = key.split(":")[0]
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")

        # Gauges
        for key, value in self._gauges.items():
            name = key.split(":")[0]
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")

        return "\n".join(lines)


class Logger:
    """Structured logging.

    Per RP-439:
    - ELK-compatible logging
    - Structured JSON output
    - Log levels
    """

    def __init__(
        self,
        name: str = "jarvis",
        output_path: str | None = None,
    ):
        self.name = name
        self.output_path = output_path
        self._logs: list[dict[str, Any]] = []

    def _log(
        self,
        level: str,
        message: str,
        **kwargs,
    ) -> None:
        """Internal log method."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "logger": self.name,
            "message": message,
            **kwargs,
        }

        self._logs.append(entry)

        if self.output_path:
            with open(self.output_path, "a") as f:
                f.write(json.dumps(entry) + "\n")

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._log("debug", message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._log("info", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._log("warning", message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self._log("error", message, **kwargs)


# Global instances
_tracer: Tracer | None = None
_metrics: MetricsCollector | None = None
_logger: Logger | None = None


def get_tracer() -> Tracer:
    """Get global tracer."""
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer


def get_metrics() -> MetricsCollector:
    """Get global metrics collector."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics


def get_logger() -> Logger:
    """Get global logger."""
    global _logger
    if _logger is None:
        _logger = Logger()
    return _logger
