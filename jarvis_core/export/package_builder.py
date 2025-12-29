"""Package builder for run outputs including writing drafts."""
from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Optional


def build_run_package(run_id: str, output_path: Optional[Path] = None) -> Path:
    run_dir = Path("data/runs") / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    if output_path is None:
        output_path = run_dir / "package.zip"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for path in run_dir.rglob("*"):
            if path.is_file() and path != output_path:
                zipf.write(path, path.relative_to(run_dir))

    return output_path
