"""Hashing utilities for reproducibility.

Per RP-02, this provides deterministic hashing for prompts and inputs.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any


def normalize_text(text: str) -> str:
    """Normalize text for consistent hashing.

    - Lowercase
    - Collapse whitespace
    - Strip leading/trailing whitespace
    """
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def prompt_hash(prompt: str, normalize: bool = True) -> str:
    """Compute hash of a prompt.

    Args:
        prompt: The prompt text.
        normalize: Whether to normalize before hashing.

    Returns:
        SHA256 hash (first 16 chars).
    """
    if normalize:
        prompt = normalize_text(prompt)

    return hashlib.sha256(prompt.encode()).hexdigest()[:16]


def input_hash(data: Any, normalize: bool = True) -> str:
    """Compute hash of any input data.

    Args:
        data: Any JSON-serializable data.
        normalize: Whether to normalize strings.

    Returns:
        SHA256 hash (first 16 chars).
    """
    if isinstance(data, str):
        content = normalize_text(data) if normalize else data
    elif isinstance(data, dict):
        # Sort keys for determinism
        content = json.dumps(data, sort_keys=True, ensure_ascii=False)
    elif isinstance(data, (list, tuple)):
        content = json.dumps(list(data), ensure_ascii=False)
    else:
        content = str(data)

    return hashlib.sha256(content.encode()).hexdigest()[:16]


def compute_cache_key(
    tool_name: str,
    inputs: Any,
    version: str = "1.0",
) -> str:
    """Compute cache key for a tool call.

    Args:
        tool_name: Name of the tool.
        inputs: Tool inputs.
        version: Tool version.

    Returns:
        Deterministic cache key.
    """
    inp_hash = input_hash(inputs)
    combined = f"{tool_name}:{version}:{inp_hash}"
    return hashlib.sha256(combined.encode()).hexdigest()[:24]
