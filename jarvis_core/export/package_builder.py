"""Package builder for decision reports."""
from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Dict


def build_decision_package(report_files: Dict[str, Path], output_dir: Path) -> Path:
    """Package decision report files into a zip archive."""
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / "decision_report.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for name, path in report_files.items():
            zip_file.write(path, arcname=path.name)

    return zip_path
