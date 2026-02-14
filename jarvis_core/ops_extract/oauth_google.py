"""Google OAuth token refresh helpers for ops_extract."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests


def _read_token_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _write_token_cache(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def refresh_access_token(
    *,
    refresh_token: str,
    client_id: str,
    client_secret: str,
    timeout_sec: float = 15.0,
) -> tuple[str, int]:
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=timeout_sec,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"oauth_refresh_failed:{resp.status_code}:{resp.text[:200]}")
    payload = resp.json() if resp.content else {}
    if not isinstance(payload, dict):
        raise RuntimeError("oauth_refresh_failed:invalid_payload")
    access_token = str(payload.get("access_token", "")).strip()
    expires_in = int(payload.get("expires_in", 0) or 0)
    if not access_token:
        raise RuntimeError("oauth_refresh_failed:missing_access_token")
    return access_token, expires_in


def resolve_drive_access_token(
    *,
    access_token: str | None,
    refresh_token: str | None,
    client_id: str | None,
    client_secret: str | None,
    token_cache_path: str | None,
) -> str | None:
    if access_token:
        return access_token

    cache_path = Path(token_cache_path) if token_cache_path else None
    if cache_path is not None:
        cache = _read_token_cache(cache_path)
        token = str(cache.get("access_token", "")).strip()
        expires_at = int(cache.get("expires_at", 0) or 0)
        if token and expires_at > int(time.time()) + 30:
            return token

    if refresh_token and client_id and client_secret:
        fresh_token, expires_in = refresh_access_token(
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
        )
        if cache_path is not None:
            _write_token_cache(
                cache_path,
                {
                    "access_token": fresh_token,
                    "expires_at": int(time.time()) + max(0, int(expires_in)),
                },
            )
        return fresh_token

    return None

