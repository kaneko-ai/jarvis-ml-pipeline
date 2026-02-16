from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from jarvis_cli import main
from jarvis_core.storage import RunStore


def test_cli_papers_tree_offline_generates_bundle(tmp_path: Path):
    out_dir = tmp_path / "runs"
    run_id = "tree_offline_run"

    with (
        patch(
            "sys.argv",
            [
                "jarvis_cli.py",
                "--offline",
                "papers",
                "tree",
                "--id",
                "arxiv:dummy",
                "--out",
                str(out_dir),
                "--out-run",
                run_id,
            ],
        ),
        patch("jarvis_core.ui.status.get_status_banner", return_value="Offline Mode"),
    ):
        main()

    run_dir = out_dir / run_id
    assert run_dir.exists()
    for artifact in RunStore.REQUIRED_ARTIFACTS:
        assert (run_dir / artifact).exists(), f"missing artifact: {artifact}"

    result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    assert result["status"] in {"success", "failed", "needs_retry"}
    assert result["status"] != "success"
