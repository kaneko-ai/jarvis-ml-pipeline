"""Audit trail logging with hash chaining."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class AuditEntry:
    timestamp: str
    action: str
    user: str
    details: dict
    entry_hash: str
    prev_hash: str | None = None


class AuditLogger:
    """Audit logger that writes to logs/audit with hash chaining."""

    def __init__(self, base_dir: Path | str = "logs/audit") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._last_hash: dict[str, str | None] = {}

    def log_action(self, action: str, user: str, details: dict) -> AuditEntry:
        return self._log_entry(action=action, user=user, details=details)

    def log_data_access(self, resource: str, user: str, access_type: str) -> AuditEntry:
        return self._log_entry(
            action="data_access",
            user=user,
            details={"resource": resource, "access_type": access_type},
        )

    def export_log(self, start: datetime, end: datetime) -> list[AuditEntry]:
        entries: list[AuditEntry] = []
        current = start.date()
        while current <= end.date():
            path = self._log_path(current)
            if path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    payload = json.loads(line)
                    ts = datetime.fromisoformat(payload["timestamp"])
                    if start <= ts <= end:
                        entries.append(
                            AuditEntry(
                                timestamp=payload["timestamp"],
                                action=payload["action"],
                                user=payload["user"],
                                details=payload["details"],
                                entry_hash=payload["entry_hash"],
                                prev_hash=payload.get("prev_hash"),
                            )
                        )
            current = current.fromordinal(current.toordinal() + 1)
        return entries

    def _log_entry(self, action: str, user: str, details: dict) -> AuditEntry:
        timestamp = datetime.utcnow().isoformat()
        date_key = timestamp.split("T")[0]
        prev_hash = self._last_hash.get(date_key)
        payload = json.dumps(
            {"timestamp": timestamp, "action": action, "user": user, "details": details},
            sort_keys=True,
        )
        entry_hash = hashlib.sha256(f"{prev_hash or ''}{payload}".encode("utf-8")).hexdigest()
        entry = AuditEntry(
            timestamp=timestamp,
            action=action,
            user=user,
            details=details,
            entry_hash=entry_hash,
            prev_hash=prev_hash,
        )
        self._write_entry(date_key, entry)
        self._last_hash[date_key] = entry_hash
        return entry

    def _log_path(self, date_value) -> Path:
        return self.base_dir / f"{date_value}.jsonl"

    def _write_entry(self, date_key: str, entry: AuditEntry) -> None:
        path = self._log_path(date_key)
        record = {
            "timestamp": entry.timestamp,
            "action": entry.action,
            "user": entry.user,
            "details": entry.details,
            "entry_hash": entry.entry_hash,
            "prev_hash": entry.prev_hash,
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")