"""Terminal security schema definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class ExecutionPolicy(str, Enum):
    """Execution policy for terminal commands."""

    OFF = "off"
    AUTO = "auto"
    TURBO = "turbo"


@dataclass
class CommandPattern:
    pattern: str
    is_regex: bool = False
    reason: str | None = None


@dataclass
class TerminalSecurityConfig:
    execution_policy: ExecutionPolicy = ExecutionPolicy.AUTO
    allow_list: list[CommandPattern] = field(default_factory=list)
    deny_list: list[CommandPattern] = field(default_factory=list)
    max_execution_time_seconds: int = 30
    require_confirmation_for_sudo: bool = True


@dataclass
class CommandExecutionRequest:
    command: str
    working_dir: str | None = None
    environment: Mapping[str, str] | None = None
    timeout: int | None = None


@dataclass
class CommandExecutionResult:
    command: str
    allowed: bool
    executed: bool
    exit_code: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    blocked_reason: str | None = None
    requires_approval: bool = False