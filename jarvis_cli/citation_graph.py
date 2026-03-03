"""CLI handler for citation-graph command."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jarvis_core.rag.citation_graph import CitationGraph


def build_parser(sub) -> argparse.ArgumentParser:
    p = sub.add_parser("citation-graph", help="Build and visualize citation network")
    p.add_argument("input", help="JARVIS JSON file with papers")
    p.add_argument("--output-dir", "-o", default=None,
                   help="Output directory (default: logs/citation_graph/)")
    p.add_argument("--obsidian", action="store_true",
                   help="Also copy MD to Obsidian vault")
    p.add_argument("--max-nodes", type=int, default=30,
                   help="Max nodes in Mermaid diagram (default: 30)")
    p.add_argument("--stats-only", action="store_true",
                   help="Print stats without saving files")
    p.set_defaults(func=run)
    return p


def run(args):
    import yaml

    json_path = args.input
    if not Path(json_path).exists():
        print(f"[ERROR] File not found: {json_path}")
        return

    print(f"[citation-graph] Loading papers from {json_path} ...")
    cg = CitationGraph.from_json(json_path)
    stats = cg.stats()

    print(f"[citation-graph] Nodes: {stats['nodes']}, Edges: {stats['edges']}")

    if args.stats_only:
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        return

    # Determine output dir
    if args.output_dir:
        out_dir = args.output_dir
    else:
        try:
            cfg = yaml.safe_load(
                open("config.yaml", "r", encoding="utf-8")
            )
            base = cfg.get("storage", {}).get("logs_dir", "logs")
        except Exception:
            base = "logs"
        out_dir = str(Path(base) / "citation_graph")

    print(f"[citation-graph] Saving to {out_dir} ...")
    paths = cg.save(out_dir, prefix="citation_network")

    for kind, path in paths.items():
        print(f"  {kind}: {path}")

    # Hub papers
    hubs = cg.find_hubs(top_n=5)
    if hubs:
        print("\n[citation-graph] Hub Papers (PageRank):")
        for i, h in enumerate(hubs, 1):
            print(f"  {i}. {h['title']} ({h['year']}) "
                  f"PR={h['pagerank']} in={h['in_degree']} out={h['out_degree']}")

    # Copy to Obsidian
    if args.obsidian:
        try:
            cfg = yaml.safe_load(
                open("config.yaml", "r", encoding="utf-8")
            )
            vault = cfg["obsidian"]["vault_path"]
            notes_folder = cfg["obsidian"].get("notes_folder", "JARVIS/Notes")
            dest = Path(vault) / notes_folder / "citation_network.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            md_content = cg.to_obsidian_md(max_nodes=args.max_nodes)
            dest.write_text(md_content, encoding="utf-8")
            print(f"\n[citation-graph] Obsidian note saved: {dest}")
        except Exception as e:
            print(f"[citation-graph] Obsidian export failed: {e}")

    print("[citation-graph] Done.")
