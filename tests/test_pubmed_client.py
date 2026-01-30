"""Tests for PubMed Client.

Per JARVIS_LOCALFIRST_ROADMAP Task 1.4
Comprehensive test suite for PubMed client functionality.
"""

from unittest.mock import Mock, patch


class TestPubMedArticle:
    """Tests for PubMedArticle dataclass."""

    def test_minimal_creation(self):
        """Test with minimal required fields."""
        from jarvis_core.sources.pubmed_client import PubMedArticle

        article = PubMedArticle(pmid="12345678", title="Test Article")

        assert article.pmid == "12345678"
        assert article.title == "Test Article"
        assert article.abstract == ""
        assert article.authors == []

    def test_full_creation(self):
        """Test with all fields."""
        from jarvis_core.sources.pubmed_client import PubMedArticle

        article = PubMedArticle(
            pmid="12345678",
            title="Full Article",
            abstract="Abstract text",
            authors=["Smith J", "Doe A"],
            journal="Test Journal",
            pub_date="2024-01",
            doi="10.1000/test",
            pmc_id="PMC123456",
            keywords=["test", "article"],
            mesh_terms=["Term1", "Term2"],
        )

        assert article.doi == "10.1000/test"
        assert len(article.authors) == 2
        assert len(article.mesh_terms) == 2

    def test_to_dict(self):
        """Test serialization to dict."""
        from jarvis_core.sources.pubmed_client import PubMedArticle

        article = PubMedArticle(
            pmid="99999999",
            title="Test",
            authors=["Author A"],
        )

        result = article.to_dict()

        assert isinstance(result, dict)
        assert result["pmid"] == "99999999"
        assert "authors" in result


class TestPubMedClient:
    """Tests for PubMedClient."""

    def test_initialization_default(self):
        """Test default initialization."""
        from jarvis_core.sources.pubmed_client import PubMedClient

        client = PubMedClient()

        assert client.api_key is None
        assert client.tool_name == "jarvis-research-os"
        assert client.rate_limit == 0.34

    def test_initialization_with_api_key(self):
        """Test with API key."""
        from jarvis_core.sources.pubmed_client import PubMedClient

        client = PubMedClient(
            api_key="test_key",
            email="test@example.com",
        )

        assert client.api_key == "test_key"
        assert client.email == "test@example.com"

    def test_build_params_minimal(self):
        """Test parameter building without api key."""
        from jarvis_core.sources.pubmed_client import PubMedClient

        client = PubMedClient()
        params = client._build_params(db="pubmed", term="cancer")

        assert params["tool"] == "jarvis-research-os"
        assert params["db"] == "pubmed"
        assert "api_key" not in params

    def test_build_params_with_credentials(self):
        """Test parameter building with api key and email."""
        from jarvis_core.sources.pubmed_client import PubMedClient

        client = PubMedClient(api_key="key123", email="user@test.com")
        params = client._build_params(db="pubmed")

        assert params["api_key"] == "key123"
        assert params["email"] == "user@test.com"

    @patch("jarvis_core.sources.pubmed_client.requests.Session.get")
    def test_search_success(self, mock_get):
        """Test successful search."""
        from jarvis_core.sources.pubmed_client import PubMedClient

        mock_response = Mock()
        mock_response.json.return_value = {"esearchresult": {"idlist": ["111", "222", "333"]}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = PubMedClient()
        client._last_request_time = 0

        results = client.search("cancer treatment", max_results=10)

        assert len(results) == 3
        assert "111" in results

    @patch("jarvis_core.sources.pubmed_client.requests.Session.get")
    def test_search_empty_results(self, mock_get):
        """Test search with no results."""
        from jarvis_core.sources.pubmed_client import PubMedClient

        mock_response = Mock()
        mock_response.json.return_value = {"esearchresult": {"idlist": []}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = PubMedClient()
        client._last_request_time = 0

        results = client.search("xyznonexistent123")

        assert results == []

    @patch("jarvis_core.sources.pubmed_client.requests.Session.get")
    def test_search_network_error(self, mock_get):
        """Test search with network error."""
        import requests
        from jarvis_core.sources.pubmed_client import PubMedClient

        mock_get.side_effect = requests.RequestException("Network error")

        client = PubMedClient()
        client._last_request_time = 0

        results = client.search("cancer")

        assert results == []

    def test_fetch_empty_list(self):
        """Test fetch with empty PMID list."""
        from jarvis_core.sources.pubmed_client import PubMedClient

        client = PubMedClient()
        articles = client.fetch([])

        assert articles == []

    @patch("jarvis_core.sources.pubmed_client.requests.Session.get")
    def test_fetch_success(self, mock_get):
        """Test successful article fetch."""
        from jarvis_core.sources.pubmed_client import PubMedClient

        xml_response = """<?xml version="1.0"?>
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>12345678</PMID>
                    <Article>
                        <ArticleTitle>Test Article</ArticleTitle>
                        <Abstract>
                            <AbstractText>Test abstract.</AbstractText>
                        </Abstract>
                        <AuthorList>
                            <Author>
                                <LastName>Smith</LastName>
                                <ForeName>John</ForeName>
                            </Author>
                        </AuthorList>
                        <Journal>
                            <Title>Test Journal</Title>
                            <JournalIssue>
                                <PubDate>
                                    <Year>2024</Year>
                                </PubDate>
                            </JournalIssue>
                        </Journal>
                    </Article>
                </MedlineCitation>
            </PubmedArticle>
        </PubmedArticleSet>"""

        mock_response = Mock()
        mock_response.text = xml_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = PubMedClient()
        client._last_request_time = 0

        articles = client.fetch(["12345678"])

        assert len(articles) == 1
        assert articles[0].pmid == "12345678"
        assert articles[0].title == "Test Article"

    def test_parse_pubmed_xml_invalid(self):
        """Test XML parsing with invalid XML."""
        from jarvis_core.sources.pubmed_client import PubMedClient

        client = PubMedClient()
        articles = client._parse_pubmed_xml("<invalid>not valid")

        assert articles == []

    def test_parse_pubmed_xml_empty(self):
        """Test XML parsing with empty article set."""
        from jarvis_core.sources.pubmed_client import PubMedClient

        client = PubMedClient()
        xml = """<?xml version="1.0"?><PubmedArticleSet></PubmedArticleSet>"""
        articles = client._parse_pubmed_xml(xml)

        assert articles == []

    @patch("jarvis_core.sources.pubmed_client.requests.Session.get")
    def test_search_and_fetch(self, mock_get):
        """Test combined search and fetch."""
        from jarvis_core.sources.pubmed_client import PubMedClient

        search_response = Mock()
        search_response.json.return_value = {"esearchresult": {"idlist": ["11111"]}}
        search_response.raise_for_status = Mock()

        fetch_response = Mock()
        fetch_response.text = """<?xml version="1.0"?>
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>11111</PMID>
                    <Article>
                        <ArticleTitle>Combined Test</ArticleTitle>
                    </Article>
                </MedlineCitation>
            </PubmedArticle>
        </PubmedArticleSet>"""
        fetch_response.raise_for_status = Mock()

        mock_get.side_effect = [search_response, fetch_response]

        client = PubMedClient()
        client._last_request_time = 0

        articles = client.search_and_fetch("test", max_results=5)

        assert len(articles) == 1
        assert articles[0].pmid == "11111"

    def test_rate_limit_wait(self):
        """Test rate limiting functionality."""
        import time
        from jarvis_core.sources.pubmed_client import PubMedClient

        client = PubMedClient(rate_limit=0.1)
        client._last_request_time = time.time()

        start = time.time()
        client._rate_limit_wait()
        elapsed = time.time() - start

        # Should have waited some time (but not too much)
        assert elapsed >= 0.05  # At least some wait


class TestPubMedClientEdgeCases:
    """Edge case tests for PubMedClient."""

    def test_article_with_no_abstract(self):
        """Test parsing article with no abstract."""
        from jarvis_core.sources.pubmed_client import PubMedClient

        xml = """<?xml version="1.0"?>
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>99999</PMID>
                    <Article>
                        <ArticleTitle>No Abstract</ArticleTitle>
                    </Article>
                </MedlineCitation>
            </PubmedArticle>
        </PubmedArticleSet>"""

        client = PubMedClient()
        articles = client._parse_pubmed_xml(xml)

        assert len(articles) == 1
        assert articles[0].abstract == ""

    def test_article_with_multiple_authors(self):
        """Test parsing article with multiple authors."""
        from jarvis_core.sources.pubmed_client import PubMedClient

        xml = """<?xml version="1.0"?>
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>88888</PMID>
                    <Article>
                        <ArticleTitle>Multi Author</ArticleTitle>
                        <AuthorList>
                            <Author>
                                <LastName>Smith</LastName>
                                <ForeName>John</ForeName>
                            </Author>
                            <Author>
                                <LastName>Doe</LastName>
                                <ForeName>Jane</ForeName>
                            </Author>
                            <Author>
                                <LastName>Brown</LastName>
                                <ForeName>Bob</ForeName>
                            </Author>
                        </AuthorList>
                    </Article>
                </MedlineCitation>
            </PubmedArticle>
        </PubmedArticleSet>"""

        client = PubMedClient()
        articles = client._parse_pubmed_xml(xml)

        assert len(articles) == 1
        assert len(articles[0].authors) == 3


class TestModuleImports:
    """Test module imports."""

    def test_imports(self):
        """Test all exports are importable."""
        from jarvis_core.sources.pubmed_client import (
            PubMedClient,
            PubMedArticle,
        )

        assert PubMedClient is not None
        assert PubMedArticle is not None
