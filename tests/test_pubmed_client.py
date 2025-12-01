from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis_core.integrations.pubmed_client import fetch_pubmed_details, search_pubmed  # noqa: E402


def test_search_pubmed_returns_ids(monkeypatch):
    class DummyResp:
        def __init__(self):
            self._json = {"esearchresult": {"idlist": ["123", "456"]}}

        def json(self):
            return self._json

        def raise_for_status(self):  # pragma: no cover - no-op
            return None

    def fake_get(url, params=None, timeout=None):  # noqa: ANN001
        assert "esearch.fcgi" in url
        assert params["retmode"] == "json"
        return DummyResp()

    monkeypatch.setattr("jarvis_core.integrations.pubmed_client.requests.get", fake_get)

    ids = search_pubmed("cancer", max_results=2)
    assert ids == ["123", "456"]


def test_fetch_pubmed_details_parses_xml(monkeypatch):
    xml = """
    <PubmedArticleSet>
      <PubmedArticle>
        <MedlineCitation>
          <PMID>111</PMID>
          <Article>
            <ArticleTitle>Test Title</ArticleTitle>
            <Journal><Title>Test Journal</Title></Journal>
            <Abstract><AbstractText>Sample abstract text.</AbstractText></Abstract>
          </Article>
        </MedlineCitation>
        <PubmedData>
          <ArticleIdList>
            <ArticleId IdType="doi">10.1234/example</ArticleId>
          </ArticleIdList>
        </PubmedData>
      </PubmedArticle>
    </PubmedArticleSet>
    """.strip()

    class DummyResp:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):  # pragma: no cover - no-op
            return None

    def fake_get(url, params=None, timeout=None):  # noqa: ANN001
        assert "efetch.fcgi" in url
        return DummyResp(xml)

    monkeypatch.setattr("jarvis_core.integrations.pubmed_client.requests.get", fake_get)

    results = fetch_pubmed_details(["111"])
    assert len(results) == 1
    summary = results[0]
    assert summary.pmid == "111"
    assert summary.title == "Test Title"
    assert summary.doi == "10.1234/example"
    assert summary.abstract.startswith("Sample abstract")
