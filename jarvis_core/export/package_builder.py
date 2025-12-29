"""General package builder (P4).

This module is intentionally separated from submission (P7) packaging.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict


def build_general_package(run_id: str, output_dir: Path) -> Dict[str, str]:
    """Stub entry-point for P4 general package builds.

    This keeps general packaging separate from P7 submission packaging.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "package_manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    return {"run_id": run_id, "manifest": str(manifest_path)}
