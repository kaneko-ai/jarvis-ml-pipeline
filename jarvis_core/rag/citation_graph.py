"""Citation network builder and visualizer for JARVIS Research OS.

Uses networkx to build paper citation graphs.
Outputs Mermaid diagrams and Obsidian-compatible markdown.
"""
from __future__ import annotations

import json
import networkx as nx
from pathlib import Path
from typing import Optional


def _stringify(val):
    """Convert any value to a GraphML-safe string."""
    if val is None:
        return ""
    if isinstance(val, (list, dict)):
        return json.dumps(val, ensure_ascii=False)
    return str(val)


class CitationGraph:
    """Build and query a citation network from JARVIS paper data."""

    def __init__(self):
        self.G = nx.DiGraph()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def add_papers(self, papers: list[dict]) -> int:
        """Add papers as nodes. Returns count of nodes added."""
        added = 0
        for p in papers:
            pid = p.get("doi") or p.get("pmid") or p.get("title", "unknown")
            pid = str(pid)
            if pid in self.G:
                continue
            self.G.add_node(pid, **{
                "title": _stringify(p.get("title", "")),
                "year": _stringify(p.get("year", "")),
                "authors": _stringify(p.get("authors", "")),
                "source": _stringify(p.get("source", "")),
                "score": _stringify(p.get("score", 0)),
                "evidence_level": _stringify(p.get("evidence_level", "")),
            })
            added += 1
        return added

    def add_citation(self, from_id: str, to_id: str):
        """Add a directed citation edge: from_id cites to_id."""
        if from_id not in self.G:
            self.G.add_node(from_id, title=from_id)
        if to_id not in self.G:
            self.G.add_node(to_id, title=to_id)
        self.G.add_edge(from_id, to_id)

    def add_citations_from_s2(self, papers: list[dict]) -> int:
        """Add citation edges from Semantic Scholar reference data.

        Each paper dict may contain 'references' (list of DOIs/IDs)
        and 'cited_by' (list of DOIs/IDs).
        """
        edge_count = 0
        for p in papers:
            pid = p.get("doi") or p.get("pmid") or p.get("title", "")
            pid = str(pid)
            for ref in p.get("references", []):
                if isinstance(ref, dict):
                    ref_id = str(ref.get("doi") or ref.get("paperId") or ref.get("title", ""))
                else:
                    ref_id = str(ref)
                if ref_id:
                    self.add_citation(pid, ref_id)
                    edge_count += 1
            for citer in p.get("cited_by", []):
                if isinstance(citer, dict):
                    citer_id = str(citer.get("doi") or citer.get("paperId") or citer.get("title", ""))
                else:
                    citer_id = str(citer)
                if citer_id:
                    self.add_citation(citer_id, pid)
                    edge_count += 1
        return edge_count

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """Return basic graph statistics."""
        if len(self.G) == 0:
            return {"nodes": 0, "edges": 0}
        result = {
            "nodes": self.G.number_of_nodes(),
            "edges": self.G.number_of_edges(),
            "density": round(nx.density(self.G), 4),
        }
        if len(self.G) > 0:
            in_deg = dict(self.G.in_degree())
            top_cited = sorted(in_deg.items(), key=lambda x: x[1], reverse=True)[:5]
            result["top_cited"] = [
                {"id": n, "citations": c, "title": self.G.nodes[n].get("title", n)}
                for n, c in top_cited if c > 0
            ]
            out_deg = dict(self.G.out_degree())
            top_citers = sorted(out_deg.items(), key=lambda x: x[1], reverse=True)[:5]
            result["top_citers"] = [
                {"id": n, "refs": c, "title": self.G.nodes[n].get("title", n)}
                for n, c in top_citers if c > 0
            ]
        # Connected components (treat as undirected)
        if len(self.G) > 1:
            ug = self.G.to_undirected()
            result["components"] = nx.number_connected_components(ug)
        return result

    def find_hubs(self, top_n: int = 10) -> list[dict]:
        """Find hub papers by PageRank."""
        if len(self.G) == 0:
            return []
        pr = nx.pagerank(self.G, max_iter=200)
        ranked = sorted(pr.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [
            {
                "id": nid,
                "pagerank": round(score, 6),
                "title": self.G.nodes[nid].get("title", nid),
                "year": self.G.nodes[nid].get("year", ""),
                "in_degree": self.G.in_degree(nid),
                "out_degree": self.G.out_degree(nid),
            }
            for nid, score in ranked
        ]

    def find_clusters(self) -> list[list[str]]:
        """Find clusters using weakly connected components."""
        components = list(nx.weakly_connected_components(self.G))
        components.sort(key=len, reverse=True)
        return [list(c) for c in components]

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _short_label(self, nid: str) -> str:
        """Create a short label for Mermaid nodes."""
        title = self.G.nodes[nid].get("title", nid)
        year = self.G.nodes[nid].get("year", "")
        if len(title) > 40:
            title = title[:37] + "..."
        if year:
            return f"{title} ({year})"
        return title

    def _safe_id(self, nid: str) -> str:
        """Make ID safe for Mermaid."""
        safe = nid.replace("/", "_").replace(".", "_").replace("-", "_")
        safe = safe.replace(" ", "_").replace(":", "_")
        return "n" + safe[:40]

    def to_mermaid(self, max_nodes: int = 30) -> str:
        """Export graph as Mermaid flowchart."""
        lines = ["graph LR"]
        # Limit to top nodes by PageRank if too many
        if len(self.G) > max_nodes:
            pr = nx.pagerank(self.G, max_iter=200)
            top_nodes = set(
                n for n, _ in sorted(pr.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
            )
        else:
            top_nodes = set(self.G.nodes())

        # Add nodes
        for nid in top_nodes:
            safe = self._safe_id(nid)
            label = self._short_label(nid).replace('"', "'")
            lines.append(f'    {safe}["{label}"]')

        # Add edges
        for u, v in self.G.edges():
            if u in top_nodes and v in top_nodes:
                lines.append(f"    {self._safe_id(u)} --> {self._safe_id(v)}")

        return "\n".join(lines)

    def to_obsidian_md(self, title: str = "Citation Network",
                       max_nodes: int = 30) -> str:
        """Export as Obsidian-compatible markdown with Mermaid diagram."""
        stats = self.stats()
        hubs = self.find_hubs(top_n=5)
        mermaid = self.to_mermaid(max_nodes=max_nodes)

        lines = [
            f"# {title}",
            "",
            f"Generated by JARVIS Research OS",
            "",
            "## Statistics",
            "",
            f"- Nodes: {stats.get('nodes', 0)}",
            f"- Edges: {stats.get('edges', 0)}",
            f"- Density: {stats.get('density', 0)}",
            f"- Components: {stats.get('components', 'N/A')}",
            "",
            "## Hub Papers (by PageRank)",
            "",
        ]
        for i, h in enumerate(hubs, 1):
            lines.append(
                f"{i}. **{h['title']}** ({h['year']}) "
                f"— PageRank: {h['pagerank']}, "
                f"Cited by: {h['in_degree']}, Refs: {h['out_degree']}"
            )
        lines.extend([
            "",
            "## Citation Network Diagram",
            "",
            "```mermaid",
            mermaid,
            "```",
            "",
        ])

        # Top cited
        top_cited = stats.get("top_cited", [])
        if top_cited:
            lines.append("## Most Cited Papers")
            lines.append("")
            for tc in top_cited:
                lines.append(f"- **{tc['title']}** — {tc['citations']} citations")
            lines.append("")

        return "\n".join(lines)

    def save(self, output_dir: str, prefix: str = "citation_network") -> dict:
        """Save graph as GraphML, Mermaid, and Obsidian MD."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        paths = {}

        # GraphML (convert all attrs to strings for safety)
        gml_path = out / f"{prefix}.graphml"
        G_safe = self.G.copy()
        for nid in G_safe.nodes():
            for k, v in list(G_safe.nodes[nid].items()):
                G_safe.nodes[nid][k] = _stringify(v)
        for u, v in G_safe.edges():
            for k, val in list(G_safe.edges[u, v].items()):
                G_safe.edges[u, v][k] = _stringify(val)
        nx.write_graphml(G_safe, str(gml_path))
        paths["graphml"] = str(gml_path)

        # Mermaid
        mmd_path = out / f"{prefix}.mmd"
        mmd_path.write_text(self.to_mermaid(), encoding="utf-8")
        paths["mermaid"] = str(mmd_path)

        # Obsidian MD
        md_path = out / f"{prefix}.md"
        md_path.write_text(self.to_obsidian_md(), encoding="utf-8")
        paths["obsidian_md"] = str(md_path)

        # JSON stats
        stats_path = out / f"{prefix}_stats.json"
        stats_path.write_text(
            json.dumps(self.stats(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        paths["stats"] = str(stats_path)

        return paths

    # ------------------------------------------------------------------
    # Load from file
    # ------------------------------------------------------------------

    @classmethod
    def from_json(cls, json_path: str) -> "CitationGraph":
        """Load papers from a JARVIS JSON output file."""
        cg = cls()
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
        papers = data if isinstance(data, list) else data.get("papers", [])
        cg.add_papers(papers)
        cg.add_citations_from_s2(papers)
        return cg

    @classmethod
    def from_graphml(cls, graphml_path: str) -> "CitationGraph":
        """Load from a previously saved GraphML file."""
        cg = cls()
        cg.G = nx.read_graphml(graphml_path)
        return cg
