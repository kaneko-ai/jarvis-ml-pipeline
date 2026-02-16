"""Runners for `jarvis papers tree` and `jarvis papers map3d`."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from jarvis_core.bundle import BundleAssembler
from jarvis_core.network.degradation import DegradationLevel, get_degradation_manager

from .citation_tree import build_tree
from .ids import normalize_paper_id
from .map3d import build_map_points
from .render import write_map_outputs, write_tree_outputs
from .semantic_scholar import fetch_references, fetch_root_and_references


def run_tree(*, paper_id: str, depth: int, max_per_level: int, out: str, out_run: str) -> dict:
    run_id = _resolve_run_id(out_run)
    run_dir = Path(out) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    assembler = BundleAssembler(run_dir)

    offline = _is_offline()
    warnings: list[dict] = []
    fail_reasons: list[dict] = []
    root = None
    nodes: list[dict] = []
    edges: list[dict] = []

    try:
        normalized = normalize_paper_id(paper_id)
        fetch = fetch_root_and_references(
            s2_id=normalized.s2_lookup_id,
            max_refs=max_per_level,
            offline=offline,
        )
        root = fetch.paper
        warnings.extend(fetch.warnings)
        if root:
            tree = build_tree(
                root=root,
                depth=depth,
                max_per_level=max_per_level,
                fetch_refs=lambda pid, limit: fetch_references(
                    paper_id=pid, max_refs=limit, offline=offline
                ),
            )
            nodes = tree.nodes
            edges = tree.edges
            warnings.extend(tree.warnings)
        else:
            fail_reasons.append(
                {
                    "code": "PAPER_ID_RESOLVE_FAILED",
                    "msg": f"Unable to resolve paper id: {paper_id}",
                    "severity": "warning",
                }
            )
    except ValueError as exc:
        fail_reasons.append({"code": "INPUT_INVALID", "msg": str(exc), "severity": "error"})
    except Exception as exc:
        fail_reasons.append({"code": "INTERNAL_ERROR", "msg": str(exc), "severity": "error"})

    tree_dir = run_dir / "paper_graph" / "tree"
    write_tree_outputs(tree_dir, nodes=nodes, edges=edges)

    gate_passed = len(nodes) > 1 and not _has_fatal(fail_reasons)
    if offline:
        fail_reasons.append(
            {
                "code": "OFFLINE_MODE",
                "msg": "Offline mode prevents network fetch.",
                "severity": "warning",
            }
        )
        gate_passed = False
    if not gate_passed and not fail_reasons:
        fail_reasons.append(
            {
                "code": "GRAPH_BUILD_INCOMPLETE",
                "msg": "Citation tree was not completed.",
                "severity": "warning",
            }
        )

    context = _context(run_id=run_id, goal=f"papers tree {paper_id}", pipeline="paper_graph.tree")
    artifacts = {
        "papers": [_paper_as_record(n) for n in nodes],
        "claims": [],
        "evidence": [],
        "scores": {"features": {"node_count": len(nodes)}, "rankings": []},
        "answer": f"Citation tree generated with {len(nodes)} nodes and {len(edges)} edges.",
        "citations": [],
        "warnings": warnings,
    }
    assembler.build(
        context,
        artifacts,
        quality_report={"gate_passed": gate_passed, "fail_reasons": fail_reasons},
    )
    return _load_result(run_dir, run_id)


def run_map3d(*, paper_id: str, k_neighbors: int, seed: int, out: str, out_run: str) -> dict:
    run_id = _resolve_run_id(out_run)
    run_dir = Path(out) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    assembler = BundleAssembler(run_dir)

    offline = _is_offline()
    warnings: list[dict] = []
    fail_reasons: list[dict] = []
    points: list[dict] = []
    map_config: dict = {"embedding_method": "none", "seed": seed}

    try:
        normalized = normalize_paper_id(paper_id)
        fetch = fetch_root_and_references(
            s2_id=normalized.s2_lookup_id,
            max_refs=max(10, min(50, k_neighbors)),
            offline=offline,
        )
        warnings.extend(fetch.warnings)
        if not fetch.paper:
            fail_reasons.append(
                {
                    "code": "PAPER_ID_RESOLVE_FAILED",
                    "msg": f"Unable to resolve paper id: {paper_id}",
                    "severity": "warning",
                }
            )
        else:
            map_result = build_map_points(
                center_paper=fetch.paper,
                neighbor_papers=fetch.references,
                k_neighbors=max(10, min(50, k_neighbors)),
                seed=seed,
            )
            points = map_result.points
            map_config = map_result.config
            warnings.extend(map_result.warnings)
    except ValueError as exc:
        fail_reasons.append({"code": "INPUT_INVALID", "msg": str(exc), "severity": "error"})
    except Exception as exc:
        fail_reasons.append({"code": "INTERNAL_ERROR", "msg": str(exc), "severity": "error"})

    map_dir = run_dir / "paper_graph" / "map3d"
    write_map_outputs(
        map_dir,
        points=points,
        config=map_config,
        warnings=warnings,
        plot_html=not offline,
    )

    gate_passed = len(points) >= 2 and not _has_fatal(fail_reasons)
    if offline:
        fail_reasons.append(
            {
                "code": "OFFLINE_MODE",
                "msg": "Offline mode prevents network fetch.",
                "severity": "warning",
            }
        )
        gate_passed = False
    if not gate_passed and not fail_reasons:
        fail_reasons.append(
            {
                "code": "MAP3D_INCOMPLETE",
                "msg": "3D map generation did not produce enough points.",
                "severity": "warning",
            }
        )

    context = _context(run_id=run_id, goal=f"papers map3d {paper_id}", pipeline="paper_graph.map3d")
    rankings = [
        {"paper_id": p["paper_id"], "distance_to_center": p["distance_to_center"]}
        for p in sorted(points[1:], key=lambda x: x["distance_to_center"])[:10]
    ]
    artifacts = {
        "papers": [
            {"paper_id": p["paper_id"], "title": p["title"], "year": p.get("year", 0)}
            for p in points
        ],
        "claims": [],
        "evidence": [],
        "scores": {"features": {"point_count": len(points)}, "rankings": rankings},
        "answer": f"3D map generated with {len(points)} points.",
        "citations": [],
        "warnings": warnings,
    }
    assembler.build(
        context,
        artifacts,
        quality_report={"gate_passed": gate_passed, "fail_reasons": fail_reasons},
    )
    return _load_result(run_dir, run_id)


def _resolve_run_id(out_run: str) -> str:
    if out_run and out_run != "auto":
        return out_run
    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{now}_{uuid.uuid4().hex[:8]}"


def _context(*, run_id: str, goal: str, pipeline: str) -> dict:
    return {
        "run_id": run_id,
        "task_id": run_id,
        "goal": goal,
        "query": goal,
        "pipeline": pipeline,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": 42,
        "model": "feature-runner",
    }


def _is_offline() -> bool:
    return get_degradation_manager().get_level() == DegradationLevel.OFFLINE


def _has_fatal(fail_reasons: list[dict]) -> bool:
    return any(
        str(reason.get("code", "")).upper() in BundleAssembler.FATAL_FAIL_CODES
        for reason in fail_reasons
    )


def _paper_as_record(node: dict) -> dict:
    return {
        "paper_id": node.get("node_id"),
        "title": node.get("title", ""),
        "year": node.get("year", 0),
    }


def _load_result(run_dir: Path, run_id: str) -> dict:
    result_path = run_dir / "result.json"
    status = "needs_retry"
    if result_path.exists():
        try:
            status = str(
                json.loads(result_path.read_text(encoding="utf-8")).get("status", "needs_retry")
            )
        except Exception:
            status = "needs_retry"
    return {"run_id": run_id, "run_dir": str(run_dir), "status": status}
