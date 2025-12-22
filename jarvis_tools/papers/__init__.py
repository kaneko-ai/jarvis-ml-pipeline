"""Papers tools package for literature processing."""
from .models import PaperRecord, ChunkRecord, Locator
from .pubmed import pubmed_esearch, pubmed_esummary
from .pmc_oa import get_oa_pdf_url
from .pdf_extract import extract_text_from_pdf
from .chunking import split_into_chunks, create_locator

__all__ = [
    "PaperRecord",
    "ChunkRecord",
    "Locator",
    "pubmed_esearch",
    "pubmed_esummary",
    "get_oa_pdf_url",
    "extract_text_from_pdf",
    "split_into_chunks",
    "create_locator",
]
