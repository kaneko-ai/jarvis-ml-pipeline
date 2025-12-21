"""Budget Manager.

Per V4-C10, this provides unified budget management for token/time/calls.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class BudgetExceeded(Exception):
    """Raised when budget is exceeded."""

    def __init__(self, resource: str, used: float, limit: float):
        self.resource = resource
        self.used = used
        self.limit = limit
        super().__init__(f"{resource} budget exceeded: {used}/{limit}")


@dataclass
class Budget:
    """Budget allocation."""

    max_tokens: int = 100000
    max_time_seconds: float = 300.0
    max_api_calls: int = 100
    max_chunks: int = 10000

    # Soft limits for warning
    warn_at_percent: float = 0.8

    def to_dict(self) -> dict:
        return {
            "max_tokens": self.max_tokens,
            "max_time_seconds": self.max_time_seconds,
            "max_api_calls": self.max_api_calls,
            "max_chunks": self.max_chunks,
            "warn_at_percent": self.warn_at_percent,
        }


class BudgetManager:
    """Manage budget during execution."""

    def __init__(self, budget: Budget = None):
        self.budget = budget or Budget()
        self.start_time = time.time()

        # Usage tracking
        self.tokens_used = 0
        self.api_calls = 0
        self.chunks_processed = 0

        # Warnings
        self.warnings: list = []

    def use_tokens(self, count: int) -> None:
        """Record token usage.

        Args:
            count: Number of tokens used.

        Raises:
            BudgetExceeded: If token budget exceeded.
        """
        self.tokens_used += count
        self._check_limit("tokens", self.tokens_used, self.budget.max_tokens)

    def use_api_call(self) -> None:
        """Record an API call."""
        self.api_calls += 1
        self._check_limit("api_calls", self.api_calls, self.budget.max_api_calls)

    def use_chunk(self, count: int = 1) -> None:
        """Record chunk processing."""
        self.chunks_processed += count
        self._check_limit("chunks", self.chunks_processed, self.budget.max_chunks)

    def check_time(self) -> None:
        """Check time budget."""
        elapsed = time.time() - self.start_time
        self._check_limit("time", elapsed, self.budget.max_time_seconds)

    def _check_limit(self, resource: str, used: float, limit: float) -> None:
        """Check if limit exceeded."""
        ratio = used / limit if limit > 0 else 0

        # Warning at threshold
        if ratio >= self.budget.warn_at_percent and ratio < 1.0:
            warning = f"{resource} at {ratio:.0%} of budget"
            if warning not in self.warnings:
                self.warnings.append(warning)

        # Error at limit
        if ratio >= 1.0:
            raise BudgetExceeded(resource, used, limit)

    def get_status(self) -> dict:
        """Get current budget status."""
        elapsed = time.time() - self.start_time
        return {
            "tokens": {
                "used": self.tokens_used,
                "limit": self.budget.max_tokens,
                "percent": self.tokens_used / self.budget.max_tokens * 100,
            },
            "time": {
                "used": elapsed,
                "limit": self.budget.max_time_seconds,
                "percent": elapsed / self.budget.max_time_seconds * 100,
            },
            "api_calls": {
                "used": self.api_calls,
                "limit": self.budget.max_api_calls,
                "percent": self.api_calls / self.budget.max_api_calls * 100,
            },
            "chunks": {
                "used": self.chunks_processed,
                "limit": self.budget.max_chunks,
                "percent": self.chunks_processed / self.budget.max_chunks * 100,
            },
            "warnings": self.warnings,
        }

    def remaining(self) -> dict:
        """Get remaining budget."""
        elapsed = time.time() - self.start_time
        return {
            "tokens": self.budget.max_tokens - self.tokens_used,
            "time": self.budget.max_time_seconds - elapsed,
            "api_calls": self.budget.max_api_calls - self.api_calls,
            "chunks": self.budget.max_chunks - self.chunks_processed,
        }

    def should_stop(self) -> bool:
        """Check if we should stop to preserve budget."""
        remaining = self.remaining()
        return any(v <= 0 for v in remaining.values())


def create_budget_for_mode(mode: str) -> Budget:
    """Create budget for execution mode.

    Args:
        mode: 'quick' or 'deep'.

    Returns:
        Appropriate budget.
    """
    if mode == "quick":
        return Budget(
            max_tokens=50000,
            max_time_seconds=60,
            max_api_calls=20,
            max_chunks=1000,
        )
    else:  # deep
        return Budget(
            max_tokens=500000,
            max_time_seconds=600,
            max_api_calls=200,
            max_chunks=10000,
        )
