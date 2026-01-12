"""Tests for cache module - Coverage improvement (FIXED)."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os


class TestCacheLevel:
    """Tests for CacheLevel enum."""

    def test_cache_level_values(self):
        """Test CacheLevel enum values."""
        from jarvis_core.cache.multi_level import CacheLevel

        assert CacheLevel.L1_MEMORY.value == "l1_memory"
        assert CacheLevel.L2_DISK.value == "l2_disk"
        assert CacheLevel.MISS.value == "miss"


class TestCacheStats:
    """Tests for CacheStats dataclass."""

    def test_cache_stats_creation(self):
        """Test CacheStats creation."""
        from jarvis_core.cache.multi_level import CacheStats

        stats = CacheStats()
        assert stats.l1_hits == 0
        assert stats.l2_hits == 0
        assert stats.misses == 0
        assert stats.writes == 0

    def test_hit_rate_zero(self):
        """Test hit rate with no operations."""
        from jarvis_core.cache.multi_level import CacheStats

        stats = CacheStats()
        assert stats.hit_rate() == 0.0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        from jarvis_core.cache.multi_level import CacheStats

        stats = CacheStats(l1_hits=5, l2_hits=3, misses=2)
        assert stats.hit_rate() == 0.8

    def test_to_dict(self):
        """Test to_dict method."""
        from jarvis_core.cache.multi_level import CacheStats

        stats = CacheStats(l1_hits=10, l2_hits=5, misses=5, writes=15)
        result = stats.to_dict()
        
        assert result["l1_hits"] == 10
        assert result["l2_hits"] == 5
        assert result["misses"] == 5
        assert result["writes"] == 15
        assert "hit_rate" in result


class TestMultiLevelCache:
    """Tests for MultiLevelCache class."""

    def test_cache_creation_no_l2(self):
        """Test cache creation without L2."""
        from jarvis_core.cache.multi_level import MultiLevelCache

        cache = MultiLevelCache()
        assert cache.l1_cache == {}
        assert cache.l2_path is None

    def test_cache_creation_with_l2(self):
        """Test cache creation with L2 path."""
        from jarvis_core.cache.multi_level import MultiLevelCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = MultiLevelCache(l2_path=tmpdir)
            assert cache.l2_path is not None

    def test_l1_put_and_get(self):
        """Test L1 cache put and get."""
        from jarvis_core.cache.multi_level import MultiLevelCache, CacheLevel

        cache = MultiLevelCache()
        cache.put("test_key", {"data": "value"}, write_l2=False)
        
        value, level = cache.get("test_key")
        assert value == {"data": "value"}
        assert level == CacheLevel.L1_MEMORY

    def test_cache_miss(self):
        """Test cache miss."""
        from jarvis_core.cache.multi_level import MultiLevelCache, CacheLevel

        cache = MultiLevelCache()
        value, level = cache.get("nonexistent")
        
        assert value is None
        assert level == CacheLevel.MISS

    def test_l2_cache(self):
        """Test L2 disk cache."""
        from jarvis_core.cache.multi_level import MultiLevelCache, CacheLevel

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write to cache
            cache1 = MultiLevelCache(l2_path=tmpdir)
            cache1.put("persistent_key", "persistent_value")
            
            # Create new cache instance to test L2 read
            cache2 = MultiLevelCache(l2_path=tmpdir)
            value, level = cache2.get("persistent_key")
            
            assert value == "persistent_value"
            assert level == CacheLevel.L2_DISK

    def test_invalidate(self):
        """Test cache invalidation."""
        from jarvis_core.cache.multi_level import MultiLevelCache, CacheLevel

        cache = MultiLevelCache()
        cache.put("key_to_delete", "value")
        cache.invalidate("key_to_delete")
        
        value, level = cache.get("key_to_delete")
        assert value is None
        assert level == CacheLevel.MISS

    def test_clear(self):
        """Test clearing all cache."""
        from jarvis_core.cache.multi_level import MultiLevelCache, CacheLevel

        cache = MultiLevelCache()
        cache.put("key1", "value1", write_l2=False)
        cache.put("key2", "value2", write_l2=False)
        cache.clear()
        
        value1, _ = cache.get("key1")
        value2, _ = cache.get("key2")
        assert value1 is None
        assert value2 is None

    def test_get_stats(self):
        """Test getting cache statistics."""
        from jarvis_core.cache.multi_level import MultiLevelCache

        cache = MultiLevelCache()
        cache.put("key", "value", write_l2=False)
        cache.get("key")
        cache.get("missing")
        
        stats = cache.get_stats()
        assert stats["writes"] == 1
        assert stats["l1_hits"] == 1
        assert stats["misses"] == 1

    def test_l1_eviction(self):
        """Test L1 cache eviction when full."""
        from jarvis_core.cache.multi_level import MultiLevelCache

        cache = MultiLevelCache(l1_max_size=3)
        cache.put("key1", "value1", write_l2=False)
        cache.put("key2", "value2", write_l2=False)
        cache.put("key3", "value3", write_l2=False)
        cache.put("key4", "value4", write_l2=False)
        
        # First key should be evicted
        assert "key1" not in cache.l1_cache


class TestModuleImports:
    """Test module imports."""

    def test_cache_imports(self):
        """Test cache module imports."""
        from jarvis_core.cache.multi_level import (
            MultiLevelCache,
            CacheLevel,
            CacheStats,
        )

        assert MultiLevelCache is not None
        assert CacheLevel is not None
        assert CacheStats is not None
