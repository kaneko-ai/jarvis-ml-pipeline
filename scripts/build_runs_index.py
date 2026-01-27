"""Script to rebuild runs/index.json from existing summary.json files (Phase 17)."""

import json
import logging
from pathlib import Path
from jarvis_core.security.atomic_io import atomic_write_json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("build_runs_index")


def rebuild_index(runs_dir: Path):
    """Scan runs_dir and build index.json from summary.json files."""
    runs_dir = Path(runs_dir)
    index = {}

    if not runs_dir.exists():
        logger.error(f"Runs directory {runs_dir} does not exist.")
        return

    # Scan directories
    for run_dir in runs_dir.iterdir():
        if not run_dir.is_dir():
            continue

        summary_path = run_dir / "summary.json"
        if summary_path.exists():
            try:
                with open(summary_path, "r", encoding="utf-8") as f:
                    summary = json.load(f)

                run_id = summary.get("run_id", run_dir.name)
                index[run_id] = {
                    "status": summary.get("status"),
                    "started_at": summary.get("started_at"),
                    "finished_at": summary.get("finished_at"),
                    "schema_version": summary.get("schema_version", "v1"),
                }
                logger.debug(f"Indexed {run_id}")
            except Exception as e:
                logger.warning(f"Failed to index {run_dir.name}: {e}")

    index_path = runs_dir / "index.json"
    atomic_write_json(index_path, index)
    logger.info(f"Rebuilt index.json with {len(index)} entries at {index_path}")


if __name__ == "__main__":
    import sys

    # Default to data/runs if not specified
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "data/runs"
    rebuild_index(Path(target_dir))
