from __future__ import annotations

import json
from types import SimpleNamespace
from pathlib import Path

from jarvis_core.ops_extract.oauth_google import resolve_drive_access_token


def test_oauth_google_uses_cached_refresh_token(monkeypatch, tmp_path: Path) -> None:
    cache_path = tmp_path / "drive_token.json"
    cache_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "refresh_token": "cached_refresh",
                "client_id": "cached_client",
                "client_secret": "cached_secret",
                "access_token": "",
                "expires_at": 0,
            }
        ),
        encoding="utf-8",
    )

    def _ok_post(*_args, **_kwargs):
        return SimpleNamespace(
            status_code=200,
            content=b"1",
            json=lambda: {"access_token": "fresh_from_cache", "expires_in": 3600},
        )

    monkeypatch.setattr("requests.post", _ok_post)
    token = resolve_drive_access_token(
        access_token=None,
        refresh_token=None,
        client_id=None,
        client_secret=None,
        token_cache_path=str(cache_path),
    )
    assert token == "fresh_from_cache"
    saved = json.loads(cache_path.read_text(encoding="utf-8"))
    assert saved["refresh_token"] == "cached_refresh"
    assert saved["access_token"] == "fresh_from_cache"
