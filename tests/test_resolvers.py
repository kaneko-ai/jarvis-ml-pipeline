"""Tests for DOI/PubMed/CrossRef Resolver (RP22).

Per RP22, these tests verify:
- CrossRef API mock lookup
- PubMed API mock lookup
- Reference enrichment
- Failure handling (graceful)
"""

from jarvis_core.reference import Reference, resolve_references
from jarvis_core.resolvers.crossref_resolver import (
    CrossRefResult,
    resolve_crossref,
    search_crossref,
)
from jarvis_core.resolvers.pubmed_resolver import (
    PubMedResult,
    resolve_pubmed,
)
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
# if str(ROOT) not in sys.path:
#     sys.path.insert(0, str(ROOT))


class TestCrossRefResolver:
    """Tests for CrossRef resolver."""

    def test_crossref_result_dataclass(self):
        """Should create result dataclass."""
        result = CrossRefResult(
            doi="10.1234/test",
            title="Test Paper",
            authors=["Smith, J."],
            year=2023,
            success=True,
        )
        assert result.doi == "10.1234/test"
        assert result.success is True

    @patch("jarvis_core.resolvers.crossref_resolver.urllib.request.urlopen")
    def test_search_crossref_success(self, mock_urlopen):
        """Should parse CrossRef response."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {
                "status": "ok",
                "message": {
                    "items": [
                        {
                            "DOI": "10.1234/example",
                            "title": ["Example Paper"],
                            "author": [
                                {"family": "Smith", "given": "John"},
                            ],
                            "published-print": {"date-parts": [[2023]]},
                            "container-title": ["Nature"],
                            "URL": "https://example.com",
                        }
                    ]
                },
            }
        ).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock()
        mock_urlopen.return_value = mock_response

        result = search_crossref("Example Paper")

        assert result.success is True
        assert result.doi == "10.1234/example"
        assert result.title == "Example Paper"
        assert "Smith, John" in result.authors
        assert result.year == 2023

    @patch("jarvis_core.resolvers.crossref_resolver.urllib.request.urlopen")
    def test_search_crossref_failure(self, mock_urlopen):
        """Should handle failures gracefully."""
        mock_urlopen.side_effect = Exception("Network error")

        result = search_crossref("Test")

        assert result.success is False
        assert result.doi is None

    def test_resolve_crossref_enriches_reference(self):
        """Should enrich reference with metadata."""
        ref = Reference(
            id="R1",
            source_type="pdf",
            locator="pdf:paper.pdf",
            title="CD73 in Cancer",
        )

        # Mock the search to return success
        with patch("jarvis_core.resolvers.crossref_resolver.search_crossref") as mock:
            mock.return_value = CrossRefResult(
                doi="10.1234/cd73",
                title="CD73 in Cancer: A Review",
                authors=["Wang, X."],
                year=2022,
                journal="Cancer Research",
                success=True,
            )

            resolve_crossref(ref)

        assert ref.doi == "10.1234/cd73"
        assert ref.year == 2022


class TestPubMedResolver:
    """Tests for PubMed resolver."""

    def test_pubmed_result_dataclass(self):
        """Should create result dataclass."""
        result = PubMedResult(
            pmid="12345678",
            title="Test Article",
            success=True,
        )
        assert result.pmid == "12345678"

    def test_resolve_pubmed_enriches_reference(self):
        """Should enrich reference with PMID."""
        ref = Reference(
            id="R1",
            source_type="url",
            locator="url:https://pubmed.com",
            title="CD73 immunotherapy",
        )

        with patch("jarvis_core.resolvers.pubmed_resolver.search_pubmed") as mock:
            mock.return_value = PubMedResult(
                pmid="98765432",
                title="CD73 immunotherapy",
                authors=["Kim, S."],
                year=2021,
                journal="Nature Medicine",
                success=True,
            )

            resolve_pubmed(ref)

        assert ref.pmid == "98765432"


class TestResolveReferences:
    """Tests for resolve_references function."""

    def test_resolve_references_calls_resolvers(self):
        """Should call both resolvers."""
        refs = [
            Reference(id="R1", source_type="pdf", locator="pdf:x", title="Test"),
        ]

        with patch("jarvis_core.resolvers.crossref_resolver.resolve_crossref") as mock_cr:
            with patch("jarvis_core.resolvers.pubmed_resolver.resolve_pubmed") as mock_pm:
                resolve_references(refs)

                mock_cr.assert_called_once()
                mock_pm.assert_called_once()

    def test_resolve_references_handles_errors(self):
        """Should not fail on resolver errors."""
        refs = [
            Reference(id="R1", source_type="pdf", locator="pdf:x", title="Test"),
        ]

        with patch("jarvis_core.resolvers.crossref_resolver.resolve_crossref") as mock_cr:
            with patch("jarvis_core.resolvers.pubmed_resolver.resolve_pubmed") as mock_pm:
                mock_cr.side_effect = Exception("API error")
                mock_pm.side_effect = Exception("API error")

                # Should not raise
                result = resolve_references(refs)

                assert len(result) == 1


class TestReferenceExtendedFields:
    """Tests for extended Reference fields."""

    def test_reference_has_doi_pmid_journal(self):
        """Reference should have doi/pmid/journal fields."""
        ref = Reference(
            id="R1",
            source_type="pdf",
            locator="pdf:x",
            doi="10.1234/test",
            pmid="12345",
            journal="Nature",
        )

        assert ref.doi == "10.1234/test"
        assert ref.pmid == "12345"
        assert ref.journal == "Nature"

    def test_to_dict_includes_extended_fields(self):
        """to_dict should include doi/pmid/journal."""
        ref = Reference(
            id="R1",
            source_type="pdf",
            locator="pdf:x",
            doi="10.1234/test",
            pmid="12345",
            journal="Nature",
        )

        d = ref.to_dict()

        assert d["doi"] == "10.1234/test"
        assert d["pmid"] == "12345"
        assert d["journal"] == "Nature"

    def test_from_dict_restores_extended_fields(self):
        """from_dict should restore doi/pmid/journal."""
        data = {
            "id": "R1",
            "source_type": "pdf",
            "locator": "pdf:x",
            "doi": "10.9999/abc",
            "pmid": "99999",
            "journal": "Science",
        }

        ref = Reference.from_dict(data)

        assert ref.doi == "10.9999/abc"
        assert ref.pmid == "99999"
        assert ref.journal == "Science"