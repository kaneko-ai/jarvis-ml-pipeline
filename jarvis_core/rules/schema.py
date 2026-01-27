"""Schema definitions for rules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RuleScope(str, Enum):
    """Rule scope for configuration."""

    GLOBAL = "global"
    WORKSPACE = "workspace"


@dataclass
class Rule:
    """Rule definition."""

    name: str
    scope: RuleScope
    path: str
    content: str
    enabled: bool = True
