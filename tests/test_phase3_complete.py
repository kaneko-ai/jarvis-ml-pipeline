"""Tests for Documentation, Distribution, and Optimization.

Tests for Task 3.3-3.5
"""

import time


class TestPerformanceUtils:
    """Tests for performance utilities."""

    def test_performance_metrics_dataclass(self):
        """Test PerformanceMetrics dataclass."""
        from jarvis_core.utils.performance import PerformanceMetrics

        metrics = PerformanceMetrics(
            name="test",
            execution_time_ms=100.5,
            memory_before_mb=50.0,
            memory_after_mb=55.0,
            memory_delta_mb=5.0,
        )

        d = metrics.to_dict()
        assert d["name"] == "test"
        assert d["execution_time_ms"] == 100.5

    def test_measure_performance_context(self):
        """Test performance measurement context manager."""
        from jarvis_core.utils.performance import measure_performance

        with measure_performance("test_op") as metrics:
            time.sleep(0.01)  # 10ms

        assert metrics.execution_time_ms >= 10
        assert metrics.name == "test_op"

    def test_timed_decorator(self):
        """Test timed decorator."""
        from jarvis_core.utils.performance import timed

        @timed
        def slow_function():
            time.sleep(0.01)
            return "done"

        result = slow_function()
        assert result == "done"

    def test_memoize_decorator(self):
        """Test memoization decorator."""
        from jarvis_core.utils.performance import memoize

        call_count = 0

        @memoize(maxsize=10)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call (cached)
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Not called again

    def test_batch_processor(self):
        """Test batch processing."""
        from jarvis_core.utils.performance import BatchProcessor

        processor = BatchProcessor(batch_size=3)
        items = list(range(10))

        def double_batch(batch):
            return [x * 2 for x in batch]

        results = processor.process(items, double_batch)

        assert len(results) == 10
        assert results[0] == 0
        assert results[5] == 10

    def test_lazy_loader(self):
        """Test lazy loading."""
        from jarvis_core.utils.performance import LazyLoader

        load_count = 0

        def loader():
            nonlocal load_count
            load_count += 1
            return "expensive_resource"

        lazy = LazyLoader(loader)

        assert not lazy.is_loaded()
        assert load_count == 0

        # Access triggers load
        value = lazy.value
        assert value == "expensive_resource"
        assert lazy.is_loaded()
        assert load_count == 1

        # Second access doesn't reload
        value2 = lazy.value
        assert load_count == 1

    def test_memory_manager(self):
        """Test memory manager."""
        from jarvis_core.utils.performance import LazyLoader, MemoryManager

        manager = MemoryManager(threshold_mb=1000)

        lazy = LazyLoader(lambda: "resource")
        manager.register(lazy)

        _ = lazy.value  # Load it

        status = manager.status()
        assert status["registered_resources"] == 1
        assert status["loaded_resources"] == 1

    def test_response_cache(self):
        """Test response cache."""
        from jarvis_core.utils.performance import ResponseCache

        cache = ResponseCache(max_size=100, default_ttl=60)

        cache.set("key1", {"data": "value1"})
        result = cache.get("key1")

        assert result == {"data": "value1"}

        # Missing key
        assert cache.get("nonexistent") is None

    def test_response_cache_ttl(self):
        """Test cache TTL expiration."""
        from jarvis_core.utils.performance import ResponseCache

        cache = ResponseCache(max_size=100, default_ttl=1)

        # Set with very short TTL
        cache.set("key", "value", ttl=1)

        # Should still exist immediately
        assert cache.get("key") == "value"

        # After TTL, should be gone
        time.sleep(1.1)
        assert cache.get("key") is None

    def test_global_managers(self):
        """Test global manager access."""
        from jarvis_core.utils.performance import (
            get_memory_manager,
            get_response_cache,
        )

        manager1 = get_memory_manager()
        manager2 = get_memory_manager()
        assert manager1 is manager2

        cache1 = get_response_cache()
        cache2 = get_response_cache()
        assert cache1 is cache2


class TestDocumentationFiles:
    """Tests for documentation files existence."""

    def test_api_reference_exists(self):
        """Test API reference exists."""
        from pathlib import Path

        api_ref = Path("docs/API_REFERENCE.md")
        assert api_ref.exists()

        content = api_ref.read_text(encoding="utf-8")
        assert "JARVIS" in content
        assert "API" in content

    def test_quickstart_exists(self):
        """Test quickstart guide exists."""
        from pathlib import Path

        quickstart = Path("docs/QUICKSTART.md")
        assert quickstart.exists()

        content = quickstart.read_text(encoding="utf-8")
        assert "インストール" in content or "install" in content.lower()


class TestDistributionFiles:
    """Tests for distribution configuration."""

    def test_dockerfile_exists(self):
        """Test Dockerfile exists."""
        from pathlib import Path

        dockerfile = Path("Dockerfile")
        assert dockerfile.exists()

        content = dockerfile.read_text(encoding="utf-8")
        assert "FROM python" in content

    def test_pyproject_has_optional_deps(self):
        """Test pyproject.toml has optional dependencies."""
        from pathlib import Path

        pyproject = Path("pyproject.toml")
        assert pyproject.exists()

        content = pyproject.read_text(encoding="utf-8")
        assert "[project.optional-dependencies]" in content
        assert "embedding" in content or "llm" in content


class TestPhase3Complete:
    """Integration tests for Phase 3 completion."""

    def test_all_phase3_modules(self):
        """Test all Phase 3 modules import."""
        # Plugins
        from jarvis_core.plugins.plugin_system import Plugin
        from jarvis_core.plugins.zotero_integration import ZoteroClient

        # Performance
        from jarvis_core.utils.performance import measure_performance

        assert Plugin is not None
        assert ZoteroClient is not None
        assert measure_performance is not None
