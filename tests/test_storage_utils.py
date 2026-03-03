"""Tests for storage_utils module."""
import pytest
from pathlib import Path
from jarvis_core.storage_utils import get_logs_dir, get_exports_dir, get_pdf_archive_dir


class TestStorageUtils:
    def test_get_logs_dir_returns_path(self):
        p = get_logs_dir()
        assert isinstance(p, Path)
        assert p.exists()

    def test_get_logs_dir_with_subdir(self):
        p = get_logs_dir("test_subdir")
        assert isinstance(p, Path)
        assert p.exists()
        assert "test_subdir" in str(p)

    def test_get_exports_dir_returns_path(self):
        p = get_exports_dir()
        assert isinstance(p, Path)
        assert p.exists()

    def test_get_pdf_archive_dir_returns_path(self):
        p = get_pdf_archive_dir()
        assert isinstance(p, Path)
        assert p.exists()

    def test_logs_dir_is_writable(self):
        p = get_logs_dir("write_test")
        test_file = p / "pytest_write_check.txt"
        test_file.write_text("ok", encoding="utf-8")
        assert test_file.read_text(encoding="utf-8") == "ok"
        test_file.unlink()
