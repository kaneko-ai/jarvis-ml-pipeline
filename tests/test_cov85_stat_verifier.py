from __future__ import annotations

from jarvis_core.verification.stat_verifier import verify_statistical_claim


def test_verify_statistical_claim_collects_all_major_issues() -> None:
    result = verify_statistical_claim(
        "This is significant",
        {
            "p_value": 1,
            "effect_size": 0.9,
            "sample_size": 5,
            "ci_low": -0.2,
            "ci_high": 0.3,
            "mean_diff": 1.0,
            "std": 2.0,
        },
    )

    assert result.is_valid is False
    assert "p_value_unity_with_significance_claim" in result.issues
    assert "small_sample_size_red_flag" in result.issues
    assert "claim_significance_mismatch" in result.issues
    assert "effect_size_recalculation_mismatch" in result.issues
    assert result.recalculated_values["effect_size"] == 0.5


def test_verify_statistical_claim_handles_invalid_ranges_and_not_significant() -> None:
    result = verify_statistical_claim(
        "Not significant in subgroup",
        {
            "p_value": 0,
            "sample_size": 0,
            "ci_low": 3,
            "ci_high": 2,
        },
    )

    assert result.is_valid is False
    assert "p_value_implausibly_zero" in result.issues
    assert "invalid_sample_size" in result.issues
    assert "invalid_ci_range" in result.issues
    assert "claim_insignificance_mismatch" in result.issues


def test_verify_statistical_claim_valid_case() -> None:
    result = verify_statistical_claim(
        "Significant benefit observed",
        {
            "p_value": 0.01,
            "effect_size": 0.5,
            "sample_size": 100,
            "ci_low": 0.2,
            "ci_high": 0.8,
            "mean_diff": 1.0,
            "std": 2.0,
        },
    )

    assert result.is_valid is True
    assert result.issues == []
    assert result.recalculated_values["effect_size"] == 0.5
