"""Atomic I/O utilities for preventing file corruption."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write(path: Path | str, content: str | bytes) -> None:
    """Write content to a file atomically by using a temporary file.

    Args:
        path: Destination path.
        content: Content to write (str or bytes).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Use the same directory as the target to ensure same-filesystem move
    mode = "w" if isinstance(content, str) else "wb"
    encoding = "utf-8" if isinstance(content, str) else None

    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.tmp-", suffix=".tmp")

    try:
        with os.fdopen(tmp_fd, mode, encoding=encoding) as f:
            f.write(content)

        # Atomic replace
        os.replace(tmp_path, path)
    except Exception as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise e


def atomic_write_json(path: Path | str, data: Any, indent: int | None = 2) -> None:
    """Write data to a JSON file atomically.

    Args:
        path: Destination path.
        data: JSON-serializable data.
        indent: JSON indentation level.
    """
    content = json.dumps(data, indent=indent, ensure_ascii=False)
    atomic_write(path, content)


def atomic_write_jsonl(path: Path | str, rows: list[Any]) -> None:
    """Write rows to a JSONL file atomically.

    Args:
        path: Destination path.
        rows: List of JSON-serializable rows.
    """
    content = ""
    for row in rows:
        content += json.dumps(row, ensure_ascii=False) + "\n"
    atomic_write(path, content)
