from __future__ import annotations

from jarvis_core.ops_extract.drive_repair import repair_duplicate_folders


def test_repair_mode_returns_primary_and_quarantine_ids():
    report = repair_duplicate_folders(
        folders=[
            {"id": "f2", "createdTime": "2026-02-14T00:00:00+00:00"},
            {"id": "f1", "createdTime": "2026-02-13T00:00:00+00:00"},
            {"id": "f3", "createdTime": "2026-02-15T00:00:00+00:00"},
        ]
    )
    assert report["status"] == "duplicate_detected"
    assert report["primary_id"] == "f1"
    assert sorted(report["quarantine_ids"]) == ["f2", "f3"]

