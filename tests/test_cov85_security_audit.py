from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from jarvis_core.security.audit import AuditLogger


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_log_action_and_hash_chain(tmp_path: Path) -> None:
    logger = AuditLogger(base_dir=tmp_path)

    first = logger.log_action("create", "alice", {"id": 1})
    second = logger.log_action("update", "alice", {"id": 1, "field": "title"})

    assert first.prev_hash is None
    assert second.prev_hash == first.entry_hash
    assert len(first.entry_hash) == 64
    assert len(second.entry_hash) == 64

    date_key = first.timestamp.split("T")[0]
    rows = _read_jsonl(tmp_path / f"{date_key}.jsonl")
    assert [row["action"] for row in rows] == ["create", "update"]
    assert rows[1]["prev_hash"] == rows[0]["entry_hash"]


def test_log_data_access_writes_expected_payload(tmp_path: Path) -> None:
    logger = AuditLogger(base_dir=tmp_path)

    entry = logger.log_data_access(resource="patient_table", user="bob", access_type="read")

    assert entry.action == "data_access"
    assert entry.user == "bob"
    assert entry.details == {"resource": "patient_table", "access_type": "read"}


def test_export_log_filters_by_datetime_range(tmp_path: Path) -> None:
    logger = AuditLogger(base_dir=tmp_path)
    current = logger.log_action("sync", "carol", {"source": "pubmed"})

    # Add one out-of-range record manually in the same daily file.
    date_key = current.timestamp.split("T")[0]
    old_payload = {
        "timestamp": (datetime.fromisoformat(current.timestamp) - timedelta(days=3)).isoformat(),
        "action": "old_action",
        "user": "carol",
        "details": {"source": "legacy"},
        "entry_hash": "h" * 64,
        "prev_hash": None,
    }
    with (tmp_path / f"{date_key}.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(old_payload) + "\n")

    start = datetime.fromisoformat(current.timestamp) - timedelta(minutes=1)
    end = datetime.fromisoformat(current.timestamp) + timedelta(minutes=1)
    exported = logger.export_log(start=start, end=end)

    assert len(exported) == 1
    assert exported[0].action == "sync"
    assert exported[0].details["source"] == "pubmed"
