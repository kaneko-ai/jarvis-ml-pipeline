"""Trace Spans.

Per V4-C01, this provides workflow→module→stage measurement.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class Span:
    """A traced span of execution."""

    span_id: str
    name: str
    parent_id: str | None
    start_time: float
    end_time: float | None = None
    item_count: int = 0
    metadata: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> float | None:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None

    def to_dict(self) -> dict:
        return {
            "span_id": self.span_id,
            "name": self.name,
            "parent_id": self.parent_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "item_count": self.item_count,
            "metadata": self.metadata,
        }


class SpanTracker:
    """Track execution spans for performance analysis."""

    def __init__(self):
        self.spans: list[Span] = []
        self._span_stack: list[str] = []
        self._span_counter = 0

    def start_span(
        self,
        name: str,
        metadata: dict = None,
    ) -> str:
        """Start a new span.

        Args:
            name: Span name.
            metadata: Optional metadata.

        Returns:
            Span ID.
        """
        self._span_counter += 1
        span_id = f"span_{self._span_counter}"

        parent_id = self._span_stack[-1] if self._span_stack else None

        span = Span(
            span_id=span_id,
            name=name,
            parent_id=parent_id,
            start_time=time.time(),
            metadata=metadata or {},
        )

        self.spans.append(span)
        self._span_stack.append(span_id)

        return span_id

    def end_span(self, span_id: str, item_count: int = 0) -> None:
        """End a span.

        Args:
            span_id: Span ID to end.
            item_count: Number of items processed.
        """
        for span in self.spans:
            if span.span_id == span_id:
                span.end_time = time.time()
                span.item_count = item_count
                break

        if self._span_stack and self._span_stack[-1] == span_id:
            self._span_stack.pop()

    @contextmanager
    def span(self, name: str, metadata: dict = None):
        """Context manager for spans."""
        span_id = self.start_span(name, metadata)
        try:
            yield span_id
        finally:
            self.end_span(span_id)

    def get_summary(self) -> dict:
        """Get summary of all spans."""
        by_name = {}
        for span in self.spans:
            if span.name not in by_name:
                by_name[span.name] = {
                    "count": 0,
                    "total_ms": 0,
                    "total_items": 0,
                }
            by_name[span.name]["count"] += 1
            by_name[span.name]["total_ms"] += span.duration_ms or 0
            by_name[span.name]["total_items"] += span.item_count

        return by_name

    def to_dict(self) -> dict:
        return {
            "spans": [s.to_dict() for s in self.spans],
            "summary": self.get_summary(),
        }


# Global tracker
_tracker: SpanTracker | None = None


def init_tracker() -> SpanTracker:
    """Initialize global tracker."""
    global _tracker
    _tracker = SpanTracker()
    return _tracker


def get_tracker() -> SpanTracker:
    """Get or create global tracker."""
    global _tracker
    if _tracker is None:
        _tracker = SpanTracker()
    return _tracker


def start_span(name: str, metadata: dict = None) -> str:
    """Start a span on global tracker."""
    return get_tracker().start_span(name, metadata)


def end_span(span_id: str, item_count: int = 0) -> None:
    """End a span on global tracker."""
    get_tracker().end_span(span_id, item_count)


def get_current_spans() -> list[Span]:
    """Get current spans."""
    return get_tracker().spans
