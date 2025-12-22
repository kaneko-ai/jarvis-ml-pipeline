"""Status Definitions.

Per RP-142, defines success/partial/fail status strictly.
"""
from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List


class RunStatus(Enum):
    """Run completion status.

    These are the ONLY valid statuses. All runs must end in one of these.
    """

    SUCCESS = "success"
    """All quality gates passed, complete output generated."""

    PARTIAL = "partial"
    """Some gates passed, usable output generated with limitations."""

    FAILED = "failed"
    """Fatal error, no usable output."""

    RUNNING = "running"
    """Run is still in progress (transient state)."""

    TIMEOUT = "timeout"
    """Run exceeded time budget (subtype of failed)."""

    BUDGET_EXCEEDED = "budget_exceeded"
    """Run exceeded resource budget (subtype of partial)."""


# Terminal statuses (run is complete)
TERMINAL_STATUSES = {RunStatus.SUCCESS, RunStatus.PARTIAL, RunStatus.FAILED, RunStatus.TIMEOUT}

# Successful outcomes (usable output)
SUCCESSFUL_STATUSES = {RunStatus.SUCCESS, RunStatus.PARTIAL, RunStatus.BUDGET_EXCEEDED}


@dataclass
class StatusReason:
    """Reason for a status."""

    status: RunStatus
    reason: str
    gate_failures: List[str]
    warnings: List[str]


def determine_status(
    fatal_error: bool = False,
    gate_results: Optional[dict] = None,
    timeout: bool = False,
    budget_exceeded: bool = False,
) -> StatusReason:
    """Determine run status from conditions.

    Args:
        fatal_error: Whether a fatal error occurred.
        gate_results: Dict of gate_name -> passed (bool).
        timeout: Whether timeout occurred.
        budget_exceeded: Whether budget was exceeded.

    Returns:
        StatusReason with status and explanation.
    """
    gate_results = gate_results or {}

    if fatal_error:
        return StatusReason(
            status=RunStatus.FAILED,
            reason="Fatal error during execution",
            gate_failures=[],
            warnings=[],
        )

    if timeout:
        return StatusReason(
            status=RunStatus.TIMEOUT,
            reason="Execution timed out",
            gate_failures=[],
            warnings=["Run did not complete within time budget"],
        )

    # Check gate failures
    failed_gates = [g for g, passed in gate_results.items() if not passed]

    if budget_exceeded:
        return StatusReason(
            status=RunStatus.BUDGET_EXCEEDED,
            reason="Resource budget exceeded, partial results available",
            gate_failures=failed_gates,
            warnings=["Budget limit reached before completion"],
        )

    if not failed_gates:
        return StatusReason(
            status=RunStatus.SUCCESS,
            reason="All quality gates passed",
            gate_failures=[],
            warnings=[],
        )

    # Some gates failed -> partial
    return StatusReason(
        status=RunStatus.PARTIAL,
        reason=f"{len(failed_gates)} quality gate(s) failed",
        gate_failures=failed_gates,
        warnings=[f"Failed gate: {g}" for g in failed_gates],
    )


def is_usable(status: RunStatus) -> bool:
    """Check if status indicates usable output."""
    return status in SUCCESSFUL_STATUSES


def is_terminal(status: RunStatus) -> bool:
    """Check if status is terminal (run complete)."""
    return status in TERMINAL_STATUSES
