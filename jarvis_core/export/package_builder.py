"""Build export packages for run artifacts."""
from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from jarvis_core.notes.note_generator import generate_notes
from jarvis_core.notebooklm.podcast_prompt import generate_notebooklm_outputs
from jarvis_core.zotero.bibtex_export import export_bibtex
from jarvis_core.notes.templates import TEMPLATE_VERSION


def _write_manifest(
    run_id: str,
    output_dir: Path,
    generated: Dict[str, Any],
) -> Path:
    manifest = {
        "run_id": run_id,
        "manifest_version": "p4-1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "template_versions": {
            "obsidian": TEMPLATE_VERSION,
        },
        "generated_outputs": generated,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def _zip_dir(source_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in source_dir.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(source_dir))


def _copy_logs(run_id: str, output_dir: Path, source_runs_dir: Path) -> Optional[Path]:
    events_path = source_runs_dir / run_id / "events.jsonl"
    if not events_path.exists():
        return None
    logs_dir = output_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    dest = logs_dir / "events_excerpt.jsonl"
    with open(events_path, "r", encoding="utf-8") as src, open(dest, "w", encoding="utf-8") as dst:
        lines = [line for line in src if line.strip()]
        for line in lines[-500:]:
            dst.write(line)
    return dest


def build_run_package(
    run_id: str,
    *,
    source_runs_dir: Path = Path("logs/runs"),
    output_base_dir: Path = Path("data/runs"),
    generate_notes: bool = True,
    generate_notebooklm: bool = False,
    export_bibtex_flag: bool = True,
    package_zip: bool = True,
) -> Dict[str, Any]:
    """Generate P4 outputs and package for a run."""
    output_dir = output_base_dir / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    generated: Dict[str, Any] = {
        "notes": None,
        "notebooklm": None,
        "zotero": None,
        "research_rank": None,
        "logs": None,
    }

    if generate_notes:
        notes_meta = generate_notes(run_id, source_runs_dir, output_base_dir)
        generated["notes"] = notes_meta
        generated["research_rank"] = str(output_dir / "research_rank.json")

    if generate_notebooklm:
        notebook_meta = generate_notebooklm_outputs(run_id, source_runs_dir, output_base_dir)
        generated["notebooklm"] = notebook_meta

    if export_bibtex_flag:
        bib_path = export_bibtex(run_id, source_runs_dir, output_base_dir)
        generated["zotero"] = bib_path

    log_path = _copy_logs(run_id, output_dir, source_runs_dir)
    if log_path:
        generated["logs"] = str(log_path)

    manifest_path = _write_manifest(run_id, output_dir, generated)

    if package_zip:
        export_dir = output_dir / "export"
        export_dir.mkdir(parents=True, exist_ok=True)
        zip_path = export_dir / f"jarvis_run_{run_id}.zip"
        temp_dir = output_dir / "_package_temp"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Copy required artifacts
        for name in ["manifest.json", "notes", "notebooklm", "zotero", "research_rank.json", "claims", "logs"]:
            path = output_dir / name
            if path.exists():
                dest = temp_dir / name
                if path.is_dir():
                    shutil.copytree(path, dest)
                else:
                    shutil.copy(path, dest)
        _zip_dir(temp_dir, zip_path)
        shutil.rmtree(temp_dir)
        generated["package"] = str(zip_path)

    generated["manifest"] = str(manifest_path)
    return generated
