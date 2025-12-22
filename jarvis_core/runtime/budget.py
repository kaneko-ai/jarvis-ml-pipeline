"""Budget Manager (All-Layer).

Per RP-138, enforces budget limits across all layers.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional
from enum import Enum
import threading


class BudgetType(Enum):
    """Types of budget limits."""

    TIME = "time"
    DOCS = "docs"
    TOKENS = "tokens"
    RETRIES = "retries"
    TOOL_CALLS = "tool_calls"


@dataclass
class BudgetLimits:
    """Budget limits for a run."""

    max_seconds: float = 300.0  # 5 minutes default
    max_docs: int = 100
    max_tokens: int = 50000
    max_retries: int = 10
    max_tool_calls: int = 50


@dataclass
class BudgetUsage:
    """Current budget usage."""

    seconds_used: float = 0.0
    docs_used: int = 0
    tokens_used: int = 0
    retries_used: int = 0
    tool_calls_used: int = 0


class BudgetExceeded(Exception):
    """Raised when budget is exceeded."""

    def __init__(self, budget_type: BudgetType, limit: float, used: float):
        self.budget_type = budget_type
        self.limit = limit
        self.used = used
        super().__init__(
            f"Budget exceeded: {budget_type.value} limit {limit}, used {used}"
        )


class BudgetManager:
    """Manages budget limits across all layers."""

    def __init__(self, limits: Optional[BudgetLimits] = None):
        self.limits = limits or BudgetLimits()
        self.usage = BudgetUsage()
        self._start_time = time.time()
        self._lock = threading.Lock()

    def check_time(self) -> bool:
        """Check if time budget is exceeded."""
        elapsed = time.time() - self._start_time
        self.usage.seconds_used = elapsed
        return elapsed <= self.limits.max_seconds

    def check_all(self) -> tuple[bool, Optional[BudgetType]]:
        """Check all budgets. Returns (ok, exceeded_type)."""
        with self._lock:
            # Time
            if not self.check_time():
                return False, BudgetType.TIME

            # Docs
            if self.usage.docs_used > self.limits.max_docs:
                return False, BudgetType.DOCS

            # Tokens
            if self.usage.tokens_used > self.limits.max_tokens:
                return False, BudgetType.TOKENS

            # Retries
            if self.usage.retries_used > self.limits.max_retries:
                return False, BudgetType.RETRIES

            # Tool calls
            if self.usage.tool_calls_used > self.limits.max_tool_calls:
                return False, BudgetType.TOOL_CALLS

            return True, None

    def add_docs(self, count: int) -> None:
        """Add to docs usage."""
        with self._lock:
            self.usage.docs_used += count

    def add_tokens(self, count: int) -> None:
        """Add to tokens usage."""
        with self._lock:
            self.usage.tokens_used += count

    def add_retry(self) -> None:
        """Add a retry."""
        with self._lock:
            self.usage.retries_used += 1

    def add_tool_call(self) -> None:
        """Add a tool call."""
        with self._lock:
            self.usage.tool_calls_used += 1

    def get_remaining(self) -> dict:
        """Get remaining budget."""
        with self._lock:
            elapsed = time.time() - self._start_time
            return {
                "seconds": max(0, self.limits.max_seconds - elapsed),
                "docs": max(0, self.limits.max_docs - self.usage.docs_used),
                "tokens": max(0, self.limits.max_tokens - self.usage.tokens_used),
                "retries": max(0, self.limits.max_retries - self.usage.retries_used),
                "tool_calls": max(0, self.limits.max_tool_calls - self.usage.tool_calls_used),
            }

    def require_budget(self, budget_type: BudgetType) -> None:
        """Require budget available, raise if exceeded."""
        ok, exceeded = self.check_all()
        if not ok and exceeded == budget_type:
            limit = getattr(self.limits, f"max_{budget_type.value}", 0)
            used = getattr(self.usage, f"{budget_type.value}_used", 0)
            raise BudgetExceeded(budget_type, limit, used)

    def summary(self) -> dict:
        """Get usage summary."""
        remaining = self.get_remaining()
        return {
            "limits": {
                "max_seconds": self.limits.max_seconds,
                "max_docs": self.limits.max_docs,
                "max_tokens": self.limits.max_tokens,
            },
            "usage": {
                "seconds": self.usage.seconds_used,
                "docs": self.usage.docs_used,
                "tokens": self.usage.tokens_used,
            },
            "remaining": remaining,
        }


# Global budget manager
_budget_manager: Optional[BudgetManager] = None


def get_budget_manager() -> BudgetManager:
    """Get global budget manager."""
    global _budget_manager
    if _budget_manager is None:
        _budget_manager = BudgetManager()
    return _budget_manager


def set_budget_manager(manager: BudgetManager) -> None:
    """Set global budget manager."""
    global _budget_manager
    _budget_manager = manager
