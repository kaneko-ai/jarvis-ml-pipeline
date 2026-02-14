"""Network profile detection for ops_extract mode."""

from __future__ import annotations

import os
import socket
import time
from typing import Any

import requests

from .contracts import OpsExtractConfig


def detect_network_profile(config: OpsExtractConfig) -> tuple[str, dict[str, Any]]:
    """Detect current network profile and return diagnostics payload."""

    if os.getenv("JARVIS_OPS_EXTRACT_FIXED_TIME"):
        fixed_profile = str(os.getenv("JARVIS_OPS_EXTRACT_FIXED_NETWORK_PROFILE", "ONLINE")).upper()
        if fixed_profile not in {"OFFLINE", "VPN", "ONLINE"}:
            fixed_profile = "ONLINE"
        return fixed_profile, {
            "dns_resolve_ok": True,
            "ping_ok": None,
            "drive_api_reachable": fixed_profile != "OFFLINE",
            "proxy_env": {
                "HTTP_PROXY": False,
                "HTTPS_PROXY": False,
                "NO_PROXY": False,
            },
            "vpn_hint": {"active": fixed_profile == "VPN", "reason": "fixed_time_mode"},
            "errors": [],
            "latency_ms": 0.0,
            "profile": fixed_profile,
        }

    diag: dict[str, Any] = {
        "dns_resolve_ok": False,
        "ping_ok": None,
        "drive_api_reachable": False,
        "proxy_env": {
            "HTTP_PROXY": bool(os.getenv("HTTP_PROXY")),
            "HTTPS_PROXY": bool(os.getenv("HTTPS_PROXY")),
            "NO_PROXY": bool(os.getenv("NO_PROXY")),
        },
        "vpn_hint": {
            "active": bool(os.getenv("VPN") or os.getenv("VPN_ENABLED")),
            "reason": "env_hint",
        },
        "errors": [],
        "latency_ms": None,
    }

    try:
        socket.gethostbyname("www.googleapis.com")
        diag["dns_resolve_ok"] = True
    except Exception as exc:
        diag["errors"].append(f"dns_resolve_failed:{exc}")

    api_base = (config.drive_api_base_url or "https://www.googleapis.com/drive/v3").rstrip("/")
    probe_url = f"{api_base}/about"
    started = time.perf_counter()
    try:
        resp = requests.get(
            probe_url,
            params={"fields": "user"},
            timeout=3.0,
        )
        # 200/401/403 means endpoint is reachable at network layer.
        diag["drive_api_reachable"] = resp.status_code in {200, 401, 403}
    except Exception as exc:
        diag["errors"].append(f"drive_probe_failed:{exc}")
    finally:
        diag["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)

    if diag["dns_resolve_ok"] and diag["drive_api_reachable"]:
        profile = "ONLINE"
    elif diag["dns_resolve_ok"] and not diag["drive_api_reachable"]:
        profile = "VPN"
    else:
        profile = "OFFLINE"
    diag["profile"] = profile
    return profile, diag
