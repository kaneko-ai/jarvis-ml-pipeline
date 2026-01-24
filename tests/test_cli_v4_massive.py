"""Tests for cli_v4 massive - FIXED."""

import pytest


@pytest.mark.slow
class TestCLIBasic:
    def test_import(self):
        from jarvis_core.cli_v4 import main

        assert main is not None


class TestModule:
    def test_cli_module(self):
        from jarvis_core.cli_v4 import main

        assert main is not None
