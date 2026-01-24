import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlencode


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_url(base_url: str, params: Dict[str, Any]) -> str:
    encoded = urlencode(params, doseq=True)
    return f"{base_url}?{encoded}" if encoded else base_url


def compute_file_hash(path: Path) -> Optional[str]:
    if not path.exists():
        return None

    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class SourceSnapshot:
    path: Path
    payload: Dict[str, Any]

    @classmethod
    def load(cls, path: Path) -> "SourceSnapshot":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(path=path, payload=data)

    @classmethod
    def load_or_create(cls, path: Path, metadata: Dict[str, Any]) -> "SourceSnapshot":
        if path.exists():
            snapshot = cls.load(path)
            snapshot.payload.setdefault("metadata", {}).update(metadata)
            snapshot.save()
            return snapshot

        payload = {
            "snapshot_version": 1,
            "run_id": path.parent.name,
            "created_at": now_iso(),
            "metadata": metadata,
            "sources": [],
        }
        snapshot = cls(path=path, payload=payload)
        snapshot.save()
        return snapshot

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _find_entry(self, url: str, source_type: str) -> Optional[Dict[str, Any]]:
        for entry in self.payload.get("sources", []):
            if entry.get("url") == url and entry.get("type") == source_type:
                return entry
        return None

    def add_candidate(
        self, url: str, source_type: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        entry = self._find_entry(url, source_type)
        if entry is None:
            entry = {
                "url": url,
                "type": source_type,
                "status": "pending",
                "requested_at": None,
                "completed_at": None,
                "http_status": None,
                "hash": None,
                "output_path": None,
                "error": None,
                "metadata": metadata or {},
            }
            self.payload.setdefault("sources", []).append(entry)
        elif metadata:
            entry.setdefault("metadata", {}).update(metadata)
        self.save()

    def start_request(
        self, url: str, source_type: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        self.add_candidate(url, source_type, metadata)
        entry = self._find_entry(url, source_type)
        if entry is None:
            return
        entry["requested_at"] = entry.get("requested_at") or now_iso()
        entry["status"] = "in_progress"
        if metadata:
            entry.setdefault("metadata", {}).update(metadata)
        self.save()

    def finish_request(
        self,
        url: str,
        source_type: str,
        status: str,
        http_status: Optional[int] = None,
        output_path: Optional[str] = None,
        hash_value: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.add_candidate(url, source_type, metadata)
        entry = self._find_entry(url, source_type)
        if entry is None:
            return
        entry["status"] = status
        entry["http_status"] = http_status
        entry["completed_at"] = now_iso()
        entry["hash"] = hash_value
        entry["output_path"] = output_path
        entry["error"] = error
        if metadata:
            entry.setdefault("metadata", {}).update(metadata)
        self.save()
