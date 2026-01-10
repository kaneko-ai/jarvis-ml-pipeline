"""Tests for truth.confidence module."""

from jarvis_core.truth.confidence import (
    ConfidenceLevel,
    CONFIDENCE_LEVELS,
    get_confidence_level,
    calibrate_confidence,
    _get_calibration_note,
    format_confidence_for_display,
    ConfidenceRegistry,
)


class TestConfidenceLevel:
    def test_levels_defined(self):
        assert len(CONFIDENCE_LEVELS) == 5
        assert all(isinstance(lvl, ConfidenceLevel) for lvl in CONFIDENCE_LEVELS)


class TestGetConfidenceLevel:
    def test_very_high(self):
        level = get_confidence_level(0.95)
        assert level.level == "very_high"

    def test_high(self):
        level = get_confidence_level(0.8)
        assert level.level == "high"

    def test_medium(self):
        level = get_confidence_level(0.6)
        assert level.level == "medium"

    def test_low(self):
        level = get_confidence_level(0.4)
        assert level.level == "low"

    def test_very_low(self):
        level = get_confidence_level(0.1)
        assert level.level == "very_low"


class TestCalibrateConfidence:
    def test_calibrate_basic(self):
        result = calibrate_confidence(0.8, "test_module", evidence_count=2)
        
        assert "value" in result
        assert "level" in result
        assert "description" in result
        assert result["evidence_count"] == 2

    def test_calibrate_caps_without_evidence(self):
        result = calibrate_confidence(0.9, evidence_count=0)
        
        # Without evidence, capped at 0.4
        assert result["value"] <= 0.4

    def test_calibrate_caps_single_evidence(self):
        result = calibrate_confidence(0.9, evidence_count=1)
        
        # With single evidence, capped at 0.7
        assert result["value"] <= 0.7

    def test_calibrate_multiple_evidence(self):
        result = calibrate_confidence(0.9, evidence_count=3)
        
        # Multiple evidences allow full confidence
        assert result["value"] == 0.9

    def test_calibrate_clamps_to_range(self):
        result = calibrate_confidence(1.5, evidence_count=5)
        assert result["value"] <= 1.0
        
        result = calibrate_confidence(-0.5, evidence_count=5)
        assert result["value"] >= 0.0


class TestGetCalibrationNote:
    def test_no_evidence(self):
        note = _get_calibration_note(0.5, 0)
        assert "推定" in note or "根拠なし" in note

    def test_single_evidence(self):
        note = _get_calibration_note(0.5, 1)
        assert "単一" in note or "追加確認" in note

    def test_high_confidence(self):
        note = _get_calibration_note(0.85, 3)
        assert "高い" in note

    def test_standard_confidence(self):
        note = _get_calibration_note(0.5, 2)
        assert "標準" in note


class TestFormatConfidenceForDisplay:
    def test_format_high(self):
        result = format_confidence_for_display(0.85)
        assert "85%" in result
        assert "high" in result

    def test_format_low(self):
        result = format_confidence_for_display(0.35)
        assert "35%" in result
        assert "low" in result


class TestConfidenceRegistry:
    def test_register_and_get(self):
        ConfidenceRegistry.register("test_module", 0.65)
        baseline = ConfidenceRegistry.get_baseline("test_module")
        
        assert baseline == 0.65

    def test_get_default(self):
        baseline = ConfidenceRegistry.get_baseline("unknown_module")
        assert baseline == 0.5

    def test_default_baselines_registered(self):
        # Check default baselines exist
        assert ConfidenceRegistry.get_baseline("gap_analysis") == 0.5
        assert ConfidenceRegistry.get_baseline("hypothesis") == 0.4
        assert ConfidenceRegistry.get_baseline("fact_extraction") == 0.7
