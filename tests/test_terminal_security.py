import pytest

from jarvis_core.security.terminal import TerminalSecurityManager
from jarvis_core.security.terminal_schema import (
    CommandExecutionRequest,
    ExecutionPolicy,
    TerminalSecurityConfig,
)


def test_terminal_security_blocks_deny_list():
    manager = TerminalSecurityManager()
    request = CommandExecutionRequest(command="rm -rf /")
    result = manager.check_command(request)
    assert result.allowed is False
    assert result.blocked_reason


def test_terminal_security_allows_safe_command():
    manager = TerminalSecurityManager()
    request = CommandExecutionRequest(command="git status")
    result = manager.check_command(request)
    assert result.allowed is True
    assert result.executed is False


def test_terminal_security_off_policy_blocks():
    config = TerminalSecurityConfig(execution_policy=ExecutionPolicy.OFF)
    manager = TerminalSecurityManager(config)
    request = CommandExecutionRequest(command="ls")
    result = manager.check_command(request)
    assert result.allowed is False
    assert result.blocked_reason == "Execution policy is OFF"


@pytest.mark.asyncio
async def test_execute_command_runs_when_allowed(tmp_path):
    manager = TerminalSecurityManager()
    request = CommandExecutionRequest(command="pwd", working_dir=str(tmp_path))
    result = await manager.execute_command(request, approved=True)
    assert result.executed is True
    assert result.exit_code == 0