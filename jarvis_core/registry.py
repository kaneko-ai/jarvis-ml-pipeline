"""Agent registry backed by configuration files.

The registry maps categories and agent names to concrete implementations so the
router can select appropriate tools for a given task. Definitions are intended
to be loaded from YAML (e.g., configs/agents.yaml) and optionally overridden at
runtime.
"""

from __future__ import annotations

import importlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config_loader import load_and_merge


@dataclass
class AgentDefinition:
    name: str
    category: str
    entrypoint: str
    description: str | None = None
    capabilities: list[str] | None = None

    def load_class(self):
        module_name, _, cls_name = self.entrypoint.partition(":")
        if not module_name or not cls_name:
            raise ValueError(f"Invalid entrypoint: {self.entrypoint}")
        module = importlib.import_module(module_name)
        return getattr(module, cls_name)


class AgentRegistry:
    """Configuration-driven registry of available agents."""

    def __init__(
        self,
        agents: Mapping[str, AgentDefinition],
        categories: Mapping[str, Mapping[str, Any]],
    ) -> None:
        self._agents = dict(agents)
        self._categories = dict(categories)

    @classmethod
    def from_file(
        cls, path: str | Path, overrides: Mapping[str, Any] | None = None
    ) -> AgentRegistry:
        config = load_and_merge(path, overrides)
        raw_agents = config.get("agents", {})
        agent_defs: dict[str, AgentDefinition] = {}
        for name, data in raw_agents.items():
            agent_defs[name] = AgentDefinition(
                name=name,
                category=data.get("category", "generic"),
                entrypoint=data.get("entrypoint", ""),
                description=data.get("description"),
                capabilities=data.get("capabilities"),
            )
        categories = config.get("categories", {})
        return cls(agent_defs, categories)

    def get_agent(self, name: str) -> AgentDefinition | None:
        return self._agents.get(name)

    def get_agents_for_category(self, category: str) -> list[AgentDefinition]:
        agent_names: Iterable[str] = self._categories.get(category, {}).get("agents", [])
        return [self._agents[name] for name in agent_names if name in self._agents]

    def get_default_agent_for_category(self, category: str) -> AgentDefinition | None:
        category_cfg = self._categories.get(category)
        if not category_cfg:
            return None
        default_name = category_cfg.get("default_agent")
        if not default_name:
            return None
        return self.get_agent(default_name)

    def create_agent_instance(self, name: str, **kwargs: Any):
        definition = self.get_agent(name)
        if not definition:
            raise KeyError(f"Agent '{name}' not found in registry")
        cls = definition.load_class()
        try:
            return cls(**kwargs)
        except TypeError:
            # Some agents may not accept kwargs; attempt no-arg construction.
            return cls()
