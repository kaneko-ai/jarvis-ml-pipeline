"""Performance Profiler for JARVIS.

Per JARVIS_COMPLETION_PLAN_v3 Sprint 23: パフォーマンス最適化
Provides profiling and benchmarking utilities.
"""
from __future__ import annotations

import cProfile
import io
import logging
import pstats
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProfileResult:
    """Result of a profiling session."""

    name: str
    elapsed_time: float
    calls: int = 0
    memory_used_mb: float = 0.0
    cpu_percent: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "elapsed_time_ms": self.elapsed_time * 1000,
            "calls": self.calls,
            "memory_used_mb": self.memory_used_mb,
            "cpu_percent": self.cpu_percent,
            "details": self.details,
        }


class Profiler:
    """Performance profiler for JARVIS operations."""

    def __init__(self):
        self._results: list[ProfileResult] = []
        self._enabled = True

    def enable(self) -> None:
        """Enable profiling."""
        self._enabled = True

    def disable(self) -> None:
        """Disable profiling."""
        self._enabled = False

    @contextmanager
    def profile(self, name: str):
        """Context manager for profiling a code block.
        
        Args:
            name: Name of the operation being profiled
            
        Yields:
            ProfileResult that will be populated after the block completes
        """
        if not self._enabled:
            yield ProfileResult(name=name, elapsed_time=0)
            return

        start_time = time.perf_counter()

        # Try to get memory usage
        memory_before = 0.0
        try:
            import psutil
            process = psutil.Process()
            memory_before = process.memory_info().rss / (1024 * 1024)
        except ImportError:
            pass

        result = ProfileResult(name=name, elapsed_time=0)

        try:
            yield result
        finally:
            elapsed = time.perf_counter() - start_time
            result.elapsed_time = elapsed

            # Get memory after
            try:
                import psutil
                process = psutil.Process()
                memory_after = process.memory_info().rss / (1024 * 1024)
                result.memory_used_mb = memory_after - memory_before
            except ImportError:
                pass

            self._results.append(result)
            logger.debug(f"Profile [{name}]: {elapsed*1000:.2f}ms")

    def profile_function(self, func: Callable) -> Callable:
        """Decorator to profile a function.
        
        Args:
            func: Function to profile
            
        Returns:
            Wrapped function
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.profile(func.__name__):
                return func(*args, **kwargs)
        return wrapper

    def get_results(self) -> list[ProfileResult]:
        """Get all profiling results."""
        return self._results.copy()

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of profiling results."""
        if not self._results:
            return {"total_time_ms": 0, "operations": []}

        total_time = sum(r.elapsed_time for r in self._results)

        return {
            "total_time_ms": total_time * 1000,
            "operation_count": len(self._results),
            "operations": [r.to_dict() for r in self._results],
        }

    def clear(self) -> None:
        """Clear all results."""
        self._results.clear()


class CPUProfiler:
    """CPU profiler using cProfile."""

    def __init__(self):
        self._profiler: cProfile.Profile | None = None

    def start(self) -> None:
        """Start CPU profiling."""
        self._profiler = cProfile.Profile()
        self._profiler.enable()

    def stop(self) -> str:
        """Stop CPU profiling and return stats.
        
        Returns:
            Formatted statistics string
        """
        if not self._profiler:
            return ""

        self._profiler.disable()

        stream = io.StringIO()
        stats = pstats.Stats(self._profiler, stream=stream)
        stats.sort_stats("cumulative")
        stats.print_stats(20)  # Top 20 functions

        return stream.getvalue()

    @contextmanager
    def profile(self):
        """Context manager for CPU profiling.
        
        Yields:
            None, stats are available after the block
        """
        self.start()
        try:
            yield
        finally:
            stats = self.stop()
            print(stats)


class BenchmarkRunner:
    """Run benchmarks for performance testing."""

    def __init__(self):
        self._benchmarks: dict[str, Callable] = {}

    def register(self, name: str, func: Callable) -> None:
        """Register a benchmark function."""
        self._benchmarks[name] = func

    def run(
        self,
        name: str | None = None,
        iterations: int = 10,
    ) -> dict[str, dict[str, float]]:
        """Run benchmarks.
        
        Args:
            name: Optional specific benchmark to run
            iterations: Number of iterations per benchmark
            
        Returns:
            Dict of benchmark results
        """
        benchmarks = (
            {name: self._benchmarks[name]}
            if name
            else self._benchmarks
        )

        results = {}

        for bench_name, func in benchmarks.items():
            times = []

            for _ in range(iterations):
                start = time.perf_counter()
                func()
                elapsed = time.perf_counter() - start
                times.append(elapsed)

            results[bench_name] = {
                "mean_ms": (sum(times) / len(times)) * 1000,
                "min_ms": min(times) * 1000,
                "max_ms": max(times) * 1000,
                "iterations": iterations,
            }

        return results


# Global profiler instance
_default_profiler = Profiler()


def profile(name: str):
    """Convenience function for profiling.
    
    Args:
        name: Name of the operation
        
    Returns:
        Context manager
    """
    return _default_profiler.profile(name)


def get_profiler() -> Profiler:
    """Get the default profiler.
    
    Returns:
        Default Profiler instance
    """
    return _default_profiler
