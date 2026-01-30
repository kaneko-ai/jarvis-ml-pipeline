"""Tests for RP-320+ knowledge graph.

Core tests for KG features.
"""

import pytest

pytestmark = pytest.mark.core


class TestUMLSIntegration:
    """Tests for RP-320 UMLS Integration."""

    def test_normalize_gene(self):
        """Should normalize gene symbol."""
        from jarvis_tools.kg.umls import UMLSIntegration

        umls = UMLSIntegration()
        result = umls.normalize("CD73")

        assert result.cui is not None
        assert result.preferred_name is not None

    def test_expand_synonyms(self):
        """Should expand with synonyms."""
        from jarvis_tools.kg.umls import UMLSIntegration

        umls = UMLSIntegration()
        synonyms = umls.expand_with_synonyms("CD73")

        assert "CD73" in synonyms
        assert len(synonyms) > 1
