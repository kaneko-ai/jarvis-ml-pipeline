"""PDF-to-Markdown client for JARVIS Research OS.

Primary: Datalab.to MinerU API (requires paid subscription).
Fallback: PyMuPDF4LLM (free, local, no API key needed).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class MinerUClient:
    """PDF to Markdown converter with MinerU API + PyMuPDF fallback."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DATALAB_API_KEY", "")
        self._use_api = bool(self.api_key)

    def convert_pdf(
        self,
        pdf_path: str,
        mode: str = "balanced",
        output_format: str = "markdown",
    ) -> dict:
        """Convert PDF. Try MinerU API first, fall back to PyMuPDF."""
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Try MinerU API if key is available
        if self._use_api:
            try:
                return self._convert_via_api(path, mode, output_format)
            except Exception as e:
                print(f"  MinerU API failed ({e}), falling back to PyMuPDF...")

        # Fallback: PyMuPDF4LLM (local, free)
        return self._convert_via_pymupdf(path)

    def _convert_via_api(self, path: Path, mode: str, output_format: str) -> dict:
        """Convert via Datalab.to MinerU API."""
        from datalab_sdk import ConvertOptions, DatalabClient

        client = DatalabClient(api_key=self.api_key)
        options = ConvertOptions(
            output_format=output_format,
            mode=mode,
            paginate=True,
        )
        result = client.convert(str(path), options=options)

        text = (
            getattr(result, "text", "")
            or getattr(result, "markdown", "")
            or str(result)
        )
        output = {
            "text": text,
            "metadata": {},
            "images": {},
            "format": output_format,
            "mode": mode,
            "source_file": str(path),
            "engine": "mineru_api",
        }
        if hasattr(result, "metadata") and result.metadata:
            output["metadata"] = (
                result.metadata
                if isinstance(result.metadata, dict)
                else str(result.metadata)
            )
        return output

    def _convert_via_pymupdf(self, path: Path) -> dict:
        """Convert via PyMuPDF4LLM (local, no API needed)."""
        import pymupdf4llm

        md_text = pymupdf4llm.to_markdown(str(path))

        # Extract metadata via PyMuPDF
        metadata = {}
        try:
            import pymupdf

            doc = pymupdf.open(str(path))
            meta = doc.metadata
            if meta:
                metadata = {
                    "title": meta.get("title", ""),
                    "author": meta.get("author", ""),
                    "subject": meta.get("subject", ""),
                    "creator": meta.get("creator", ""),
                    "pages": doc.page_count,
                }
            doc.close()
        except Exception:
            pass

        return {
            "text": md_text,
            "metadata": metadata,
            "images": {},
            "format": "markdown",
            "mode": "local",
            "source_file": str(path),
            "engine": "pymupdf4llm",
        }

    def convert_and_save(
        self,
        pdf_path: str,
        output_path: Optional[str] = None,
        mode: str = "balanced",
        output_format: str = "markdown",
    ) -> str:
        """Convert PDF and save result to file."""
        result = self.convert_pdf(pdf_path, mode=mode, output_format=output_format)

        if output_path is None:
            ext_map = {
                "markdown": ".md",
                "html": ".html",
                "json": ".json",
                "chunks": ".json",
            }
            ext = ext_map.get(output_format, ".md")
            output_path = str(Path(pdf_path).with_suffix(ext))

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["text"])

        return output_path

    def convert_pdf_to_papers(self, pdf_path: str, mode: str = "balanced") -> dict:
        """Convert PDF and return in JARVIS paper-compatible format."""
        result = self.convert_pdf(pdf_path, mode=mode, output_format="markdown")

        title = Path(pdf_path).stem.replace("_", " ").replace("-", " ")

        if isinstance(result.get("metadata"), dict):
            if result["metadata"].get("title"):
                title = result["metadata"]["title"]

        paper = {
            "title": title,
            "abstract": result["text"][:500] if result["text"] else "",
            "full_text": result["text"],
            "source": f"pdf_{result.get('engine', 'unknown')}",
            "source_file": str(pdf_path),
            "metadata": result.get("metadata", {}),
        }
        return paper
