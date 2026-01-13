"""Tests for contradiction detector coverage - FIXED."""

import pytest


class TestDetectorBasic:
    def test_import(self):
        from jarvis_core.contradiction.detector import ContradictionDetector
        assert ContradictionDetector is not None


class TestModule:
    def test_detector_module(self):
        from jarvis_core.contradiction import detector
        assert detector is not None
