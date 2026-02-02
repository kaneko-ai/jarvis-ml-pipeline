from unittest.mock import MagicMock, patch
import numpy as np
from jarvis_core.embeddings.model import DeterministicEmbeddingModel


def test_input_normalization():
    model = DeterministicEmbeddingModel(use_cache=False)

    t1 = "Hello   World"
    t2 = "Hello World"
    t3 = "Hello\nWorld"

    # Normalization should make t1 and t2 identical, but t3 might differ depending on regex
    # Our regex replaces all whitespace sequences with single space

    # Internal normalization check
    assert model._normalize_text(t1) == "Hello World"
    assert model._normalize_text(t2) == "Hello World"
    assert model._normalize_text(t3) == "Hello World"

    # Embeddings should be identical
    v1 = model.embed(t1)
    v2 = model.embed(t2)
    v3 = model.embed(t3)

    assert np.allclose(v1, v2)
    assert np.allclose(v1, v3)


def test_caching_mechanism(tmp_path):
    cache_dir = tmp_path / "cache"
    model = DeterministicEmbeddingModel(cache_dir=cache_dir, use_cache=True)

    text = "Unique text for caching test"

    # First call: Compute
    v1 = model.embed(text)

    # Verify cache file created
    assert (cache_dir / f"embed_{model._sanitize_name(model.model_name)}.db").exists()

    # Second call: Should hit cache
    # We can't easily mock the internal call without patching, but we can verify consistency
    v2 = model.embed(text)

    assert np.allclose(v1, v2)

    # Manually inspect cache
    key = model._cache.generate_key(model._normalize_text(text), model.model_name)
    cached_val = model._cache.get(key)
    assert cached_val is not None
    assert np.allclose(v1[0], np.array(cached_val, dtype=np.float32))


def test_unicode_normalization():
    model = DeterministicEmbeddingModel(use_cache=False)

    # NFKC should normalize compatible characters
    t1 = "café"
    t2 = "cafe\u0301"  # cafe + combining acute accent

    assert model._normalize_text(t1) == model._normalize_text(t2)

    v1 = model.embed(t1)
    v2 = model.embed(t2)

    assert np.allclose(v1, v2)
