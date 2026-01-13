"""Tests for contradiction massive - FIXED."""

import pytest


class TestContradictionBasic:
    def test_import(self):
        from jarvis_core.analysis.contradiction import ContradictionDetector
        assert ContradictionDetector is not None
    
    def test_create(self):
        from jarvis_core.analysis.contradiction import ContradictionDetector
        d = ContradictionDetector()
        assert d is not None


class TestModule:
    def test_module(self):
        from jarvis_core.analysis import contradiction
        assert contradiction is not None
