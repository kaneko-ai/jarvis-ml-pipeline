from __future__ import annotations

from pathlib import Path

from jarvis_core.analysis.knowledge_graph import KnowledgeGraph


def test_knowledge_graph_add_link_neighbors_and_stats() -> None:
    kg = KnowledgeGraph()
    p = kg.add_paper("p1", "Paper 1", year=2025)
    c = kg.add_concept("Tumor Microenvironment")
    cl = kg.add_claim("cl1", "Claim text is long enough", score=0.7)

    assert p.id == "p1"
    assert c.id.startswith("concept:")
    assert cl.label.startswith("Claim text")

    kg.link_paper_concept("p1", "Tumor Microenvironment", weight=0.8)
    kg.link_papers("p1", "p2")
    kg.link_claim_evidence("cl1", "ev1")

    neighbors = kg.get_neighbors("p1")
    assert any(n[0] == c.id for n in neighbors)

    stats = kg.stats()
    assert stats["total_nodes"] >= 3
    assert stats["total_edges"] == 3
    assert stats["node_types"]["paper"] == 1


def test_knowledge_graph_subgraph_save_load_and_networkx(
    tmp_path: Path, monkeypatch
) -> None:  # noqa: ANN001
    kg = KnowledgeGraph()
    kg.add_node("n1", "N1", "concept")
    kg.add_node("n2", "N2", "paper")
    kg.add_edge("n1", "n2", "mentions", 0.5)

    sub = kg.get_subgraph({"n1", "n2"})
    assert set(sub.nodes.keys()) == {"n1", "n2"}
    assert len(sub.edges) == 1

    path = tmp_path / "kg.json"
    kg.save(str(path))

    loaded = KnowledgeGraph()
    loaded.load(str(path))
    assert set(loaded.nodes.keys()) == {"n1", "n2"}
    assert len(loaded.edges) == 1

    class _FakeDiGraph:
        def __init__(self) -> None:
            self.nodes = []
            self.edges = []

        def add_node(self, node_id, **kwargs):  # noqa: ANN001
            self.nodes.append((node_id, kwargs))

        def add_edge(self, source, target, **kwargs):  # noqa: ANN001
            self.edges.append((source, target, kwargs))

    class _FakeNx:
        DiGraph = _FakeDiGraph

    monkeypatch.setitem(__import__("sys").modules, "networkx", _FakeNx())
    nx_graph = loaded.to_networkx()
    assert nx_graph is not None
    assert len(nx_graph.nodes) == 2
    assert len(nx_graph.edges) == 1

    monkeypatch.delitem(__import__("sys").modules, "networkx", raising=False)
    assert loaded.to_networkx() is None
