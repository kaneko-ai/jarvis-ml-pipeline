"""Personal configuration loader for ops_extract daily operations."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


_REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_PERSONAL_CONFIG: dict[str, Any] = {
    "logs_root": "logs",
    "runs_dir": "logs/runs",
    "queue_dir": "logs/sync_queue",
    "dashboard_default_mode": "personal",
    "dashboard_autofollow_latest": True,
    "drive_token_cache": "~/.config/javis/drive_token.json",
    "drive_default_root_folder": "",
    "paper_counter_path": "logs/counters/papers.json",
}

_ENV_MAP = {
    "logs_root": "JAVIS_LOGS_ROOT",
    "runs_dir": "JAVIS_RUNS_DIR",
    "queue_dir": "JAVIS_QUEUE_DIR",
    "dashboard_default_mode": "JAVIS_DASHBOARD_MODE",
    "dashboard_autofollow_latest": "JAVIS_DASHBOARD_AUTOFOLLOW",
    "drive_token_cache": "JAVIS_DRIVE_TOKEN_CACHE",
    "drive_default_root_folder": "JAVIS_DRIVE_ROOT_FOLDER",
    "paper_counter_path": "JAVIS_PAPER_COUNTER_PATH",
}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _parse_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    raw = str(value).strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return default


def _resolve_path(value: str, *, repo_root: Path) -> str:
    text = str(value).strip()
    if not text:
        return text
    expanded = Path(text).expanduser()
    if expanded.is_absolute():
        return str(expanded)
    return str((repo_root / expanded).resolve())


def load_personal_config(*, repo_root: Path | None = None) -> dict[str, Any]:
    """Load personal config with precedence: defaults < repo < home < env."""
    repo_root = repo_root or _REPO_ROOT
    cfg = dict(DEFAULT_PERSONAL_CONFIG)

    repo_cfg = _read_json(repo_root / "config" / "javis.json")
    cfg.update(repo_cfg)

    home_cfg = _read_json(Path("~/.config/javis/config.json").expanduser())
    cfg.update(home_cfg)

    for key, env_name in _ENV_MAP.items():
        value = os.getenv(env_name)
        if value is None:
            continue
        cfg[key] = value

    cfg["dashboard_autofollow_latest"] = _parse_bool(
        cfg.get("dashboard_autofollow_latest"),
        bool(DEFAULT_PERSONAL_CONFIG["dashboard_autofollow_latest"]),
    )

    for key in ("logs_root", "runs_dir", "queue_dir", "paper_counter_path", "drive_token_cache"):
        cfg[key] = _resolve_path(str(cfg.get(key, "")), repo_root=repo_root)

    cfg["drive_default_root_folder"] = str(cfg.get("drive_default_root_folder", "")).strip()
    cfg["dashboard_default_mode"] = str(
        cfg.get("dashboard_default_mode", DEFAULT_PERSONAL_CONFIG["dashboard_default_mode"])
    ).strip() or str(DEFAULT_PERSONAL_CONFIG["dashboard_default_mode"])
    return cfg
