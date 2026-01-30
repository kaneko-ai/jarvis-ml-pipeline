"""Tests for contradiction detector full - FIXED."""


class TestDetectorBasic:
    def test_import(self):
        from jarvis_core.contradiction.detector import ContradictionDetector

        assert ContradictionDetector is not None

    def test_create(self):
        from jarvis_core.contradiction.detector import ContradictionDetector

        d = ContradictionDetector()
        assert d is not None


class TestModule:
    def test_detector_module(self):
        from jarvis_core.contradiction import detector

        assert detector is not None
