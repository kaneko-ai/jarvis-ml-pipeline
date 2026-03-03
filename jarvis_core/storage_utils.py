"""Storage path utilities for JARVIS Research OS.

Reads config.yaml storage section and returns resolved paths.
Falls back to local 'logs' directory if H: drive is unavailable.
"""
from __future__ import annotations

from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


def _load_storage_config() -> dict:
    """Load storage section from config.yaml."""
    try:
        import yaml
        cfg = yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8"))
        return cfg.get("storage", {})
    except Exception:
        return {}


def get_logs_dir(subdir: str = "") -> Path:
    """Return logs directory, with optional subdirectory.

    Uses config.yaml storage.logs_dir if available and accessible.
    Falls back to local 'logs' directory.
    """
    sc = _load_storage_config()
    primary = sc.get("logs_dir", "logs")
    fallback = sc.get("local_fallback", "logs")

    p = Path(primary)
    if subdir:
        p = p / subdir

    try:
        p.mkdir(parents=True, exist_ok=True)
        # Verify writable
        test_file = p / ".jarvis_write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        return p
    except Exception:
        fb = Path(fallback)
        if subdir:
            fb = fb / subdir
        fb.mkdir(parents=True, exist_ok=True)
        return fb


def get_exports_dir(subdir: str = "") -> Path:
    """Return exports directory."""
    sc = _load_storage_config()
    primary = sc.get("exports_dir", "exports")
    fallback = sc.get("local_fallback", "logs")

    p = Path(primary)
    if subdir:
        p = p / subdir

    try:
        p.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        fb = Path(fallback)
        if subdir:
            fb = fb / subdir
        fb.mkdir(parents=True, exist_ok=True)
        return fb


def get_pdf_archive_dir() -> Path:
    """Return PDF archive directory."""
    sc = _load_storage_config()
    primary = sc.get("pdf_archive_dir", "pdf-archive")
    fallback = sc.get("local_fallback", "logs")

    p = Path(primary)
    try:
        p.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        fb = Path(fallback) / "pdf-archive"
        fb.mkdir(parents=True, exist_ok=True)
        return fb
