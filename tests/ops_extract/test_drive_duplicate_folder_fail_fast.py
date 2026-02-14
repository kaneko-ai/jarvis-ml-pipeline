from __future__ import annotations

import pytest

from jarvis_core.ops_extract.drive_client import DriveResumableClient, DriveUploadError


def test_ensure_folder_fails_when_duplicate_exists(monkeypatch):
    client = DriveResumableClient(
        access_token="token",
        api_base_url="https://www.googleapis.com/drive/v3",
        upload_base_url="https://www.googleapis.com/upload/drive/v3/files",
    )

    monkeypatch.setattr(
        client,
        "list_children",
        lambda **_kwargs: [{"id": "f1"}, {"id": "f2"}],
    )

    with pytest.raises(DriveUploadError):
        client.ensure_folder(name="dup", parent_id="root")

