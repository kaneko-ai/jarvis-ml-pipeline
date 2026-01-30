"""Terminal security manager implementation."""

from __future__ import annotations

import asyncio
import os
import re
import shlex
from pathlib import Path

import yaml

from .terminal_schema import (
    CommandExecutionRequest,
    CommandExecutionResult,
    CommandPattern,
    ExecutionPolicy,
    TerminalSecurityConfig,
)


class TerminalSecurityManager:
    """Evaluate and execute terminal commands with policy enforcement."""

    def __init__(self, config: TerminalSecurityConfig | None = None) -> None:
        self._config = config or TerminalSecurityConfig()
        self._allow_list = self._default_allow_list() + list(self._config.allow_list)
        self._deny_list = self._default_deny_list() + list(self._config.deny_list)

    @classmethod
    def from_yaml(cls, config_path: Path) -> TerminalSecurityManager:
        data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}
        config = TerminalSecurityConfig(
            execution_policy=ExecutionPolicy(data.get("execution_policy", ExecutionPolicy.AUTO)),
            allow_list=[CommandPattern(**item) for item in data.get("allow_list", [])],
            deny_list=[CommandPattern(**item) for item in data.get("deny_list", [])],
            max_execution_time_seconds=data.get("max_execution_time_seconds", 30),
            require_confirmation_for_sudo=data.get("require_confirmation_for_sudo", True),
        )
        return cls(config)

    def _default_allow_list(self) -> list[CommandPattern]:
        return [
            CommandPattern(pattern="ls", is_regex=False, reason="Safe listing"),
            CommandPattern(pattern="cat", is_regex=False, reason="Safe read"),
            CommandPattern(pattern="git status", is_regex=False, reason="Git status"),
            CommandPattern(pattern="pwd", is_regex=False, reason="Print working directory"),
            CommandPattern(pattern="whoami", is_regex=False, reason="User identity"),
        ]

    def _default_deny_list(self) -> list[CommandPattern]:
        return [
            CommandPattern(pattern="rm -rf /", is_regex=False, reason="Dangerous delete"),
            CommandPattern(pattern="mkfs", is_regex=False, reason="Filesystem format"),
            CommandPattern(pattern="shutdown", is_regex=False, reason="Shutdown command"),
            CommandPattern(pattern="reboot", is_regex=False, reason="Reboot command"),
            CommandPattern(
                pattern=r":\s*\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",
                is_regex=True,
                reason="Fork bomb",
            ),
            CommandPattern(pattern="dd if=", is_regex=False, reason="Raw disk write"),
        ]

    def _matches_pattern(self, command: str, pattern: CommandPattern) -> bool:
        if pattern.is_regex:
            return re.search(pattern.pattern, command) is not None
        return pattern.pattern in command

    def _detect_sudo(self, command: str) -> bool:
        tokens = shlex.split(command)
        return bool(tokens) and tokens[0] == "sudo"

    def check_command(self, request: CommandExecutionRequest) -> CommandExecutionResult:
        command = request.command
        if self._config.execution_policy == ExecutionPolicy.OFF:
            return CommandExecutionResult(
                command=command,
                allowed=False,
                executed=False,
                blocked_reason="Execution policy is OFF",
            )

        for pattern in self._deny_list:
            if self._matches_pattern(command, pattern):
                return CommandExecutionResult(
                    command=command,
                    allowed=False,
                    executed=False,
                    blocked_reason=pattern.reason or "Denied by policy",
                )

        requires_approval = False
        if self._config.require_confirmation_for_sudo and self._detect_sudo(command):
            requires_approval = True

        if self._allow_list:
            allowed = any(self._matches_pattern(command, pattern) for pattern in self._allow_list)
            if not allowed:
                return CommandExecutionResult(
                    command=command,
                    allowed=False,
                    executed=False,
                    blocked_reason="Command not in allow list",
                    requires_approval=requires_approval,
                )

        return CommandExecutionResult(
            command=command,
            allowed=True,
            executed=False,
            requires_approval=requires_approval,
        )

    async def execute_command(
        self, request: CommandExecutionRequest, approved: bool
    ) -> CommandExecutionResult:
        result = self.check_command(request)
        if not result.allowed:
            return result
        if result.requires_approval and not approved:
            return CommandExecutionResult(
                command=request.command,
                allowed=False,
                executed=False,
                blocked_reason="Approval required for sudo command",
                requires_approval=True,
            )

        timeout = request.timeout or self._config.max_execution_time_seconds
        env = os.environ.copy()
        if request.environment:
            env.update(request.environment)

        process = await asyncio.create_subprocess_shell(
            request.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=request.working_dir,
            env=env,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return CommandExecutionResult(
                command=request.command,
                allowed=True,
                executed=True,
                exit_code=process.returncode,
                stdout=stdout.decode("utf-8", errors="ignore"),
                stderr=stderr.decode("utf-8", errors="ignore"),
            )
        except asyncio.TimeoutError:
            process.kill()
            return CommandExecutionResult(
                command=request.command,
                allowed=True,
                executed=True,
                blocked_reason="Command timed out",
            )