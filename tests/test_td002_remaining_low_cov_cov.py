from __future__ import annotations

import builtins
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
import requests

from jarvis_core.integrations import obsidian_sync_v2 as obsidian_module
from jarvis_core.reliability import health as health_module
from jarvis_core.retrieval import citation_graph as citation_module
from jarvis_core.scoring import paper_score as paper_score_module
from jarvis_core.sources import base as source_base_module
from jarvis_core.sources import crossref_client as crossref_module
from jarvis_core.sources.registry import SourceRegistry


def test_paper_score_end_to_end_and_tier() -> None:
    paper = {
        "oa_status": "gold",
        "journal": "Nature",
        "year": 2024,
        "title": "Cancer immunotherapy randomized trial",
        "abstract": "Domain oncology and efficacy data",
    }
    claims = [
        {"claim_type": "method", "evidence": [{"score": 0.9}]},
        {"claim_type": "result", "evidence": [{"score": 0.8}]},
    ]
    result = paper_score_module.score_paper(
        paper=paper,
        claims=claims,
        query="immunotherapy randomized trial",
        domain="oncology",
    )
    assert result.score > 0
    assert result.tier in {"A", "B", "C", "S"}
    assert result.to_dict()["breakdown"]["transparency"] >= 20


def test_paper_score_sub_functions_cover_edges() -> None:
    assert paper_score_module._tier(95) == "S"
    assert paper_score_module._tier(82) == "A"
    assert paper_score_module._tier(70) == "B"
    assert paper_score_module._tier(10) == "C"

    tr = paper_score_module._score_transparency(
        {"oa_status": "closed"},
        [{"claim_type": "method"}, {"claim_type": "result"}],
    )
    assert tr == 20.0

    rel = paper_score_module._score_relevance(
        {"title": "alpha", "abstract": "beta"},
        query="gamma",
        domain="delta",
    )
    assert rel == 5.0

    ev = paper_score_module._score_evidence_strength(
        [{"evidence": [{"score": 0.1}]}, {"evidence": []}, {}]
    )
    assert 0.0 <= ev <= 20.0


def test_obsidian_sync_paper_run_and_stats(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class _FixedDateTime:
        @classmethod
        def now(cls):  # noqa: ANN206
            from datetime import datetime

            return datetime(2026, 2, 6, 0, 0, 0)

    monkeypatch.setattr(obsidian_module, "datetime", _FixedDateTime)

    sync = obsidian_module.ObsidianSync(str(tmp_path / "vault"))
    paper = {
        "paper_id": "P1",
        "title": 'Title:*?"<>|/Test',
        "authors": ["A", "B"],
        "year": 2025,
        "source": "pubmed",
        "abstract": "Abstract text",
    }
    claims = [
        {"paper_id": "P1", "claim_type": "result", "claim_text": "Claim A"},
        {"paper_id": "P2", "claim_type": "method", "claim_text": "Ignored"},
    ]
    evidence = [
        {"paper_id": "P1", "source": "pmid:1", "evidence_text": "Evidence A"},
        {"paper_id": "P2", "source": "pmid:2", "evidence_text": "Ignored"},
    ]

    created = sync.sync_paper(paper, claims=claims, evidence=evidence)
    assert created.status == "created"
    unchanged = sync.sync_paper(paper, claims=claims, evidence=evidence)
    assert unchanged.status == "unchanged"

    paper2 = dict(paper)
    paper2["abstract"] = "Updated abstract"
    updated = sync.sync_paper(paper2, claims=claims, evidence=evidence)
    assert updated.status == "updated"

    run_res = sync.sync_run(
        run_id="RUN-1",
        query="query",
        papers=[paper, {"paper_id": "P2", "title": "T2"}],
        claims=claims,
        summary="summary",
    )
    assert run_res.status == "created"

    stats = sync.get_sync_stats()
    assert stats["papers_synced"] >= 1
    assert stats["runs_synced"] >= 1


def test_obsidian_sync_format_helpers_and_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    sync = obsidian_module.ObsidianSync(str(tmp_path / "vault"))
    assert sync._format_claims(None, "P1") == "No claims extracted."
    assert sync._format_evidence(None, "P1") == "No evidence linked."
    assert "No claims" in sync._format_claims([{"paper_id": "P2"}], "P1")
    assert "No evidence" in sync._format_evidence([{"paper_id": "P2"}], "P1")

    note_path = sync.papers_dir / "x.md"
    content = "abc"

    orig_open = builtins.open

    def _mock_open(*args: object, **kwargs: object):
        if str(args[0]).endswith("x.md"):
            raise OSError("no-write")
        return orig_open(*args, **kwargs)

    monkeypatch.setattr(builtins, "open", _mock_open)
    err = sync._write_note(note_path, content)
    assert err.status == "error"


def _make_response(
    status_code: int = 200,
    payload: dict[str, Any] | None = None,
    raise_exc: Exception | None = None,
) -> Any:
    class _Resp:
        def __init__(self) -> None:
            self.status_code = status_code

        def raise_for_status(self) -> None:
            if raise_exc:
                raise raise_exc

        def json(self) -> dict[str, Any]:
            return payload or {}

    return _Resp()


def test_crossref_get_work_and_search(monkeypatch: pytest.MonkeyPatch) -> None:
    client = crossref_module.CrossrefClient(mailto="a@example.com", timeout=1.0)
    work_item = {
        "DOI": "10.1000/xyz",
        "title": ["A title"],
        "author": [{"given": "Jane", "family": "Doe"}],
        "published-online": {"date-parts": [[2024, 2, 3]]},
        "container-title": ["Journal"],
        "abstract": "<jats:p>Abstract</jats:p>",
        "ISSN": ["1234-5678"],
        "URL": "https://example.org",
        "references-count": 10,
        "is-referenced-by-count": 20,
    }

    def _mock_get(url: str, **kwargs: object) -> Any:
        if url.endswith("/works/10.1000/xyz"):
            return _make_response(payload={"message": work_item})
        return _make_response(payload={"message": {"items": [work_item]}})

    monkeypatch.setattr(crossref_module.requests, "get", _mock_get)

    work = client.get_work("https://doi.org/10.1000/xyz")
    assert work is not None
    assert work.abstract == "Abstract"
    assert work.to_dict()["doi"] == "10.1000/xyz"

    works = client.search("abc", rows=2001, offset=2, filter_type="journal-article")
    assert len(works) == 1
    assert works[0].doi == "10.1000/xyz"


def test_crossref_error_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    client = crossref_module.CrossrefClient()
    monkeypatch.setattr(
        crossref_module.requests,
        "get",
        lambda *args, **kwargs: _make_response(status_code=404),
    )
    assert client.get_work("10.1000/missing") is None

    monkeypatch.setattr(
        crossref_module.requests,
        "get",
        lambda *args, **kwargs: (_ for _ in ()).throw(requests.RequestException("boom")),
    )
    assert client.get_work("10.1000/error") is None
    assert client.search("x") == []

    bad_item = {
        "DOI": "10.1000/x",
        "author": [None],
        "published-print": {"date-parts": [[1, 99, 99]]},
    }
    assert client._parse_work(bad_item) is None
    assert client._parse_work({}) is None


def test_citation_graph_build_related_and_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    retriever = citation_module.CitationGraphRetriever(max_hops=2)

    def _fetch(pid: str) -> citation_module.CitationNode | None:
        mapping = {
            "A": citation_module.CitationNode(
                paper_id="A",
                title="A",
                year=2020,
                citation_count=5,
                references=["B", "C"],
                cited_by=["D"],
            ),
            "B": citation_module.CitationNode(
                paper_id="B",
                title="B",
                year=2021,
                citation_count=100,
                references=["E"],
                cited_by=[],
            ),
            "C": citation_module.CitationNode(
                paper_id="C",
                title="C",
                year=2022,
                citation_count=10,
                references=[],
                cited_by=[],
            ),
            "D": citation_module.CitationNode(
                paper_id="D",
                title="D",
                year=2023,
                citation_count=30,
                references=[],
                cited_by=[],
            ),
            "E": citation_module.CitationNode(
                paper_id="E",
                title="E",
                year=2024,
                citation_count=20,
                references=[],
                cited_by=[],
            ),
        }
        return mapping.get(pid)

    monkeypatch.setattr(retriever, "_fetch_paper", _fetch)
    graph = retriever.build_graph(["A"], depth=2)
    assert "A" in graph and "B" in graph and "E" in graph

    related = retriever.find_related("A", top_k=3)
    assert related
    assert related[0].paper_id == "B"

    path = retriever.get_citation_path("A", "E")
    assert path is not None
    assert path.hop_count == 2
    assert retriever.get_citation_path("A", "ZZZ") is None


def test_citation_graph_fetch_uses_cache() -> None:
    node = citation_module.CitationNode(
        paper_id="X",
        title="X",
        year=2020,
        citation_count=1,
    )
    retriever = citation_module.CitationGraphRetriever(cache={"X": node})
    assert retriever._fetch_paper("X") is node


def test_source_registry_and_base_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Adapter(source_base_module.SourceAdapter):
        @property
        def source_name(self) -> str:
            return "dummy"

        def search(self, query: str, limit: int = 10) -> list[source_base_module.SearchResult]:
            return [
                source_base_module.SearchResult(
                    source_id="1",
                    title=query,
                    url="u",
                    abstract="a",
                    year=2024,
                    authors=[],
                    metadata={"limit": limit},
                )
            ]

        def fetch_details(self, source_ids: list[str]) -> list[dict[str, Any]]:
            return [{"id": sid} for sid in source_ids]

    monkeypatch.setattr(SourceRegistry, "_adapters", {})
    monkeypatch.setattr(SourceRegistry, "_instances", {})

    SourceRegistry.register("dummy")(_Adapter)
    inst1 = SourceRegistry.get_adapter("dummy")
    inst2 = SourceRegistry.get_adapter("dummy")
    assert inst1 is inst2
    assert "dummy" in SourceRegistry.list_sources()
    assert inst1.validate_query("x") is True
    assert inst1.validate_query("   ") is False
    assert inst1.search("q")[0].title == "q"
    assert inst1.fetch_details(["1"]) == [{"id": "1"}]

    with pytest.raises(ValueError):
        SourceRegistry.get_adapter("missing")


def test_health_builtin_checks_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_requests = ModuleType("requests")
    fake_requests.get = lambda _url, timeout=5: SimpleNamespace(status_code=200)  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, "requests", fake_requests)
    assert health_module.check_qdrant("http://x").status == health_module.HealthStatus.HEALTHY

    fake_requests.get = lambda _url, timeout=5: SimpleNamespace(status_code=503)  # type: ignore[attr-defined]
    assert health_module.check_qdrant("http://x").status == health_module.HealthStatus.DEGRADED

    def _raise(*args: object, **kwargs: object) -> None:
        raise RuntimeError("net")

    fake_requests.get = _raise  # type: ignore[assignment]
    assert health_module.check_qdrant("http://x").status == health_module.HealthStatus.UNHEALTHY

    fake_shutil = ModuleType("shutil")
    gb = 1024**3
    fake_shutil.disk_usage = lambda _path: (10 * gb, 5 * gb, 2 * gb)  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, "shutil", fake_shutil)
    assert (
        health_module.check_disk_space("/", min_gb=1.0).status == health_module.HealthStatus.HEALTHY
    )

    fake_shutil.disk_usage = lambda _path: (10 * gb, 9 * gb, int(0.6 * gb))  # type: ignore[attr-defined]
    assert (
        health_module.check_disk_space("/", min_gb=1.0).status
        == health_module.HealthStatus.DEGRADED
    )

    fake_shutil.disk_usage = lambda _path: (_ for _ in ()).throw(RuntimeError("disk"))  # type: ignore[attr-defined]
    assert (
        health_module.check_disk_space("/", min_gb=1.0).status
        == health_module.HealthStatus.UNHEALTHY
    )

    fake_psutil = ModuleType("psutil")

    @dataclass
    class _Mem:
        percent: float

    fake_psutil.virtual_memory = lambda: _Mem(10.0)  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, "psutil", fake_psutil)
    assert health_module.check_memory(max_percent=90.0).status == health_module.HealthStatus.HEALTHY

    fake_psutil.virtual_memory = lambda: _Mem(85.0)  # type: ignore[attr-defined]
    assert (
        health_module.check_memory(max_percent=90.0).status == health_module.HealthStatus.DEGRADED
    )

    fake_psutil.virtual_memory = lambda: _Mem(95.0)  # type: ignore[attr-defined]
    assert (
        health_module.check_memory(max_percent=90.0).status == health_module.HealthStatus.UNHEALTHY
    )

    monkeypatch.delitem(__import__("sys").modules, "psutil", raising=False)
    orig_import = builtins.__import__

    def _mock_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "psutil":
            raise ImportError("no-psutil")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _mock_import)
    assert health_module.check_memory(max_percent=90.0).status == health_module.HealthStatus.HEALTHY
