import pytest

from jarvis_core.security.terminal import TerminalSecurityManager
from jarvis_core.security.terminal_schema import CommandExecutionRequest


def test_sudo_requires_approval():
    manager = TerminalSecurityManager()
    request = CommandExecutionRequest(command="sudo ls")
    result = manager.check_command(request)
    assert result.requires_approval is True
    assert result.allowed is True


@pytest.mark.asyncio
async def test_execute_command_blocks_without_approval():
    manager = TerminalSecurityManager()
    request = CommandExecutionRequest(command="sudo ls")
    result = await manager.execute_command(request, approved=False)
    assert result.allowed is False
    assert result.requires_approval is True
    assert result.blocked_reason