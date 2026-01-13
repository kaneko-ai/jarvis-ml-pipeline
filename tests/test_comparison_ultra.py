"""Tests for comparison ultra - FIXED."""

import pytest


class TestComparisonBasic:
    def test_import(self):
        from jarvis_core.analysis.comparison import ComparisonAnalyzer
        assert ComparisonAnalyzer is not None


class TestModule:
    def test_module(self):
        from jarvis_core.analysis import comparison
        assert comparison is not None
