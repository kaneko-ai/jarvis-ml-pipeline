"""Schemas for the skills system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class SkillScope(str, Enum):
    """Scope for a skill definition."""

    GLOBAL = "global"
    WORKSPACE = "workspace"


@dataclass
class SkillMetadata:
    """Metadata for a skill loaded from frontmatter."""

    name: str
    description: str
    triggers: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)


@dataclass
class Skill:
    """Loaded skill definition."""

    metadata: SkillMetadata
    scope: SkillScope
    path: Path
    instructions: str | None = None
    resources: dict[str, str] = field(default_factory=dict)
    scripts: dict[str, str] = field(default_factory=dict)
    loaded: bool = False