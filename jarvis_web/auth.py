"""Shared authentication helpers."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException


API_TOKEN = os.getenv("API_TOKEN")


def verify_token(authorization: Optional[str] = Header(None)) -> bool:
    """Verify authorization token."""
    from jarvis_web.config import get_config

    config = get_config()

    if config.security.auth_mode == "disabled":
        return True

    expected = os.environ.get("JARVIS_WEB_TOKEN", "")
    if not expected:
        # Default to fail if no token is configured but auth is required
        raise HTTPException(status_code=500, detail="JARVIS_WEB_TOKEN not configured")

    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header required")

    token = authorization.replace("Bearer ", "")
    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid token")

    return True


def verify_api_token(authorization: Optional[str] = Header(None)) -> bool:
    """Verify API token for job creation."""
    from jarvis_web.config import get_config

    config = get_config()

    if config.security.auth_mode == "disabled":
        return True

    if not API_TOKEN:
        raise HTTPException(status_code=500, detail="API_TOKEN not configured")

    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.replace("Bearer ", "")
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return True
