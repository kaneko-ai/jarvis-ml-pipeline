"""Safe Paths.

Per PR-101, prevents path traversal attacks.
"""

from __future__ import annotations

from pathlib import Path


class PathTraversalError(Exception):
    """Raised when path traversal is detected."""

    pass


def safe_join(base: str, *paths: str) -> Path:
    """Safely join paths, preventing traversal outside base.

    Raises:
        PathTraversalError: If result would be outside base.
    """
    base_path = Path(base).resolve()

    # Join and resolve
    full_path = base_path
    for p in paths:
        # Remove leading slashes and normalize
        p = p.lstrip("/\\")
        full_path = full_path / p

    resolved = full_path.resolve()

    # Check if resolved path is under base
    try:
        resolved.relative_to(base_path)
    except ValueError:
        raise PathTraversalError(f"Path traversal detected: {paths} would escape {base}")

    return resolved


def is_safe_path(base: str, path: str) -> bool:
    """Check if a path is safe (within base)."""
    try:
        safe_join(base, path)
        return True
    except PathTraversalError:
        return False


def sanitize_filename(name: str) -> str:
    """Sanitize a filename for safe storage."""
    # Remove path separators
    name = name.replace("/", "_").replace("\\", "_")

    # Remove . and ..
    name = name.replace("..", "_").lstrip(".")

    # Remove other dangerous chars
    dangerous = '<>:"|?*'
    for c in dangerous:
        name = name.replace(c, "_")

    # Limit length
    if len(name) > 200:
        name = name[:200]

    return name or "unnamed"


ALLOWED_DIRS = [
    "logs",
    "data",
    "output",
    "tests/fixtures",
]


def check_allowed_directory(path: str, base: str) -> bool:
    """Check if path is in an allowed directory."""
    resolved = Path(path).resolve()
    base_resolved = Path(base).resolve()

    for allowed in ALLOWED_DIRS:
        allowed_path = base_resolved / allowed
        try:
            resolved.relative_to(allowed_path)
            return True
        except ValueError:
            continue

    return False