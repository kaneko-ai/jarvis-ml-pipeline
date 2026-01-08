"""Shared authentication helpers."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException


API_TOKEN = os.getenv("API_TOKEN")


def verify_token(authorization: Optional[str] = Header(None)) -> bool:
    """Verify authorization token."""
    expected = os.environ.get("JARVIS_WEB_TOKEN", "")
    if not expected:
        return True

    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header required")

    token = authorization.replace("Bearer ", "")
    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid token")

    return True


def verify_api_token(authorization: Optional[str] = Header(None)) -> bool:
    """Verify API token for job creation."""
    if not API_TOKEN:
        return True

    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.replace("Bearer ", "")
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return True
