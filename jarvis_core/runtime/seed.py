"""Seed Enforcement.

Per PR-67, ensures deterministic random behavior.
"""

from __future__ import annotations

import hashlib
import random
import warnings

_enforced_seed: int | None = None


def enforce_seed(seed: int) -> None:
    """Enforce a random seed globally."""
    global _enforced_seed
    _enforced_seed = seed

    # Set Python random
    random.seed(seed)

    # Try to set numpy if available
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass


def get_enforced_seed() -> int | None:
    """Get the currently enforced seed."""
    return _enforced_seed


def require_seed() -> int:
    """Require that a seed is set. Raises if not."""
    if _enforced_seed is None:
        raise RuntimeError(
            "No seed enforced. Set seed via RunConfig or enforce_seed() "
            "to ensure reproducibility."
        )
    return _enforced_seed


def warn_if_no_seed() -> None:
    """Warn if no seed is set (non-blocking)."""
    if _enforced_seed is None:
        warnings.warn(
            "No random seed enforced. Results may not be reproducible. "
            "Set seed in RunConfig for reproducibility.",
            UserWarning,
            stacklevel=2,
        )


def deterministic_hash(data: str) -> str:
    """Create a deterministic hash (not affected by random)."""
    return hashlib.sha256(data.encode()).hexdigest()


def reset_seed() -> None:
    """Reset the enforced seed (for testing)."""
    global _enforced_seed
    _enforced_seed = None
