"""Failure Taxonomy.

Per PR-93, classifies failures for analysis.
"""
from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List


class FailureCategory(Enum):
    """Categories of failures."""

    # Retrieval issues
    RETRIEVAL_EMPTY = "retrieval_empty"  # No results returned
    RETRIEVAL_IRRELEVANT = "retrieval_irrelevant"  # Results not relevant
    RETRIEVAL_TIMEOUT = "retrieval_timeout"  # Retrieval timed out

    # Extraction issues
    EXTRACT_PDF_FAIL = "extract_pdf_fail"  # PDF extraction failed
    EXTRACT_EMPTY = "extract_empty"  # Extraction returned empty
    EXTRACT_CORRUPTED = "extract_corrupted"  # Extracted text corrupted

    # Citation issues
    CITATION_MISSING = "citation_missing"  # Claim without citation
    CITATION_INVALID = "citation_invalid"  # Citation doesn't support claim
    CITATION_ORPHAN = "citation_orphan"  # Citation without matching source

    # Generation issues
    GENERATE_HALLUCINATION = "generate_hallucination"  # Unsupported claim
    GENERATE_CONTRADICTION = "generate_contradiction"  # Self-contradictory
    GENERATE_INCOMPLETE = "generate_incomplete"  # Partial answer

    # System issues
    SYSTEM_TIMEOUT = "system_timeout"  # Overall timeout
    SYSTEM_BUDGET = "system_budget"  # Budget exceeded
    SYSTEM_ERROR = "system_error"  # Internal error

    # Network issues
    NETWORK_TIMEOUT = "network_timeout"
    NETWORK_REFUSED = "network_refused"
    NETWORK_DNS = "network_dns"

    # Unknown
    UNKNOWN = "unknown"


@dataclass
class ClassifiedFailure:
    """A classified failure instance."""

    category: FailureCategory
    message: str
    step_id: Optional[int] = None
    tool: Optional[str] = None
    recoverable: bool = False
    suggestion: str = ""


def classify_exception(exc: Exception) -> FailureCategory:
    """Classify an exception into a failure category."""
    exc_name = type(exc).__name__.lower()
    exc_msg = str(exc).lower()

    # Timeout
    if "timeout" in exc_name or "timeout" in exc_msg:
        if "network" in exc_msg or "connection" in exc_msg:
            return FailureCategory.NETWORK_TIMEOUT
        return FailureCategory.SYSTEM_TIMEOUT

    # Network
    if "connection" in exc_name or "refused" in exc_msg:
        return FailureCategory.NETWORK_REFUSED
    if "dns" in exc_msg or "resolve" in exc_msg:
        return FailureCategory.NETWORK_DNS

    # PDF
    if "pdf" in exc_msg or "fitz" in exc_msg:
        return FailureCategory.EXTRACT_PDF_FAIL

    # Budget
    if "budget" in exc_msg or "limit" in exc_msg:
        return FailureCategory.SYSTEM_BUDGET

    return FailureCategory.UNKNOWN


def classify_eval_failure(failure: dict) -> ClassifiedFailure:
    """Classify an evaluation failure."""
    gate = failure.get("gate", "")
    reason = failure.get("reason", "")

    if "citation" in gate.lower():
        if "missing" in reason.lower():
            return ClassifiedFailure(
                category=FailureCategory.CITATION_MISSING,
                message=reason,
                suggestion="Add citations to unsupported claims",
            )
        return ClassifiedFailure(
            category=FailureCategory.CITATION_INVALID,
            message=reason,
            suggestion="Verify citation-claim alignment",
        )

    if "entity" in gate.lower() or "coverage" in gate.lower():
        return ClassifiedFailure(
            category=FailureCategory.RETRIEVAL_IRRELEVANT,
            message=reason,
            suggestion="Improve retrieval query or expand sources",
        )

    if "hallucination" in gate.lower():
        return ClassifiedFailure(
            category=FailureCategory.GENERATE_HALLUCINATION,
            message=reason,
            suggestion="Strengthen evidence requirements",
        )

    return ClassifiedFailure(
        category=FailureCategory.UNKNOWN,
        message=reason,
    )


def get_failure_summary(failures: List[ClassifiedFailure]) -> dict:
    """Summarize failures by category."""
    summary = {}
    for f in failures:
        cat = f.category.value
        if cat not in summary:
            summary[cat] = {"count": 0, "examples": []}
        summary[cat]["count"] += 1
        if len(summary[cat]["examples"]) < 3:
            summary[cat]["examples"].append(f.message[:50])
    return summary
