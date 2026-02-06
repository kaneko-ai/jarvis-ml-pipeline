"""Benchmark utilities for evaluation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    """Simple benchmark result container."""

    name: str = "benchmark"
    score: float = 0.0


class BenchmarkRunner:
    """Minimal benchmark runner."""

    def run(self) -> BenchmarkResult:
        """Run the benchmark and return a result."""
        return BenchmarkResult()
