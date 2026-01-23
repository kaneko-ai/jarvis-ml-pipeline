"""Golden Path Test for Cache and Store (PR-3)."""
import time
from pathlib import Path
import pytest
from jarvis_core.cache.sqlite_cache import SQLiteCache

@pytest.fixture
def cache(tmp_path):
    db_path = tmp_path / "test_cache.db"
    c = SQLiteCache(db_path=db_path, max_size_mb=1)
    yield c
    c.close()

def test_cache_basic_ops(cache):
    cache.set("key1", {"data": "value1"}, namespace="test")
    val = cache.get("key1", namespace="test")
    assert val == {"data": "value1"}
    
    cache.delete("key1", namespace="test")
    assert cache.get("key1", namespace="test") is None

def test_cache_ttl(cache):
    cache.set("short_lived", "data", ttl_seconds=1)
    assert cache.get("short_lived") == "data"
    
    time.sleep(1.1)
    assert cache.get("short_lived") is None

def test_cache_clear(cache):
    cache.set("k1", "v1", namespace="ns1")
    cache.set("k2", "v2", namespace="ns2")
    
    cache.clear(namespace="ns1")
    assert cache.get("k1", namespace="ns1") is None
    assert cache.get("k2", namespace="ns2") == "v2"
    
    cache.clear()
    assert cache.get("k2", namespace="ns2") is None

def test_cache_eviction(tmp_path):
    # Small cache to force eviction
    db_path = tmp_path / "evict.db"
    # 0.001 MB is about 1KB
    cache = SQLiteCache(db_path=db_path, max_size_mb=1)
    
    # Fill cache
    large_data = "x" * 1024 * 100 # 100KB
    for i in range(15): # Should exceed 1MB (80% target after eviction)
        cache.set(f"key_{i}", large_data)
        
    stats = cache.stats()
    assert stats["entries"] < 15 # Some should be evicted
    assert stats["size_bytes"] <= cache.max_size_bytes

def test_cache_stats(cache):
    cache.set("s1", "v1")
    stats = cache.stats()
    assert stats["entries"] == 1
    assert stats["size_bytes"] > 0
    assert "db_path" in stats

def test_cache_serialization(cache):
    # Test non-JSON serializable
    class Unserializable:
        def __str__(self): return "unserializable"
        
    obj = Unserializable()
    cache.set("unserializable", obj)
    val = cache.get("unserializable")
    assert val == "unserializable"
