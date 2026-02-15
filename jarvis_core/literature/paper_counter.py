"""Paper counter store for personal literature collection progress."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_FIELDS = ("discovered", "downloaded", "parsed", "indexed")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _blank_counts() -> dict[str, int]:
    return {field: 0 for field in _FIELDS}


def _normalize_counts(raw: Any) -> dict[str, int]:
    if not isinstance(raw, dict):
        return _blank_counts()
    normalized = _blank_counts()
    for field in _FIELDS:
        try:
            normalized[field] = max(0, int(raw.get(field, 0) or 0))
        except Exception:
            normalized[field] = 0
    return normalized


class PaperCounterStore:
    """Single-file JSON counter store with atomic updates."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def init_if_missing(self) -> dict[str, Any]:
        if self.path.exists():
            return self.snapshot()
        payload = {
            "schema_version": "1",
            "updated_at": _now_iso(),
            "totals": _blank_counts(),
            "by_run": {},
        }
        self._atomic_write(payload)
        return payload

    def snapshot(self) -> dict[str, Any]:
        payload = self._read()
        normalized = {
            "schema_version": str(payload.get("schema_version", "1")),
            "updated_at": str(payload.get("updated_at", _now_iso())),
            "totals": _normalize_counts(payload.get("totals")),
            "by_run": {},
        }
        by_run = payload.get("by_run", {})
        if isinstance(by_run, dict):
            for run_id, run_counts in by_run.items():
                rid = str(run_id).strip()
                if not rid:
                    continue
                normalized["by_run"][rid] = _normalize_counts(run_counts)
        return normalized

    def bump(self, run_id: str, field: str, delta: int = 1) -> dict[str, Any]:
        target_field = str(field).strip()
        if target_field not in _FIELDS:
            raise ValueError(f"unknown_field:{target_field}")
        rid = str(run_id).strip()
        if not rid:
            raise ValueError("run_id_required")
        amount = int(delta)
        if amount == 0:
            return self.snapshot()

        payload = self.snapshot()
        payload["totals"][target_field] = max(0, int(payload["totals"][target_field]) + amount)
        run_map = payload["by_run"].setdefault(rid, _blank_counts())
        run_map[target_field] = max(0, int(run_map[target_field]) + amount)
        payload["updated_at"] = _now_iso()
        self._atomic_write(payload)
        return payload

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {
                "schema_version": "1",
                "updated_at": _now_iso(),
                "totals": _blank_counts(),
                "by_run": {},
            }
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {
                "schema_version": "1",
                "updated_at": _now_iso(),
                "totals": _blank_counts(),
                "by_run": {},
            }
        return payload if isinstance(payload, dict) else {}

    def _atomic_write(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp_path, self.path)
