"""Confidence Calibration Registry.

Per V4-T05, this standardizes confidence values across modules.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConfidenceLevel:
    """Definition of a confidence level."""

    level: str
    min_value: float
    max_value: float
    description: str


# Calibrated confidence levels
CONFIDENCE_LEVELS = [
    ConfidenceLevel("very_high", 0.9, 1.0, "高い確証、複数の強い根拠"),
    ConfidenceLevel("high", 0.7, 0.9, "確証あり、明確な根拠"),
    ConfidenceLevel("medium", 0.5, 0.7, "ある程度の確証、部分的な根拠"),
    ConfidenceLevel("low", 0.3, 0.5, "弱い確証、限定的な根拠"),
    ConfidenceLevel("very_low", 0.0, 0.3, "ほぼ推測、根拠薄弱"),
]


def get_confidence_level(value: float) -> ConfidenceLevel:
    """Get confidence level for a value."""
    for level in CONFIDENCE_LEVELS:
        if level.min_value <= value <= level.max_value:
            return level
    return CONFIDENCE_LEVELS[-1]


def calibrate_confidence(
    raw_confidence: float,
    source_module: str = "",
    evidence_count: int = 0,
) -> dict:
    """Calibrate confidence value.

    Args:
        raw_confidence: Raw confidence value 0-1.
        source_module: Source module for context.
        evidence_count: Number of supporting evidences.

    Returns:
        Calibrated confidence with metadata.
    """
    # Clamp to 0-1
    calibrated = max(0.0, min(1.0, raw_confidence))

    # Adjust based on evidence count
    if evidence_count == 0:
        calibrated = min(calibrated, 0.4)  # Cap without evidence
    elif evidence_count == 1:
        calibrated = min(calibrated, 0.7)  # Cap with single evidence
    # Multiple evidences allow higher confidence

    level = get_confidence_level(calibrated)

    return {
        "value": round(calibrated, 3),
        "level": level.level,
        "description": level.description,
        "raw": raw_confidence,
        "source": source_module,
        "evidence_count": evidence_count,
        "calibration_note": _get_calibration_note(calibrated, evidence_count),
    }


def _get_calibration_note(value: float, evidence_count: int) -> str:
    """Generate calibration note."""
    if evidence_count == 0:
        return "根拠なし、推定値として扱う"
    elif evidence_count == 1:
        return "単一根拠、追加確認推奨"
    elif value > 0.8:
        return "高い確信度、複数根拠あり"
    else:
        return "標準的な確信度"


def format_confidence_for_display(value: float) -> str:
    """Format confidence for human display."""
    level = get_confidence_level(value)
    return f"{value:.0%} ({level.level})"


class ConfidenceRegistry:
    """Registry for module-specific confidence calibrations."""

    _calibrations: dict[str, float] = {}

    @classmethod
    def register(cls, module: str, baseline: float) -> None:
        """Register baseline confidence for a module."""
        cls._calibrations[module] = baseline

    @classmethod
    def get_baseline(cls, module: str) -> float:
        """Get baseline confidence for a module."""
        return cls._calibrations.get(module, 0.5)


# Register default baselines
ConfidenceRegistry.register("gap_analysis", 0.5)
ConfidenceRegistry.register("hypothesis", 0.4)
ConfidenceRegistry.register("recommendation", 0.5)
ConfidenceRegistry.register("feasibility", 0.6)
ConfidenceRegistry.register("fact_extraction", 0.7)