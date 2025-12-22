"""Remediation Catalog.

Per RP-185, provides registry for remediation actions.
"""
from __future__ import annotations

from typing import Dict, Optional, List
from .actions import RemediationAction, BUILTIN_ACTIONS


class DuplicateActionError(Exception):
    """Raised when registering duplicate action ID."""
    pass


class ActionCatalog:
    """Registry for remediation actions."""

    def __init__(self):
        self._actions: Dict[str, RemediationAction] = {}
        self._register_builtins()

    def _register_builtins(self):
        """Register built-in actions."""
        for action in BUILTIN_ACTIONS:
            self._actions[action.action_id] = action

    def register(self, action: RemediationAction) -> None:
        """Register a new action.

        Args:
            action: The action to register.

        Raises:
            DuplicateActionError: If action ID already exists.
        """
        if action.action_id in self._actions:
            raise DuplicateActionError(
                f"Action '{action.action_id}' already registered"
            )
        self._actions[action.action_id] = action

    def get(self, action_id: str) -> Optional[RemediationAction]:
        """Get action by ID."""
        return self._actions.get(action_id)

    def list_actions(self) -> List[str]:
        """List all registered action IDs."""
        return list(self._actions.keys())

    def has(self, action_id: str) -> bool:
        """Check if action exists."""
        return action_id in self._actions


# Global catalog
_catalog: Optional[ActionCatalog] = None


def get_catalog() -> ActionCatalog:
    """Get global action catalog."""
    global _catalog
    if _catalog is None:
        _catalog = ActionCatalog()
    return _catalog


def get_action(action_id: str) -> Optional[RemediationAction]:
    """Get action from global catalog."""
    return get_catalog().get(action_id)
