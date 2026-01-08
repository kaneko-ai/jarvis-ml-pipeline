"""FailureSignal.

Per RP-184, normalizes failures for repair logic input.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FailureCode(str, Enum):
    """Standard failure codes (single source of truth per RP-184)."""

    # Fetch/Extract
    FETCH_PDF_FAILED = "FETCH_PDF_FAILED"
    EXTRACT_PDF_FAILED = "EXTRACT_PDF_FAILED"
    FETCH_TIMEOUT = "FETCH_TIMEOUT"
    FETCH_RATE_LIMITED = "FETCH_RATE_LIMITED"

    # Citation/Claim
    CITATION_GATE_FAILED = "CITATION_GATE_FAILED"
    LOW_CLAIM_PRECISION = "LOW_CLAIM_PRECISION"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"

    # Budget/Resource
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    TIMEOUT = "TIMEOUT"

    # Model
    MODEL_ERROR = "MODEL_ERROR"
    JUDGE_TIMEOUT = "JUDGE_TIMEOUT"
    GENERATION_FAILED = "GENERATION_FAILED"

    # Entity/Retrieval
    ENTITY_MISS = "ENTITY_MISS"
    RETRIEVAL_EMPTY = "RETRIEVAL_EMPTY"

    # General
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    VALIDATION_FAILED = "VALIDATION_FAILED"


class FailureStage(str, Enum):
    """Stage where failure occurred."""

    FETCH = "fetch"
    EXTRACT = "extract"
    INDEX = "index"
    RETRIEVE = "retrieve"
    GENERATE = "generate"
    VALIDATE = "validate"
    JUDGE = "judge"
    UNKNOWN = "unknown"


@dataclass
class FailureSignal:
    """Normalized failure signal for repair logic.

    Attributes:
        code: Standardized failure code.
        message: Human-readable message.
        stage: Processing stage where failure occurred.
        metadata: Additional context (safe for logging).
    """

    code: FailureCode
    message: str
    stage: FailureStage
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "code": self.code.value if isinstance(self.code, FailureCode) else self.code,
            "message": self.message,
            "stage": self.stage.value if isinstance(self.stage, FailureStage) else self.stage,
            "metadata": self.metadata,
        }

    @classmethod
    def from_exception(cls, exc: Exception, stage: FailureStage = FailureStage.UNKNOWN) -> FailureSignal:
        """Create from exception."""
        exc_type = type(exc).__name__

        # Map exception types to failure codes
        code_map = {
            "TimeoutError": FailureCode.TIMEOUT,
            "BudgetExceeded": FailureCode.BUDGET_EXCEEDED,
            "ValueError": FailureCode.VALIDATION_FAILED,
            "FileNotFoundError": FailureCode.FETCH_PDF_FAILED,
        }

        code = code_map.get(exc_type, FailureCode.UNKNOWN_ERROR)

        return cls(
            code=code,
            message=str(exc)[:200],  # Truncate for safety
            stage=stage,
            metadata={"exception_type": exc_type},
        )

    @classmethod
    def from_result_error(cls, error_type: str, message: str, stage: str = "unknown") -> FailureSignal:
        """Create from Result error."""
        # Map error types to codes
        code_map = {
            "FetchError": FailureCode.FETCH_PDF_FAILED,
            "ExtractError": FailureCode.EXTRACT_PDF_FAILED,
            "CitationError": FailureCode.CITATION_GATE_FAILED,
            "ModelError": FailureCode.MODEL_ERROR,
            "BudgetError": FailureCode.BUDGET_EXCEEDED,
        }

        code = code_map.get(error_type, FailureCode.UNKNOWN_ERROR)

        stage_map = {
            "fetch": FailureStage.FETCH,
            "extract": FailureStage.EXTRACT,
            "retrieve": FailureStage.RETRIEVE,
            "generate": FailureStage.GENERATE,
            "validate": FailureStage.VALIDATE,
        }

        return cls(
            code=code,
            message=message[:200],
            stage=stage_map.get(stage, FailureStage.UNKNOWN),
        )


def extract_failure_signals(result: Any) -> list[FailureSignal]:
    """Extract failure signals from a Result object.

    Per RP-184, this provides signals for repair logic.

    Args:
        result: A Result object (from jarvis_core.runtime.result).

    Returns:
        List of FailureSignal objects.
    """
    signals = []

    # Check if result has error
    if hasattr(result, "error") and result.error:
        error = result.error
        signal = FailureSignal.from_result_error(
            error_type=getattr(error, "error_type", "Unknown"),
            message=getattr(error, "message", str(error)),
            stage=getattr(error, "stage", "unknown"),
        )
        signals.append(signal)

    # Check for quality gate failures
    if hasattr(result, "value") and result.value:
        value = result.value
        if hasattr(value, "gate_results"):
            for gate, passed in value.gate_results.items():
                if not passed:
                    if gate == "citation":
                        signals.append(FailureSignal(
                            code=FailureCode.CITATION_GATE_FAILED,
                            message="Citation gate not met",
                            stage=FailureStage.VALIDATE,
                        ))
                    elif gate == "entity":
                        signals.append(FailureSignal(
                            code=FailureCode.ENTITY_MISS,
                            message="Expected entities not found",
                            stage=FailureStage.RETRIEVE,
                        ))

    return signals
