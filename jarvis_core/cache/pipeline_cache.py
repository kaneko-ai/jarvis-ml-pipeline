"""Pipeline Cache (Phase 31).

Provides high-level caching for pipeline stages (extraction, embedding) to enable incremental updates.
"""

from __future__ import annotations

import logging
import hashlib
from pathlib import Path
from typing import Callable, TypeVar

from jarvis_core.cache.kv_cache import KVCache

logger = logging.getLogger(__name__)

T = TypeVar("T")


class PipelineCache:
    """Manages caching for pipeline artifacts."""

    def __init__(self, cache_dir: Path, namespace: str = "pipeline"):
        self.kv = KVCache(cache_dir, name=namespace)

    def get_or_compute(self, input_key: str, compute_fn: Callable[[], T]) -> T:
        """Get value from cache or compute and save it."""
        cached = self.kv.get(input_key)
        if cached is not None:
            logger.debug(f"Cache hit for {input_key}")
            return cached

        logger.debug(f"Cache miss for {input_key}, computing...")
        result = compute_fn()

        # Serialize if it's an object with to_dict, otherwise assume JSON serializable
        stored_value = result
        if hasattr(result, "to_dict"):
            stored_value = result.to_dict()

        self.kv.set(input_key, stored_value)
        return result

    def calculate_file_hash(self, filepath: Path) -> str:
        """Calculate SHA256 of a file for cache keying."""
        if not filepath.exists():
            return "missing"

        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            # Read in chunks
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a structured cache key."""
        base_key = self.kv.generate_key(*args, **kwargs)
        return f"{prefix}:{base_key}"