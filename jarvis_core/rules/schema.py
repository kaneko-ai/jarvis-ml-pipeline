"""Rules schema definitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class RuleScope(str, Enum):
    """Scope for a rule file."""

    GLOBAL = "global"
    WORKSPACE = "workspace"


@dataclass
class Rule:
    """Rule definition loaded from disk."""

    name: str
    scope: RuleScope
    path: Path
    content: str
    enabled: bool = True
