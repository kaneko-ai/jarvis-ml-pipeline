"""Failure learning store for ops_extract mode."""

from __future__ import annotations

import os
import re
import time
from contextlib import contextmanager, suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

LESSONS_PATH = Path("knowledge/failures/lessons_learned.md")
LESSONS_ENV_KEY = "JARVIS_OPS_EXTRACT_LESSONS_PATH"


@contextmanager
def _file_lock(lock_path: Path, timeout_sec: float = 10.0) -> Iterator[None]:
    start = time.time()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = None
    while time.time() - start < timeout_sec:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            time.sleep(0.05)
    if fd is None:
        raise TimeoutError(f"lock_timeout:{lock_path}")
    try:
        yield
    finally:
        with suppress(OSError):
            os.close(fd)
        with suppress(OSError):
            lock_path.unlink(missing_ok=True)


def resolve_lessons_path(path: Path | None = None) -> Path:
    if path is not None:
        return path
    from_env = os.getenv(LESSONS_ENV_KEY)
    if from_env:
        return Path(from_env)
    return LESSONS_PATH


def load_block_rules(path: Path | None = None) -> list[str]:
    path = resolve_lessons_path(path)
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    rules = re.findall(r"^- block_rule:\s*([A-Za-z0-9_:-]+)\s*$", text, flags=re.MULTILINE)
    # keep order but unique
    result: list[str] = []
    for r in rules:
        if r not in result:
            result.append(r)
    return result


def record_lesson(
    *,
    run_id: str,
    category: str,
    root_cause: str,
    recommendation_steps: list[str],
    preventive_checks: list[str],
    lessons_path: Path | None = None,
) -> Path:
    lessons_path = resolve_lessons_path(lessons_path)
    lessons_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = lessons_path.with_suffix(lessons_path.suffix + ".lock")
    now = datetime.now(timezone.utc).isoformat()
    preventive_checks = preventive_checks or []
    block_rule = preventive_checks[0] if preventive_checks else "check_last_run_logs"

    entry_lines = [
        f"## {now} run_id={run_id}",
        f"- category: {category}",
        f"- root_cause: {root_cause}",
        f"- recommendation: {'; '.join(recommendation_steps) if recommendation_steps else '(none)'}",
        f"- preventive_checks: {', '.join(preventive_checks) if preventive_checks else '(none)'}",
        f"- block_rule: {block_rule}",
        "",
    ]
    entry = "\n".join(entry_lines)

    with _file_lock(lock_path):
        if not lessons_path.exists():
            header = "# Lessons Learned\n\n"
            lessons_path.write_text(header, encoding="utf-8")
        with open(lessons_path, "a", encoding="utf-8") as f:
            f.write(entry)
    return lessons_path


def lesson_exists_for_run(run_id: str, lessons_path: Path | None = None) -> bool:
    lessons_path = resolve_lessons_path(lessons_path)
    if not lessons_path.exists():
        return False
    text = lessons_path.read_text(encoding="utf-8", errors="ignore")
    return f"run_id={run_id}" in text
