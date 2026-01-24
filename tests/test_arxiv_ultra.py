"""Tests for arxiv ultra - FIXED."""

import pytest


@pytest.mark.slow
class TestArxivBasic:
    def test_import(self):
        from jarvis_core.api.arxiv import ArxivClient

        assert ArxivClient is not None

    def test_create(self):
        from jarvis_core.api.arxiv import ArxivClient

        c = ArxivClient()
        assert c is not None


class TestModule:
    def test_arxiv_module(self):
        from jarvis_core.api import arxiv

        assert arxiv is not None
