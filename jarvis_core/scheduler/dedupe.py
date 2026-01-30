"""Paper deduplication registry for scheduler."""

from __future__ import annotations

import json
import re
import threading
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REGISTRY_PATH = Path("data/registry/papers_seen.jsonl")
REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)

_registry_lock = threading.Lock()


def _normalize_title(title: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", title.lower())
    return " ".join(normalized.split())


def _fingerprint(record: dict[str, Any]) -> str:
    pmid = str(record.get("pmid") or "").strip()
    doi = str(record.get("doi") or "").strip().lower()
    title = _normalize_title(record.get("title") or "")
    year = str(record.get("year") or "")
    if pmid:
        return f"pmid:{pmid}"
    if doi:
        return f"doi:{doi}"
    if title:
        return f"title:{title}|{year}"
    return ""


def _load_seen() -> set:
    if not REGISTRY_PATH.exists():
        return set()
    seen = set()
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                seen.add(entry.get("key"))
    return seen


def filter_new_papers(
    records: Iterable[dict[str, Any]], force_refresh: bool = False
) -> list[dict[str, Any]]:
    new_records: list[dict[str, Any]] = []
    with _registry_lock:
        seen = _load_seen()
        for record in records:
            key = _fingerprint(record)
            if not key:
                continue
            if key in seen and not force_refresh:
                continue
            seen.add(key)
            new_records.append({**record, "_dedupe_key": key})
        if new_records:
            with open(REGISTRY_PATH, "a", encoding="utf-8") as f:
                for record in new_records:
                    f.write(
                        json.dumps(
                            {
                                "key": record.get("_dedupe_key"),
                                "pmid": record.get("pmid"),
                                "doi": record.get("doi"),
                                "first_seen_ts": datetime.now(timezone.utc).isoformat(),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
    return new_records