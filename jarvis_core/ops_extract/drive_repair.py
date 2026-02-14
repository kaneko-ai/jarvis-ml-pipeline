"""Utilities for repairing duplicate Drive folders."""

from __future__ import annotations

from typing import Any


def plan_duplicate_folder_repair(folders: list[dict[str, Any]]) -> dict[str, Any]:
    if not folders:
        return {"status": "not_found", "primary_id": "", "quarantine_ids": []}
    if len(folders) == 1:
        return {
            "status": "ok",
            "primary_id": str(folders[0].get("id", "")),
            "quarantine_ids": [],
        }
    ordered = sorted(
        folders,
        key=lambda x: (
            str(x.get("createdTime", "")),
            str(x.get("id", "")),
        ),
    )
    primary = ordered[0]
    quarantine = ordered[1:]
    return {
        "status": "duplicate_detected",
        "primary_id": str(primary.get("id", "")),
        "quarantine_ids": [str(item.get("id", "")) for item in quarantine],
    }


def repair_duplicate_folders(*, folders: list[dict[str, Any]]) -> dict[str, Any]:
    """Return deterministic repair plan for duplicated folders."""
    return plan_duplicate_folder_repair(folders)

