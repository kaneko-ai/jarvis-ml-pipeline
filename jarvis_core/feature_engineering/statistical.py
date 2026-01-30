"""Statistical Feature Extraction (Phase 2-ΩΩ P2).

Extracts features related to statistical strength and study design quality
to improve ranking of evidence.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def extract_sample_size(text: str) -> int | None:
    """Extract sample size (N) from text.

    Args:
        text: Abstract or full text

    Returns:
        Extracted sample size or None
    """
    # Patterns for finding N
    patterns = [
        r"n\s*=\s*(\d+)",
        r"sample size of (\d+)",
        r"(\d+) patients",
        r"(\d+) participants",
        r"(\d+) cases",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Return largest number found (heuristic)
            try:
                nums = [int(m) for m in matches]
                return max(nums)
            except ValueError:
                continue

    return None


def extract_p_value(text: str) -> float | None:
    """Extract smallest p-value mentioned.

    Args:
        text: Abstract or full text

    Returns:
        Smallest p-value or None
    """
    # Patterns for p-values
    # p < 0.05, p=0.001, etc.
    pattern = r"p\s*[<>=]\s*([0]\.\d+|0\.\d+e-\d+)"

    matches = re.findall(pattern, text, re.IGNORECASE)
    if matches:
        try:
            p_values = [float(m) for m in matches]
            return min(p_values)
        except ValueError as e:
            logger.debug(f"Failed to parse p-values: {e}")

    return None


def detect_study_design(text: str) -> str:
    """Detect study design type.

    Args:
        text: Abstract or full text

    Returns:
        Design type (rct, cohort, case_control, preclinical, review, unknown)
    """
    text_lower = text.lower()

    if "meta-analysis" in text_lower or "systematic review" in text_lower:
        return "meta_analysis"

    if "randomized" in text_lower and "trial" in text_lower:
        return "rct"

    if "cohort" in text_lower or "longitudinal" in text_lower:
        return "cohort"

    if "case-control" in text_lower or "retrospective" in text_lower:
        return "case_control"

    if "in vivo" in text_lower or "mice" in text_lower or "xenograft" in text_lower:
        return "preclinical"

    if "review" in text_lower:
        return "review"

    return "unknown"


def extract_statistical_features(paper: dict[str, Any]) -> dict[str, float]:
    """Extract statistical features from paper.

    Args:
        paper: Paper dictionary with 'abstract' or 'full_text'

    Returns:
        Dict of features (normalized 0-1 where possible or raw values)
    """
    text = paper.get("abstract", "")
    if not text:
        return {
            "has_stats": 0.0,
            "log_sample_size": 0.0,
            "statistical_significance": 0.0,
            "study_design_score": 0.0,
        }

    # 1. Sample Size
    n = extract_sample_size(text)
    import math

    # Log transform N (cap at N=1000 -> 3.0)
    log_n = math.log10(n) if n and n > 0 else 0.0
    log_n = min(log_n, 4.0) / 4.0  # Normalize to 0-1 range (assuming max N=10000)

    # 2. P-value
    p = extract_p_value(text)
    # Score: 1.0 for p<0.001, 0.8 for p<0.01, 0.5 for p<0.05, 0.0 otherwise
    if p is not None:
        if p < 0.001:
            sig_score = 1.0
        elif p < 0.01:
            sig_score = 0.8
        elif p < 0.05:
            sig_score = 0.5
        else:
            sig_score = 0.2
    else:
        sig_score = 0.0

    # 3. Study Design
    design = detect_study_design(text)
    # Hierarchy of evidence
    design_scores = {
        "meta_analysis": 1.0,
        "rct": 0.9,
        "cohort": 0.7,
        "case_control": 0.5,
        "preclinical": 0.4,
        "review": 0.3,
        "unknown": 0.2,
    }
    design_score = design_scores.get(design, 0.2)

    return {
        "has_stats": 1.0 if (n is not None or p is not None) else 0.0,
        "log_sample_size": log_n,
        "statistical_significance": sig_score,
        "study_design_score": design_score,
    }