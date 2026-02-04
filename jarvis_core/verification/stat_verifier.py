"""Statistical claim verification utilities."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class VerificationResult:
    is_valid: bool
    issues: list[str] = field(default_factory=list)
    recalculated_values: dict = field(default_factory=dict)


def verify_statistical_claim(claim: str, data: dict) -> VerificationResult:
    """Verify statistical claims against provided data.

    Args:
        claim: Claim text (used for keyword hints).
        data: Data dict containing p_value, effect_size, sample_size, mean_diff, std.

    Returns:
        VerificationResult with validation summary.
    """
    issues: list[str] = []
    recalculated: dict = {}

    p_value = data.get("p_value")
    effect_size = data.get("effect_size")
    sample_size = data.get("sample_size")
    ci_low = data.get("ci_low")
    ci_high = data.get("ci_high")

    # Range and basic sanity checks
    if p_value is not None:
        if not (0 <= p_value <= 1):
            issues.append("p_value_out_of_range")
        if p_value == 0:
            issues.append("p_value_implausibly_zero")
        if p_value == 1 and "significant" in claim.lower():
            issues.append("p_value_unity_with_significance_claim")

    if sample_size is not None:
        if sample_size <= 0:
            issues.append("invalid_sample_size")
        if sample_size < 10:
            issues.append("small_sample_size_red_flag")

    # Confidence Interval Consistency
    if ci_low is not None and ci_high is not None:
        if ci_low > ci_high:
            issues.append("invalid_ci_range")

        # If CI crosses the null hypothesis (e.g., 0 for difference, 1 for ratio)
        # but p_value is claimed to be < 0.05
        crosses_null = (ci_low <= 0 <= ci_high) or (ci_low <= 1 <= ci_high)
        if crosses_null and p_value is not None and p_value < 0.05:
            issues.append("ci_p_value_contradiction")

    # Effect size recalculation
    mean_diff = data.get("mean_diff")
    std = data.get("std")
    if mean_diff is not None and std:
        recalculated["effect_size"] = mean_diff / std
        if effect_size is not None and abs(effect_size - recalculated["effect_size"]) > 0.1:
            issues.append("effect_size_recalculation_mismatch")

    # Claim vs Value consistency
    claim_lower = claim.lower()
    if "significant" in claim_lower and p_value is not None and p_value > 0.05:
        issues.append("claim_significance_mismatch")

    if "not significant" in claim_lower and p_value is not None and p_value <= 0.05:
        issues.append("claim_insignificance_mismatch")

    return VerificationResult(
        is_valid=len(issues) == 0, issues=issues, recalculated_values=recalculated
    )
