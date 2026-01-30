"""Tests for telemetry.hashing module."""

from jarvis_core.telemetry.hashing import (
    normalize_text,
    prompt_hash,
    input_hash,
    compute_cache_key,
)


class TestNormalizeText:
    def test_lowercase(self):
        result = normalize_text("Hello WORLD")
        assert result == "hello world"

    def test_collapse_whitespace(self):
        result = normalize_text("hello   world\n\tfoo")
        assert result == "hello world foo"

    def test_strip_whitespace(self):
        result = normalize_text("  hello world  ")
        assert result == "hello world"


class TestPromptHash:
    def test_basic_hash(self):
        result = prompt_hash("Test prompt")

        assert len(result) == 16
        assert result.isalnum()

    def test_same_content_same_hash(self):
        hash1 = prompt_hash("Hello world")
        hash2 = prompt_hash("Hello world")

        assert hash1 == hash2

    def test_normalized_hashes_match(self):
        hash1 = prompt_hash("Hello   World")
        hash2 = prompt_hash("hello world")

        assert hash1 == hash2

    def test_no_normalize_different_hash(self):
        hash1 = prompt_hash("Hello World", normalize=True)
        hash2 = prompt_hash("Hello World", normalize=False)

        assert hash1 != hash2


class TestInputHash:
    def test_string_input(self):
        result = input_hash("test string")
        assert len(result) == 16

    def test_dict_input(self):
        result = input_hash({"key": "value"})
        assert len(result) == 16

    def test_list_input(self):
        result = input_hash(["a", "b", "c"])
        assert len(result) == 16

    def test_dict_deterministic(self):
        hash1 = input_hash({"b": 2, "a": 1})
        hash2 = input_hash({"a": 1, "b": 2})

        # Sorted keys make it deterministic
        assert hash1 == hash2

    def test_other_type(self):
        result = input_hash(12345)
        assert len(result) == 16


class TestComputeCacheKey:
    def test_basic_cache_key(self):
        result = compute_cache_key("search", {"query": "test"})

        assert len(result) == 24
        assert result.isalnum()

    def test_same_inputs_same_key(self):
        key1 = compute_cache_key("search", {"query": "test"}, version="1.0")
        key2 = compute_cache_key("search", {"query": "test"}, version="1.0")

        assert key1 == key2

    def test_different_tool_different_key(self):
        key1 = compute_cache_key("tool_a", {"query": "test"})
        key2 = compute_cache_key("tool_b", {"query": "test"})

        assert key1 != key2

    def test_different_version_different_key(self):
        key1 = compute_cache_key("search", {"q": "x"}, version="1.0")
        key2 = compute_cache_key("search", {"q": "x"}, version="2.0")

        assert key1 != key2
