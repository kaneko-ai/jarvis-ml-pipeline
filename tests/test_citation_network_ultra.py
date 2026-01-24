"""Tests for citation_network ultra - FIXED."""

import pytest


@pytest.mark.slow
class TestCitationNetworkBasic:
    def test_import(self):
        from jarvis_core.analysis.citation_network import CitationNetwork

        assert CitationNetwork is not None

    def test_create(self):
        from jarvis_core.analysis.citation_network import CitationNetwork

        cn = CitationNetwork()
        assert cn is not None


class TestModule:
    def test_cn_module(self):
        from jarvis_core.analysis import citation_network

        assert citation_network is not None
