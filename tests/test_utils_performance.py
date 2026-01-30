"""Tests for utils.performance module."""

import time

from jarvis_core.utils.performance import (
    PerformanceMetrics,
    get_memory_usage_mb,
    measure_performance,
    timed,
    memoize,
    BatchProcessor,
    LazyLoader,
    MemoryManager,
    ResponseCache,
)


class TestPerformanceMetrics:
    def test_creation(self):
        metrics = PerformanceMetrics(
            name="test",
            execution_time_ms=100.5,
            memory_before_mb=50.0,
            memory_after_mb=55.0,
            memory_delta_mb=5.0,
        )

        assert metrics.name == "test"
        assert metrics.execution_time_ms == 100.5

    def test_to_dict(self):
        metrics = PerformanceMetrics(
            name="test",
            execution_time_ms=100.0,
            memory_before_mb=50.0,
            memory_after_mb=55.0,
            memory_delta_mb=5.0,
        )

        d = metrics.to_dict()

        assert d["name"] == "test"
        assert "execution_time_ms" in d


class TestGetMemoryUsageMb:
    def test_returns_float(self):
        result = get_memory_usage_mb()
        assert isinstance(result, float)
        assert result >= 0


class TestMeasurePerformance:
    def test_context_manager_returns_metrics(self):
        with measure_performance("test_op") as metrics_holder:
            time.sleep(0.01)  # Do some work

        # Metrics should be populated after exiting
        assert metrics_holder is not None


class TestTimed:
    def test_decorator_works(self):
        @timed
        def sample_func():
            return "result"

        result = sample_func()
        assert result == "result"


class TestMemoize:
    def test_caches_results(self):
        call_count = 0

        @memoize(maxsize=10)
        def expensive_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        assert expensive_func(5) == 10
        assert call_count == 1

        # Second call with same arg - should use cache
        assert expensive_func(5) == 10
        assert call_count == 1


class TestBatchProcessor:
    def test_process_batches(self):
        processor = BatchProcessor(batch_size=2)
        items = [1, 2, 3, 4, 5]

        def double_batch(batch):
            return [x * 2 for x in batch]

        results = processor.process(items, double_batch)

        assert results == [2, 4, 6, 8, 10]

    def test_empty_items(self):
        processor = BatchProcessor(batch_size=10)
        results = processor.process([], lambda x: x)
        assert results == []


class TestLazyLoader:
    def test_lazy_loading(self):
        load_count = 0

        def loader():
            nonlocal load_count
            load_count += 1
            return "loaded_value"

        lazy = LazyLoader(loader)

        # is_loaded is a method, not property
        assert lazy.is_loaded() is False
        assert load_count == 0

        # Access value triggers load
        value = lazy.value
        assert value == "loaded_value"
        assert lazy.is_loaded() is True
        assert load_count == 1

        # Second access doesn't reload
        _ = lazy.value
        assert load_count == 1

    def test_unload(self):
        lazy = LazyLoader(lambda: "value")

        _ = lazy.value
        assert lazy.is_loaded() is True

        lazy.unload()
        assert lazy.is_loaded() is False


class TestMemoryManager:
    def test_register_and_cleanup(self):
        manager = MemoryManager(threshold_mb=10000)

        loader = LazyLoader(lambda: "value")
        manager.register(loader)

        _ = loader.value  # Load the value

        # Force cleanup
        unloaded = manager.cleanup(force=True)
        assert unloaded >= 0

    def test_check_memory(self):
        manager = MemoryManager(threshold_mb=100000)
        result = manager.check_memory()
        assert isinstance(result, bool)

    def test_status(self):
        manager = MemoryManager()
        status = manager.status()

        assert "current_mb" in status
        assert "threshold_mb" in status


class TestResponseCache:
    def test_set_and_get(self):
        cache = ResponseCache(max_size=100)

        cache.set("key1", "value1")
        result = cache.get("key1")

        assert result == "value1"

    def test_get_missing(self):
        cache = ResponseCache()
        result = cache.get("nonexistent")
        assert result is None

    def test_ttl_expiry(self):
        cache = ResponseCache(default_ttl=0)  # Immediate expiry

        cache.set("key", "value")
        time.sleep(0.01)
        result = cache.get("key")

        assert result is None

    def test_clear(self):
        cache = ResponseCache()
        cache.set("k1", "v1")
        cache.set("k2", "v2")

        cache.clear()

        assert cache.get("k1") is None
        assert cache.get("k2") is None

    def test_stats(self):
        cache = ResponseCache()
        cache.set("k1", "v1")
        cache.get("k1")  # Hit
        cache.get("k2")  # Miss

        stats = cache.stats()

        assert "size" in stats
        assert "max_size" in stats