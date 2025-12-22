"""Run Configuration.

Per RP-03, this provides configuration for reproducible execution.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class RunConfig:
    """Configuration for a reproducible run.

    Per JARVIS_MASTER.md, includes cache, seed, and provider settings.
    """

    # Cache settings
    cache_enabled: bool = True
    cache_dir: str = "cache"

    # Reproducibility
    seed: Optional[int] = None

    # Execution
    strict_mode: bool = False
    max_retries: int = 3

    # LLM Provider
    provider: str = "gemini"
    model: str = "gemini-2.0-flash"

    # Thresholds
    thresholds: Dict[str, float] = field(default_factory=lambda: {
        "claim_precision": 0.85,
        "citation_precision": 0.9,
        "unsupported_claim_rate": 0.1,
    })

    # Additional config
    extra: Dict[str, Any] = field(default_factory=dict)

    def apply_seed(self) -> None:
        """Apply seed to random number generators."""
        if self.seed is not None:
            random.seed(self.seed)
            try:
                import numpy as np
                np.random.seed(self.seed)
            except ImportError:
                pass

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return asdict(self)

    def save(self, path: str) -> None:
        """Save config to JSON file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "RunConfig":
        """Load config from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    @classmethod
    def from_dict(cls, data: dict) -> "RunConfig":
        """Create from dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def get_default_config() -> RunConfig:
    """Get default run configuration."""
    return RunConfig()
