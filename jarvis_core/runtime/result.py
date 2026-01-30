"""Result Type.

Per PR-95, provides unified result handling across all layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar

T = TypeVar("T")


class ResultStatus(Enum):
    """Result status."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class ErrorRecord:
    """A recorded error."""

    error_type: str
    message: str
    step_id: int | None = None
    tool: str | None = None
    recoverable: bool = False

    @classmethod
    def from_exception(cls, exc: Exception, **kwargs) -> ErrorRecord:
        return cls(
            error_type=type(exc).__name__,
            message=str(exc),
            **kwargs,
        )


@dataclass
class Result(Generic[T]):
    """A result that can be success, partial, or failed.

    This replaces raw exceptions with structured error handling.

    Usage:
        result = Result.success(data)
        result = Result.partial(data, warnings=["incomplete"])
        result = Result.fail(ErrorRecord(...))

        if result.is_success:
            use(result.value)
        else:
            handle(result.error)
    """

    status: ResultStatus
    value: T | None = None
    error: ErrorRecord | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        return self.status == ResultStatus.SUCCESS

    @property
    def is_partial(self) -> bool:
        return self.status == ResultStatus.PARTIAL

    @property
    def is_failed(self) -> bool:
        return self.status == ResultStatus.FAILED

    @classmethod
    def success(cls, value: T, warnings: list[str] | None = None) -> Result[T]:
        return cls(
            status=ResultStatus.SUCCESS,
            value=value,
            warnings=warnings or [],
        )

    @classmethod
    def partial(cls, value: T, warnings: list[str] | None = None) -> Result[T]:
        return cls(
            status=ResultStatus.PARTIAL,
            value=value,
            warnings=warnings or [],
        )

    @classmethod
    def fail(cls, error: ErrorRecord | Exception | str) -> Result[T]:
        if isinstance(error, ErrorRecord):
            err = error
        elif isinstance(error, Exception):
            err = ErrorRecord.from_exception(error)
        else:
            err = ErrorRecord(error_type="Error", message=str(error))

        return cls(
            status=ResultStatus.FAILED,
            error=err,
        )

    @classmethod
    def retry(cls, error: ErrorRecord) -> Result[T]:
        return cls(
            status=ResultStatus.RETRY,
            error=error,
        )

    def unwrap(self) -> T:
        """Get value or raise."""
        if self.value is not None:
            return self.value
        raise ValueError(f"Cannot unwrap failed result: {self.error}")

    def unwrap_or(self, default: T) -> T:
        """Get value or return default."""
        return self.value if self.value is not None else default