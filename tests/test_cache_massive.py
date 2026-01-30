"""Tests for cache massive - FIXED."""

import pytest


@pytest.mark.slow
class TestCacheBasic:
    def test_import(self):
        from jarvis_core.cache import multi_level

        assert multi_level is not None


class TestModule:
    def test_cache_module(self):
        from jarvis_core import cache

        assert cache is not None
