"""Configuration loading utilities for Jarvis Core.

Provides lightweight helpers to load YAML configurations and merge overrides
so that environment- or runtime-specific tweaks can be layered on top of
baseline settings. The current implementation keeps merging minimal but aims
for forward compatibility with environment variable overrides.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None


def load_yaml_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML configuration file into a dictionary.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed configuration dictionary.
    """
    if not HAS_YAML:
        return {}

    with Path(path).expanduser().open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def merge_overrides(base: Mapping[str, Any], overrides: Mapping[str, Any] | None) -> dict[str, Any]:
    """Recursively merge ``overrides`` into ``base``.

    Shallow values in ``overrides`` replace those in ``base``; nested mappings
    are merged recursively. Non-mapping values are overwritten directly.
    """

    if overrides is None:
        return dict(base)

    merged: dict[str, Any] = dict(base)
    for key, value in overrides.items():
        if key in merged and isinstance(merged[key], Mapping) and isinstance(value, Mapping):
            merged[key] = merge_overrides(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_and_merge(path: str | Path, overrides: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Convenience wrapper to load a YAML file and apply overrides."""

    base = load_yaml_config(path)
    return merge_overrides(base, overrides)
