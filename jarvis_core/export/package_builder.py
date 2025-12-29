"""Package builder that includes QA reports."""
from __future__ import annotations

from pathlib import Path
import shutil


def build_submission_package(run_dir: Path, output_dir: Path) -> Path:
    """Copy run artifacts and QA report into a submission package directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for item in run_dir.iterdir():
        target = output_dir / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
    qa_dir = Path("data/runs") / run_dir.name / "qa"
    if qa_dir.exists():
        dest = output_dir / "qa"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(qa_dir, dest)
    return output_dir
