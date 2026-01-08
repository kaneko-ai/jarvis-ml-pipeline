"""Tests for FailureSignal normalization.

Per RP-184.
"""
import pytest

pytestmark = pytest.mark.core


class TestFailureSignalNormalization:
    """Tests for FailureSignal."""

    def test_failure_signal_creation(self):
        """Basic FailureSignal creation."""
        from jarvis_core.runtime.failure_signal import FailureCode, FailureSignal, FailureStage

        signal = FailureSignal(
            code=FailureCode.FETCH_PDF_FAILED,
            message="PDF not found",
            stage=FailureStage.FETCH,
        )

        assert signal.code == FailureCode.FETCH_PDF_FAILED
        assert signal.stage == FailureStage.FETCH

    def test_from_exception(self):
        """Create signal from exception."""
        from jarvis_core.runtime.failure_signal import FailureCode, FailureSignal, FailureStage

        exc = TimeoutError("Request timed out")
        signal = FailureSignal.from_exception(exc, FailureStage.FETCH)

        assert signal.code == FailureCode.TIMEOUT
        assert "timed out" in signal.message

    def test_to_dict(self):
        """Signal should serialize to dict."""
        from jarvis_core.runtime.failure_signal import FailureCode, FailureSignal, FailureStage

        signal = FailureSignal(
            code=FailureCode.MODEL_ERROR,
            message="API error",
            stage=FailureStage.GENERATE,
        )

        d = signal.to_dict()
        assert d["code"] == "MODEL_ERROR"
        assert d["stage"] == "generate"

    def test_standard_failure_codes(self):
        """All expected failure codes should exist."""
        from jarvis_core.runtime.failure_signal import FailureCode

        expected = [
            "FETCH_PDF_FAILED",
            "EXTRACT_PDF_FAILED",
            "CITATION_GATE_FAILED",
            "LOW_CLAIM_PRECISION",
            "BUDGET_EXCEEDED",
            "MODEL_ERROR",
        ]

        for code in expected:
            assert hasattr(FailureCode, code)
