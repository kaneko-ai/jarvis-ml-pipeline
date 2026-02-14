from __future__ import annotations

from types import SimpleNamespace

import pytest

from jarvis_core.ops_extract.oauth_google import refresh_access_token, resolve_drive_access_token


def test_refresh_access_token_success(monkeypatch):
    def _ok_post(*_args, **_kwargs):
        return SimpleNamespace(
            status_code=200,
            content=b"1",
            json=lambda: {"access_token": "new-token", "expires_in": 3600},
        )

    monkeypatch.setattr("requests.post", _ok_post)
    token, expires_in = refresh_access_token(
        refresh_token="refresh",
        client_id="cid",
        client_secret="secret",
    )
    assert token == "new-token"
    assert expires_in == 3600


def test_refresh_access_token_failure(monkeypatch):
    def _ng_post(*_args, **_kwargs):
        return SimpleNamespace(status_code=401, text="invalid_grant", content=b"1")

    monkeypatch.setattr("requests.post", _ng_post)
    with pytest.raises(RuntimeError):
        refresh_access_token(
            refresh_token="refresh",
            client_id="cid",
            client_secret="secret",
        )


def test_resolve_drive_access_token_uses_cache(tmp_path):
    cache_path = tmp_path / "token_cache.json"
    cache_path.write_text(
        '{"access_token":"cached","expires_at":32503680000}',
        encoding="utf-8",
    )
    token = resolve_drive_access_token(
        access_token=None,
        refresh_token=None,
        client_id=None,
        client_secret=None,
        token_cache_path=str(cache_path),
    )
    assert token == "cached"
