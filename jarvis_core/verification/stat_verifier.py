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

    if p_value is not None and not (0 <= p_value <= 1):
        issues.append("p_value_out_of_range")

    if sample_size is not None and sample_size <= 0:
        issues.append("invalid_sample_size")

    mean_diff = data.get("mean_diff")
    std = data.get("std")
    if mean_diff is not None and std:
        recalculated["effect_size"] = mean_diff / std
        if effect_size is not None and abs(effect_size - recalculated["effect_size"]) > 0.2:
            issues.append("effect_size_mismatch")

    if "significant" in claim.lower() and p_value is not None and p_value > 0.05:
        issues.append("claim_significance_mismatch")

    return VerificationResult(is_valid=not issues, issues=issues, recalculated_values=recalculated)