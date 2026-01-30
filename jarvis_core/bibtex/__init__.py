"""
JARVIS BibTeX Module

BibTeX自動取得: arXiv / DOI / Crossref / PubMed
"""

from .fetcher import BibTeXFetcher

# TODO(deprecate): Backwards compatibility re-exports from bibtex_utils
try:
    from jarvis_core.bibtex_utils import _escape_bibtex, export_bibtex, format_bibtex_entry
except ImportError:
    export_bibtex = None
    format_bibtex_entry = None
    _escape_bibtex = None

__all__ = ["BibTeXFetcher", "export_bibtex", "format_bibtex_entry", "_escape_bibtex"]