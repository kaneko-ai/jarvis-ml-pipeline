"""Configuration Unification.

Per V4-P02, this provides unified configuration with priority:
CLI > YAML > ENV > default
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Config:
    """Unified configuration."""

    # Core settings
    output_dir: str = "output"
    log_level: str = "INFO"

    # LLM settings
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.0

    # Workflow settings
    max_chunks: int = 100
    chunk_size: int = 1000

    # Performance settings
    timeout_seconds: int = 300
    max_retries: int = 3

    # Determinism
    seed: int | None = None

    # Source tracking
    source: str = "default"  # default, env, yaml, cli
    _overrides: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "output_dir": self.output_dir,
            "log_level": self.log_level,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "llm_temperature": self.llm_temperature,
            "max_chunks": self.max_chunks,
            "chunk_size": self.chunk_size,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "seed": self.seed,
            "source": self.source,
        }


def get_default_config() -> Config:
    """Get default configuration."""
    return Config(source="default")


def load_from_env(base: Config) -> Config:
    """Load configuration from environment variables."""
    env_vars = {
        "JARVIS_OUTPUT_DIR": "output_dir",
        "JARVIS_LOG_LEVEL": "log_level",
        "JARVIS_LLM_PROVIDER": "llm_provider",
        "JARVIS_LLM_MODEL": "llm_model",
        "JARVIS_TIMEOUT": "timeout_seconds",
        "JARVIS_SEED": "seed",
    }

    overrides = {}
    for env_var, attr in env_vars.items():
        value = os.environ.get(env_var)
        if value is not None:
            if attr in ("timeout_seconds", "max_chunks", "chunk_size", "max_retries"):
                value = int(value)
            elif attr == "llm_temperature":
                value = float(value)
            elif attr == "seed":
                value = int(value) if value else None
            setattr(base, attr, value)
            overrides[attr] = "env"

    if overrides:
        base.source = "env"
        base._overrides.update(overrides)

    return base


def load_from_yaml(path: str, base: Config) -> Config:
    """Load configuration from YAML file."""
    yaml_path = Path(path)
    if not yaml_path.exists():
        return base

    # Simple YAML parsing (key: value per line)
    overrides = {}
    with open(yaml_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Type conversion
                if value.isdigit():
                    value = int(value)
                elif value.replace(".", "").isdigit():
                    value = float(value)
                elif value.lower() in ("true", "false"):
                    value = value.lower() == "true"
                elif value.lower() == "null":
                    value = None

                if hasattr(base, key):
                    setattr(base, key, value)
                    overrides[key] = "yaml"

    if overrides:
        base.source = "yaml"
        base._overrides.update(overrides)

    return base


def load_from_cli(args: dict[str, Any], base: Config) -> Config:
    """Load configuration from CLI arguments."""
    overrides = {}
    for key, value in args.items():
        if value is not None and hasattr(base, key):
            setattr(base, key, value)
            overrides[key] = "cli"

    if overrides:
        base.source = "cli"
        base._overrides.update(overrides)

    return base


def load_config(
    yaml_path: str | None = None,
    cli_args: dict[str, Any] | None = None,
) -> Config:
    """Load configuration with priority: CLI > YAML > ENV > default.

    Args:
        yaml_path: Optional path to YAML config.
        cli_args: Optional CLI arguments dict.

    Returns:
        Resolved configuration.
    """
    # Start with defaults
    config = get_default_config()

    # Apply ENV
    config = load_from_env(config)

    # Apply YAML
    if yaml_path:
        config = load_from_yaml(yaml_path, config)

    # Apply CLI
    if cli_args:
        config = load_from_cli(cli_args, config)

    return config


def save_config_snapshot(config: Config, output_dir: str) -> None:
    """Save configuration snapshot to bundle."""
    path = Path(output_dir) / "config_snapshot.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, indent=2)
