"""Path validation for security (Phase 10)."""

from __future__ import annotations
from pathlib import Path
from typing import Set


class ForbiddenPathError(ValueError):
    """Raised when a path is forbidden for security reasons."""

    pass


class PathValidator:
    """Validator for file paths to prevent traversal and other safety issues."""

    def __init__(
        self,
        base_dir: Path,
        allowed_extensions: Set[str] | None = None,
        allow_symlinks: bool = False,
    ):
        """Initialize PathValidator.

        Args:
            base_dir: The root directory that all paths must stay within.
            allowed_extensions: Optional set of allowed extensions (e.g. {".pdf", ".bib"}).
            allow_symlinks: Whether to allow symlinks in the path.
        """
        self.base_dir = Path(base_dir).resolve()
        self.allowed_extensions = (
            {
                ext.lower() if ext.startswith(".") else f".{ext.lower()}"
                for ext in allowed_extensions
            }
            if allowed_extensions
            else None
        )
        self.allow_symlinks = allow_symlinks

    def validate(self, target_path: str | Path) -> Path:
        """Validate a path and return its absolute resolved form.

        Args:
            target_path: Path to validate.

        Returns:
            Resolved absolute path.

        Raises:
            ForbiddenPathError: If path is invalid or potentially dangerous.
        """
        path = Path(target_path)

        # 1. Reject paths containing ".." before resolution (defense in depth)
        if ".." in path.parts:
            raise ForbiddenPathError(f"Path contains '..' traversal pattern: {target_path}")

        # 2. Resolve to absolute path
        try:
            # Note: resolve() follows symlinks
            resolved = path.resolve()
        except Exception as e:
            raise ForbiddenPathError(f"Failed to resolve path: {target_path} - {e}")

        # 3. Check base directory constraint (Path Traversal prevention)
        # Using commonpath is safer than startswith for paths
        try:
            # If resolved is outside base_dir, commonpath(base_dir, resolved) will be base_dir or a parent of it
            # But simpler is to check if it's relative to base_dir
            resolved.relative_to(self.base_dir)
        except ValueError:
            raise ForbiddenPathError(
                f"Path traversal detected: {resolved} is outside allowed base {self.base_dir}"
            )

        # 4. Check symlinks if forbidden
        if not self.allow_symlinks:
            # We check the original path parts to see if any exist as symlinks
            # and also check the resolved path.
            curr = path
            while curr != curr.parent:
                if curr.exists() and curr.is_symlink():
                    raise ForbiddenPathError(f"Symlinks are restricted: {curr}")
                curr = curr.parent

        # 5. Check extension
        if self.allowed_extensions:
            if resolved.suffix.lower() not in self.allowed_extensions:
                raise ForbiddenPathError(
                    f"Extension {resolved.suffix} not allowed. "
                    f"Must be one of: {self.allowed_extensions}"
                )

        return resolved
