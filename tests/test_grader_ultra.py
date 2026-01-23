"""Tests for grader ultra - FIXED."""

import pytest


@pytest.mark.slow
class TestGraderBasic:
    def test_import(self):
        import jarvis_core.grader
        assert jarvis_core.grader is not None


class TestModule:
    def test_grader_module(self):
        import jarvis_core.grader
        assert jarvis_core.grader is not None
