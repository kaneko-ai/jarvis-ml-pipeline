"""Rendering helpers for paper graph outputs."""

from __future__ import annotations

import json
from pathlib import Path


def write_tree_outputs(tree_dir: Path, *, nodes: list[dict], edges: list[dict]) -> None:
    tree_dir.mkdir(parents=True, exist_ok=True)
    (tree_dir / "graph.json").write_text(
        json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = ["# Citation Tree", "", f"- Nodes: {len(nodes)}", f"- Edges: {len(edges)}", ""]
    for node in nodes[:50]:
        lines.append(f"- L{node.get('level', 0)} | {node.get('node_id')} | {node.get('title', '')}")
    (tree_dir / "tree.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    mermaid = ["```mermaid", "graph TD"]
    for edge in edges[:300]:
        src = _safe(edge.get("from_node_id", "src"))
        dst = _safe(edge.get("to_node_id", "dst"))
        mermaid.append(f"  {src} --> {dst}")
    mermaid.append("```")
    (tree_dir / "tree.mermaid.md").write_text("\n".join(mermaid) + "\n", encoding="utf-8")

    summary = ["# Citation Tree Summary", ""]
    hubs = sorted(nodes, key=lambda n: n.get("inbound_cites", 0), reverse=True)[:10]
    summary.append("## Hub Nodes")
    for hub in hubs:
        summary.append(f"- {hub.get('title', '')} ({hub.get('inbound_cites', 0)})")
    summary.extend(
        ["", "## Story Gaps", "- Additional source acquisition required for missing refs."]
    )
    (tree_dir / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")


def write_map_outputs(
    map_dir: Path, *, points: list[dict], config: dict, warnings: list[dict], plot_html: bool
) -> None:
    map_dir.mkdir(parents=True, exist_ok=True)
    (map_dir / "map_points.json").write_text(
        json.dumps(points, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# 3D Paper Map",
        "",
        f"- Points: {len(points)}",
        f"- Embedding: {config.get('embedding_method', 'unknown')}",
        "",
        "## Top Neighbors",
    ]
    sorted_points = sorted(points[1:], key=lambda p: p.get("distance_to_center", 1e9))[:10]
    for point in sorted_points:
        lines.append(
            f"- {point.get('paper_id')} | d={point.get('distance_to_center', 0.0):.3f} | {point.get('title', '')}"
        )
    if warnings:
        lines.extend(["", "## Warnings"])
        for warning in warnings:
            lines.append(f"- [{warning.get('code', 'WARN')}] {warning.get('msg', '')}")
    (map_dir / "map.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    if plot_html:
        _write_plotly_html(map_dir / "map.html", points)


def _write_plotly_html(path: Path, points: list[dict]) -> None:
    try:
        import plotly.graph_objects as go  # type: ignore[import-not-found]
    except Exception:
        return

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=[p.get("x", 0.0) for p in points],
                y=[p.get("y", 0.0) for p in points],
                z=[p.get("z", 0.0) for p in points],
                mode="markers+text",
                text=[p.get("paper_id", "") for p in points],
                marker={"size": 4},
            )
        ]
    )
    fig.update_layout(
        title="Paper Map 3D", scene={"xaxis_title": "X", "yaxis_title": "Y", "zaxis_title": "Z"}
    )
    fig.write_html(str(path), include_plotlyjs="cdn")


def _safe(value: str) -> str:
    text = "".join(ch if ch.isalnum() else "_" for ch in str(value))
    if text and text[0].isdigit():
        return f"n_{text}"
    return text or "n"
