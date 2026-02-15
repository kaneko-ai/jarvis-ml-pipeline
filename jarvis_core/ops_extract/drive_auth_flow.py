"""Local OAuth flow helper for Google Drive personal setup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _extract_client_info(client_secrets_path: Path) -> tuple[str, str]:
    payload = _read_json(client_secrets_path)
    if not payload:
        return "", ""
    installed = payload.get("installed")
    if not isinstance(installed, dict):
        installed = payload.get("web")
    if not isinstance(installed, dict):
        return "", ""
    client_id = str(installed.get("client_id", "")).strip()
    client_secret = str(installed.get("client_secret", "")).strip()
    return client_id, client_secret


def run_local_oauth_flow(
    *,
    client_secrets_path: str | Path,
    scopes: list[str] | None,
    token_cache_path: str | Path,
) -> dict[str, Any]:
    """Run installed-app OAuth flow and persist refresh-capable token payload."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except Exception as exc:  # pragma: no cover - optional dependency guard
        raise RuntimeError("drive_auth_extras_missing:google-auth-oauthlib") from exc

    client_path = Path(client_secrets_path).expanduser()
    if not client_path.exists():
        raise FileNotFoundError(f"client_secrets_not_found:{client_path}")
    selected_scopes = scopes or list(DEFAULT_DRIVE_SCOPES)

    flow = InstalledAppFlow.from_client_secrets_file(str(client_path), scopes=selected_scopes)
    creds = flow.run_local_server(port=0, open_browser=True)

    client_id = str(getattr(creds, "client_id", "") or "").strip()
    client_secret = str(getattr(creds, "client_secret", "") or "").strip()
    if not client_id or not client_secret:
        fallback_id, fallback_secret = _extract_client_info(client_path)
        client_id = client_id or fallback_id
        client_secret = client_secret or fallback_secret

    refresh_token = str(getattr(creds, "refresh_token", "") or "").strip()
    access_token = str(getattr(creds, "token", "") or "").strip()
    token_payload = {
        "schema_version": "1",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "access_token": access_token,
        "expires_at": 0,
        "scopes": selected_scopes,
    }

    cache_path = Path(token_cache_path).expanduser()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(token_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return token_payload
