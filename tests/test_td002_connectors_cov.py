from __future__ import annotations

from typing import Any

import pytest
from defusedxml import ElementTree as ET

from jarvis_core.connectors import pmc as pmc_module
from jarvis_core.connectors import pubmed as pubmed_module


PUBMED_XML = b"""
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345</PMID>
      <Article>
        <ArticleTitle>Sample Title</ArticleTitle>
        <Abstract>
          <AbstractText Label="Background">Background text.</AbstractText>
          <AbstractText>Result text.</AbstractText>
        </Abstract>
        <Journal>
          <Title>Journal A</Title>
          <JournalIssue>
            <PubDate><Year>2024</Year></PubDate>
          </JournalIssue>
        </Journal>
        <AuthorList>
          <Author><LastName>Smith</LastName><Initials>J</Initials></Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList>
        <ArticleId IdType="doi">10.1000/example</ArticleId>
        <ArticleId IdType="pmc">PMC999</ArticleId>
      </ArticleIdList>
    </PubmedData>
  </PubmedArticle>
</PubmedArticleSet>
"""


PMC_XML = b"""
<article>
  <front>
    <article-meta>
      <title-group><article-title>PMC Title</article-title></title-group>
      <abstract><p>PMC abstract.</p></abstract>
    </article-meta>
  </front>
  <body>
    <sec>
      <title>Introduction</title>
      <p>Section paragraph.</p>
    </sec>
  </body>
  <back>
    <ref-list>
      <ref id="r1"><mixed-citation>Ref 1 text</mixed-citation></ref>
    </ref-list>
  </back>
</article>
"""


OA_ERROR_XML = b"<OA><error>not available</error></OA>"
OA_LINK_XML = (
    b'<OA><records><record><link href="https://example.com/file.tgz" /></record></records></OA>'
)


def _raise(exc: Exception) -> None:
    raise exc


def test_paperdoc_generate_chunks_and_to_paper() -> None:
    doc = pubmed_module.PaperDoc(
        pmid="1",
        title="Title",
        abstract="A" * 30,
        sections={"Methods": "B" * 20},
        pub_date="2024",
    )
    doc.generate_chunks(chunk_size=10)
    assert doc.chunks
    paper = doc.to_paper()
    assert paper.doc_id == "pmid:1"
    assert paper.year == 2024


def test_pubmed_search_success_and_error(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = pubmed_module.PubMedConnector(api_key="k", email="e@example.com")
    monkeypatch.setattr(
        connector,
        "_make_request",
        lambda _url: b'{"esearchresult":{"idlist":["1","2"]}}',
    )
    assert connector.search("query") == ["1", "2"]

    monkeypatch.setattr(connector, "_make_request", lambda _url: _raise(RuntimeError("boom")))
    assert connector.search("query") == []


def test_pubmed_fetch_details_and_search_and_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = pubmed_module.PubMedConnector()
    monkeypatch.setattr(connector, "_make_request", lambda _url: PUBMED_XML)
    papers = connector.fetch_details(["12345"])
    assert len(papers) == 1
    assert papers[0].pmid == "12345"
    assert papers[0].is_oa is True

    monkeypatch.setattr(connector, "search", lambda *_args, **_kwargs: ["12345"])
    monkeypatch.setattr(connector, "fetch_details", lambda pmids: papers if pmids else [])
    merged = connector.search_and_fetch("test", max_results=1)
    assert len(merged) == 1


def test_pubmed_parse_xml_and_article_error_paths() -> None:
    connector = pubmed_module.PubMedConnector()
    assert connector._parse_pubmed_xml(b"not xml") == []

    missing_medline = ET.fromstring("<PubmedArticle></PubmedArticle>")
    assert connector._parse_article(missing_medline) is None

    missing_pmid = ET.fromstring(
        "<PubmedArticle><MedlineCitation></MedlineCitation></PubmedArticle>"
    )
    assert connector._parse_article(missing_pmid) is None


def test_pubmed_global_helper_functions(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeConnector:
        def search(self, _query: str, _max_results: int, _filters: Any) -> list[str]:
            return ["10"]

        def fetch_details(self, _pmids: list[str]) -> list[pubmed_module.PaperDoc]:
            return [pubmed_module.PaperDoc(pmid="10", title="T")]

    fake = _FakeConnector()
    monkeypatch.setattr(pubmed_module, "_connector", fake)
    assert pubmed_module.search_pubmed("x") == ["10"]
    assert pubmed_module.fetch_paper_details(["10"])[0].pmid == "10"


def test_pmc_resolve_fetch_and_parse_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = pmc_module.PMCConnector(api_key="k", email="e@example.com")

    # resolve_pmcid success
    monkeypatch.setattr(
        connector,
        "_make_request",
        lambda _url: b'{"records":[{"pmcid":"PMC123"}]}',
    )
    assert connector.resolve_pmcid("111") == "PMC123"

    # resolve_pmcid failure
    monkeypatch.setattr(connector, "_make_request", lambda _url: _raise(RuntimeError("fail")))
    assert connector.resolve_pmcid("111") is None

    # parse xml success
    parsed = connector._parse_pmc_xml("PMC123", PMC_XML)
    assert parsed.success is True
    assert parsed.title == "PMC Title"
    assert "Introduction" in parsed.sections

    # parse xml error
    bad = connector._parse_pmc_xml("PMC123", b"<broken")
    assert bad.success is False


def test_pmc_fetch_via_oa_service_and_fulltext_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = pmc_module.PMCConnector()

    monkeypatch.setattr(connector, "_make_request", lambda _url: OA_ERROR_XML)
    result = connector._fetch_via_oa_service("PMC1")
    assert result.success is False
    assert result.source == "oa_service"

    monkeypatch.setattr(connector, "_make_request", lambda _url: OA_LINK_XML)
    result = connector._fetch_via_oa_service("PMC1")
    assert result.success is True
    assert "download_url" in result.sections

    monkeypatch.setattr(
        connector,
        "_fetch_pmc_xml",
        lambda _pmcid: pmc_module.FulltextResult(pmcid="PMC1", success=False, error="x"),
    )
    monkeypatch.setattr(
        connector,
        "_fetch_via_oa_service",
        lambda pmcid: pmc_module.FulltextResult(pmcid=pmcid, success=True, source="oa_service"),
    )
    combined = connector.fetch_fulltext("1")
    assert combined.success is True
    assert combined.pmcid == "PMC1"


def test_pmc_fetch_fulltext_for_pmid_and_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = pmc_module.PMCConnector()
    monkeypatch.setattr(connector, "resolve_pmcid", lambda _pmid: None)
    miss = connector.fetch_fulltext_for_pmid("1")
    assert miss.success is False

    monkeypatch.setattr(connector, "resolve_pmcid", lambda _pmid: "PMC7")
    monkeypatch.setattr(
        connector,
        "fetch_fulltext",
        lambda _pmcid: pmc_module.FulltextResult(pmcid="PMC7", success=True),
    )
    ok = connector.fetch_fulltext_for_pmid("1")
    assert ok.success is True

    class _FakePMC:
        def resolve_pmcid(self, _pmid: str) -> str | None:
            return "PMC8"

        def fetch_fulltext(self, _pmcid: str) -> pmc_module.FulltextResult:
            return pmc_module.FulltextResult(pmcid="PMC8", success=True)

    monkeypatch.setattr(pmc_module, "_connector", _FakePMC())
    assert pmc_module.resolve_pmcid("x") == "PMC8"
    assert pmc_module.fetch_fulltext("PMC8").success is True
