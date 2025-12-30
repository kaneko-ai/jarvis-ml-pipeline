"""BibTeX export (alias to bibtex_utils).

This module provides backward compatibility.
"""
from .bibtex_utils import export_bibtex, format_bibtex_entry, _escape_bibtex

__all__ = ["export_bibtex", "format_bibtex_entry", "_escape_bibtex"]
