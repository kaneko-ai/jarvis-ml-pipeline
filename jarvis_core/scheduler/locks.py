"""Schedule execution locks."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


LOCK_DIR = Path("data/locks")
LOCK_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class LockHandle:
    key: str
    path: Path

    def release(self) -> None:
        try:
            if self.path.exists():
                self.path.unlink()
        except FileNotFoundError:
            return


def _read_lock(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def acquire_schedule_lock(schedule_id: str, ttl_seconds: int, margin_seconds: int = 60) -> Optional[LockHandle]:
    key = f"lock:schedule:{schedule_id}"
    path = LOCK_DIR / f"{schedule_id}.lock"
    expires_at = time.time() + ttl_seconds + margin_seconds

    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        payload = _read_lock(path)
        if payload and payload.get("expires_at", 0) < time.time():
            try:
                path.unlink()
            except FileNotFoundError:
                return None
            return acquire_schedule_lock(schedule_id, ttl_seconds, margin_seconds)
        return None

    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"key": key, "expires_at": expires_at}, f)

    return LockHandle(key=key, path=path)
