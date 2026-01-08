"""Evidence Locator Verification (Phase 2-ΩΩ).

Verifies that evidence locators point to actual text in source documents
and that quoted spans match the extracted content.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def levenshtein_ratio(s1: str, s2: str) -> float:
    """Calculate Levenshtein similarity ratio (0-1).

    Simple implementation for quote matching.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Similarity ratio (1.0 = identical)
    """
    # Normalize
    s1 = s1.lower().strip()
    s2 = s2.lower().strip()

    if s1 == s2:
        return 1.0

    # Calculate Levenshtein distance
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    # Dynamic programming matrix
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,  # deletion
                dp[i][j - 1] + 1,  # insertion
                dp[i - 1][j - 1] + cost,  # substitution
            )

    distance = dp[len1][len2]
    max_len = max(len1, len2)

    return 1.0 - (distance / max_len)


def extract_text_from_pdf(
    pdf_path: Path, page: int, paragraph: int = None, sentence: int = None
) -> str:
    """Extract text from specific location in PDF.

    NOTE: This is a placeholder. Real implementation would use pymupdf.

    Args:
        pdf_path: Path to PDF file
        page: Page number (1-indexed)
        paragraph: Paragraph number (optional)
        sentence: Sentence number (optional)

    Returns:
        Extracted text
    """
    # Placeholder: In production, use pymupdf to extract text
    logger.warning(f"PDF extraction not implemented. Would extract from {pdf_path} page {page}")
    return ""


def verify_locator(evidence: dict[str, Any], pdf_dir: Path) -> dict[str, Any]:
    """Verify evidence locator points to actual text.

    Args:
        evidence: Evidence dict with locator and quote_span
        pdf_dir: Directory containing PDFs

    Returns:
        Dict with 'valid', 'similarity', 'error'
    """
    locator = evidence.get("locator")
    quote_span = evidence.get("quote_span", "")
    paper_id = evidence.get("paper_id", "")

    if not locator:
        return {"valid": False, "similarity": 0.0, "error": "No locator provided"}

    if not quote_span:
        return {"valid": False, "similarity": 0.0, "error": "No quote_span provided"}

    # Find PDF file
    # In production, this would use paper_id to look up PDF path
    pdf_path = pdf_dir / f"{paper_id}.pdf"

    if not pdf_path.exists():
        return {"valid": False, "similarity": 0.0, "error": f"PDF not found: {pdf_path}"}

    # Extract text from locator
    try:
        extracted_text = extract_text_from_pdf(
            pdf_path,
            page=locator.get("page", 1),
            paragraph=locator.get("paragraph"),
            sentence=locator.get("sentence"),
        )
    except Exception as e:
        return {"valid": False, "similarity": 0.0, "error": f"Extraction failed: {str(e)}"}

    # Calculate similarity
    similarity = levenshtein_ratio(quote_span, extracted_text)

    # Threshold: 0.8
    valid = similarity >= 0.8

    return {
        "valid": valid,
        "similarity": similarity,
        "error": None if valid else f"Low similarity: {similarity:.2f}",
    }


def verify_all_evidence(
    evidence_list: list[dict], pdf_dir: Path, threshold: float = 0.8
) -> dict[str, Any]:
    """Verify all evidence locators.

    Args:
        evidence_list: List of evidence dicts
        pdf_dir: Directory containing PDFs
        threshold: Minimum similarity threshold

    Returns:
        Dict with 'valid_count', 'invalid_count', 'invalid_ids'
    """
    valid_count = 0
    invalid_count = 0
    invalid_ids = []

    for evidence in evidence_list:
        result = verify_locator(evidence, pdf_dir)

        if result["valid"]:
            valid_count += 1
        else:
            invalid_count += 1
            evidence_id = evidence.get("evidence_id", "unknown")
            invalid_ids.append(
                {
                    "evidence_id": evidence_id,
                    "error": result["error"],
                    "similarity": result["similarity"],
                }
            )

    return {
        "total": len(evidence_list),
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "validity_rate": valid_count / len(evidence_list) if evidence_list else 0.0,
        "invalid_ids": invalid_ids,
    }
