"""Path Normalizer.

Per RP-166, handles Windows/WSL path and encoding differences.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def normalize_path(path: str | Path) -> Path:
    """Normalize path for cross-platform compatibility.

    Args:
        path: Input path (string or Path).

    Returns:
        Normalized Path object.
    """
    if isinstance(path, str):
        # Convert WSL paths to Windows if running on Windows
        if sys.platform == "win32" and path.startswith("/mnt/"):
            # /mnt/c/... -> C:/...
            match = re.match(r"/mnt/([a-z])/(.+)", path)
            if match:
                drive = match.group(1).upper()
                rest = match.group(2)
                path = f"{drive}:/{rest}"

        path = Path(path)

    # Resolve to absolute
    path = path.resolve()

    return path


def normalize_line_endings(text: str) -> str:
    """Normalize line endings to Unix style.

    Args:
        text: Input text.

    Returns:
        Text with normalized line endings.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_text_normalized(filepath: str | Path) -> str:
    """Read text file with normalized encoding and line endings.

    Args:
        filepath: Path to file.

    Returns:
        Normalized text content.
    """
    path = normalize_path(filepath)
    text = path.read_text(encoding="utf-8")
    return normalize_line_endings(text)


def write_text_normalized(filepath: str | Path, text: str) -> None:
    """Write text file with UTF-8 encoding and Unix line endings.

    Args:
        filepath: Path to file.
        text: Text content.
    """
    path = normalize_path(filepath)
    # Normalize line endings
    text = normalize_line_endings(text)
    # Write with newline="" to prevent Python's automatic CRLF on Windows
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def path_to_uri(path: str | Path) -> str:
    """Convert path to file:// URI.

    Args:
        path: Input path.

    Returns:
        File URI string.
    """
    path = normalize_path(path)

    if sys.platform == "win32":
        # Windows: file:///C:/...
        return f"file:///{path.as_posix()}"
    else:
        # Unix: file:///home/...
        return f"file://{path.as_posix()}"


def uri_to_path(uri: str) -> Path:
    """Convert file:// URI to path.

    Args:
        uri: File URI.

    Returns:
        Path object.
    """
    if not uri.startswith("file://"):
        return Path(uri)

    # Remove file:// prefix
    path_str = uri[7:]

    # Handle Windows paths
    if sys.platform == "win32" and path_str.startswith("/"):
        # /C:/... -> C:/...
        path_str = path_str[1:]

    return normalize_path(path_str)


def ensure_utf8_stdout():
    """Ensure stdout uses UTF-8 encoding (Windows fix)."""
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
