"""Jarvis Repro.

Per RP-165, replays a run for reproduction.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class ReproConfig:
    """Configuration for reproduction run."""

    run_id: str
    original_config: Dict[str, Any]
    original_inputs: Dict[str, Any]
    index_id: Optional[str]
    seed: int


def load_run_config(run_id: str, runs_dir: str = "data/runs") -> Optional[ReproConfig]:
    """Load run configuration for reproduction.

    Args:
        run_id: Run ID to reproduce.
        runs_dir: Runs directory.

    Returns:
        ReproConfig if found, None otherwise.
    """
    run_path = Path(runs_dir) / run_id

    if not run_path.exists():
        return None

    # Load config
    config_path = run_path / "run_config.json"
    if not config_path.exists():
        return None

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Load inputs
    inputs_path = run_path / "inputs.json"
    inputs = {}
    if inputs_path.exists():
        with open(inputs_path, "r", encoding="utf-8") as f:
            inputs = json.load(f)

    return ReproConfig(
        run_id=run_id,
        original_config=config,
        original_inputs=inputs,
        index_id=config.get("index_id"),
        seed=config.get("seed", 42),
    )


def repro_run(
    run_id: str,
    runs_dir: str = "data/runs",
    output_dir: Optional[str] = None,
) -> dict:
    """Reproduce a run.

    Args:
        run_id: Run ID to reproduce.
        runs_dir: Runs directory.
        output_dir: Output directory (default: new run in runs_dir).

    Returns:
        Result dict with new run_id and comparison.
    """
    config = load_run_config(run_id, runs_dir)
    if config is None:
        return {"error": f"Run {run_id} not found"}

    # Create new run ID
    import uuid

    new_run_id = f"repro_{run_id}_{str(uuid.uuid4())[:8]}"

    # Set up repro run
    from jarvis_core.runtime.seed import enforce_seed

    enforce_seed(config.seed)

    result = {
        "original_run_id": run_id,
        "repro_run_id": new_run_id,
        "seed": config.seed,
        "config_restored": True,
    }

    # TODO: Actually execute the run with restored config
    # This is a placeholder for the full implementation

    return result


def compare_runs(run_id_1: str, run_id_2: str, runs_dir: str = "data/runs") -> dict:
    """Compare two runs for reproduction validation.

    Args:
        run_id_1: First run ID.
        run_id_2: Second run ID.
        runs_dir: Runs directory.

    Returns:
        Comparison dict with differences.
    """

    def load_summary(run_id: str) -> Optional[dict]:
        path = Path(runs_dir) / run_id / "summary.json"
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return None

    summary1 = load_summary(run_id_1)
    summary2 = load_summary(run_id_2)

    if not summary1 or not summary2:
        return {"error": "Could not load summaries"}

    # Compare key metrics
    differences = []

    keys = ["status", "claims_count", "citations_count"]
    for key in keys:
        v1 = summary1.get(key)
        v2 = summary2.get(key)
        if v1 != v2:
            differences.append(
                {
                    "key": key,
                    "run1": v1,
                    "run2": v2,
                }
            )

    return {
        "run_id_1": run_id_1,
        "run_id_2": run_id_2,
        "identical": len(differences) == 0,
        "differences": differences,
    }
