"""Pipeline Metrics (Phase 40).

Tracks and exposes KPIs (Key Performance Indicators) for observability.
Compatible with Prometheus exposition format.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class PipelineMetrics:
    """Collector for pipeline metrics."""

    def __init__(self):
        # Counter: MetricName -> LabelSet -> Value
        self._counters: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        # Gauge: MetricName -> LabelSet -> Value
        self._gauges: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        # Histogram: MetricName -> LabelSet -> List[float]
        self._histograms: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))

    def inc_counter(self, name: str, labels: Optional[Dict[str, str]] = None, value: float = 1.0):
        """Increment a counter."""
        label_key = self._format_labels(labels)
        self._counters[name][label_key] += value

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge value."""
        label_key = self._format_labels(labels)
        self._gauges[name][label_key] = value

    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value in a histogram."""
        label_key = self._format_labels(labels)
        self._histograms[name][label_key].append(value)

    def _format_labels(self, labels: Optional[Dict[str, str]]) -> str:
        """Format labels as a sorted string tuple for keys."""
        if not labels:
            return ""
        return ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))

    def generate_prometheus_output(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []

        # Counters
        for name, data in self._counters.items():
            lines.append(f"# TYPE {name} counter")
            for label_key, value in data.items():
                lbl = f"{{{label_key}}}" if label_key else ""
                lines.append(f"{name}{lbl} {value}")

        # Gauges
        for name, data in self._gauges.items():
            lines.append(f"# TYPE {name} gauge")
            for label_key, value in data.items():
                lbl = f"{{{label_key}}}" if label_key else ""
                lines.append(f"{name}{lbl} {value}")

        # Histograms (Simplified: just count and sum for now)
        for name, data in self._histograms.items():
            lines.append(f"# TYPE {name} histogram")
            for label_key, values in data.items():
                lbl_content = label_key

                # Count
                lines.append(f"{name}_count{{{lbl_content}}} {len(values)}")
                # Sum
                lines.append(f"{name}_sum{{{lbl_content}}} {sum(values)}")

        return "\n".join(lines) + "\n"


# Global instance
metrics = PipelineMetrics()
