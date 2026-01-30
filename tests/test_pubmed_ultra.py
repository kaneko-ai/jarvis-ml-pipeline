"""Tests for pubmed ultra - FIXED."""

import pytest


@pytest.mark.slow
class TestPubMedBasic:
    def test_import(self):
        from jarvis_core.api import pubmed

        assert pubmed is not None


class TestModule:
    def test_pubmed_module(self):
        from jarvis_core.api import pubmed

        assert pubmed is not None