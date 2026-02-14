from __future__ import annotations

import pytest

from jarvis_core.ops_extract.drive_client import DriveResumableClient, DriveUploadError


def test_drive_client_duplicate_folder_error_includes_ids(monkeypatch):
    client = DriveResumableClient(
        access_token="token",
        api_base_url="https://www.googleapis.com/drive/v3",
        upload_base_url="https://www.googleapis.com/upload/drive/v3/files",
    )
    monkeypatch.setattr(
        client,
        "list_children",
        lambda **_kwargs: [{"id": "folder-1"}, {"id": "folder-2"}],
    )

    with pytest.raises(DriveUploadError) as exc_info:
        client.ensure_folder(name="dup", parent_id="root")

    message = str(exc_info.value)
    assert "duplicate_folder_detected:dup" in message
    assert "ids=folder-1,folder-2" in message
