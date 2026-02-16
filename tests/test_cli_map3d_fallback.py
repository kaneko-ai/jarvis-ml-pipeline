from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from jarvis_cli import main


def test_cli_map3d_generates_points_with_fallback(tmp_path: Path, monkeypatch):
    out_dir = tmp_path / "runs"
    run_id = "map3d_run"

    root_paper = {
        "paperId": "root1",
        "title": "Root paper",
        "abstract": "center abstract",
        "year": 2024,
        "citationCount": 10,
        "externalIds": {"ArXiv": "1234.5678"},
    }
    refs = [
        {
            "paperId": f"p{i}",
            "title": f"Neighbor {i}",
            "abstract": f"abstract {i}",
            "year": 2020 + i,
            "citationCount": i,
            "externalIds": {},
        }
        for i in range(1, 6)
    ]

    monkeypatch.setattr(
        "jarvis_core.paper_graph.runner.fetch_root_and_references",
        lambda **kwargs: SimpleNamespace(paper=root_paper, references=refs, warnings=[]),
    )

    with patch(
        "sys.argv",
        [
            "jarvis_cli.py",
            "papers",
            "map3d",
            "--id",
            "arxiv:1234.5678",
            "--k",
            "5",
            "--out",
            str(out_dir),
            "--out-run",
            run_id,
        ],
    ):
        main()

    map_points_path = out_dir / run_id / "paper_graph" / "map3d" / "map_points.json"
    assert map_points_path.exists()
    points = json.loads(map_points_path.read_text(encoding="utf-8"))
    assert len(points) >= 2
    assert points[0]["x"] == 0.0
    assert points[0]["y"] == 0.0
    assert points[0]["z"] == 0.0
