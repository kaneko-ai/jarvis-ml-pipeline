"""YomiToku CLI adapter."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any


def check_yomitoku_available(command: str = "yomitoku") -> bool:
    return shutil.which(command) is not None


def _load_first_markdown_text(output_dir: Path) -> tuple[str, str | None]:
    md_files = sorted(output_dir.rglob("*.md"))
    if not md_files:
        return "", None
    first = md_files[0]
    return first.read_text(encoding="utf-8", errors="ignore"), str(first)


def run_yomitoku_cli(
    *,
    input_path: Path,
    output_dir: Path,
    mode: str = "normal",
    figure: bool = True,
    command: str = "yomitoku",
    timeout_sec: int = 900,
) -> dict[str, Any]:
    """Run YomiToku CLI with stable arguments.

    The command format is treated as:
    yomitoku -i <input_path> -o <output_dir> --format md --mode <mode> [--figure]
    """
    if not check_yomitoku_available(command):
        raise RuntimeError(f"YomiToku command not found: {command}")
    if not input_path.exists():
        raise FileNotFoundError(f"OCR input not found: {input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    args = [
        command,
        "-i",
        str(input_path),
        "-o",
        str(output_dir),
        "--format",
        "md",
        "--mode",
        mode,
    ]
    if figure:
        args.append("--figure")

    completed = subprocess.run(
        args,
        check=False,
        text=True,
        capture_output=True,
        timeout=timeout_sec,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"YomiToku failed (code={completed.returncode}): {completed.stderr.strip()}"
        )

    text, text_path = _load_first_markdown_text(output_dir)
    figure_count = len(list(output_dir.rglob("*.png"))) + len(list(output_dir.rglob("*.jpg")))
    return {
        "command": args,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "text": text,
        "text_path": text_path,
        "figure_count": figure_count,
    }
