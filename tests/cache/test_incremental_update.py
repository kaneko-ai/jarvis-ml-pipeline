from jarvis_core.cache.pipeline_cache import PipelineCache

def test_pipeline_cache_hit_miss(tmp_path):
    cache = PipelineCache(tmp_path)
    
    call_count = 0
    def expensive_op():
        nonlocal call_count
        call_count += 1
        return {"data": "result"}
    
    key = "test_key_1"
    
    # First call: Miss -> Compute
    res1 = cache.get_or_compute(key, expensive_op)
    assert res1["data"] == "result"
    assert call_count == 1
    
    # Second call: Hit -> No Compute
    res2 = cache.get_or_compute(key, expensive_op)
    assert res2["data"] == "result"
    assert call_count == 1

def test_file_hash_integration(tmp_path):
    cache = PipelineCache(tmp_path)
    
    # Create a dummy file
    f = tmp_path / "data.txt"
    f.write_text("v1")
    
    # Compute hash v1
    hash1 = cache.calculate_file_hash(f)
    key1 = cache.generate_key("process", hash1)
    
    cache.get_or_compute(key1, lambda: "processed_v1")
    
    # Modify file
    f.write_text("v2")
    hash2 = cache.calculate_file_hash(f)
    key2 = cache.generate_key("process", hash2)
    
    assert hash1 != hash2
    assert key1 != key2
    
    # Should be a miss for new key
    res = cache.get_or_compute(key2, lambda: "processed_v2")
    assert res == "processed_v2"
    
    # Old key still retrievable if needed
    assert cache.kv.get(key1) == "processed_v1"
