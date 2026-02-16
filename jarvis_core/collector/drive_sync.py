"""Optional Google Drive sync wrapper for collector outputs."""

from __future__ import annotations

from pathlib import Path


def sync_to_drive(*, run_dir: Path, drive_folder: str | None) -> tuple[bool, str]:
    if not drive_folder:
        return False, "Drive folder is not configured. Manual action required."
    try:
        from jarvis_core.ops_extract.drive_sync import sync_run_to_drive
    except Exception as exc:
        return False, f"Drive sync backend unavailable: {exc}"

    try:
        state = sync_run_to_drive(
            run_dir=run_dir,
            enabled=True,
            dry_run=False,
            upload_workers=2,
            folder_id=drive_folder,
        )
    except Exception as exc:
        return False, f"Drive sync failed: {exc}"
    ok = str(state.get("state", "")) == "committed"
    if ok:
        return True, "Drive sync completed."
    return False, f"Drive sync incomplete: {state.get('state', 'unknown')}"
