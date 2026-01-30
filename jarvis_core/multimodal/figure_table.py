"""Figure Understanding.

Per RP-340, processes and indexes figures from papers.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Figure:
    """Extracted figure information."""

    figure_id: str
    caption: str
    figure_type: str  # chart, diagram, photo, etc.
    page: int | None
    embedding: list[float] | None
    metadata: dict[str, Any]


@dataclass
class Table:
    """Extracted table information."""

    table_id: str
    caption: str
    headers: list[str]
    rows: list[list[str]]
    page: int | None
    metadata: dict[str, Any]


class FigureUnderstanding:
    """Processes and understands figures.

    Per RP-340:
    - Generates figure embeddings (CLIP)
    - Links captions to figures
    - Enables figure-based search
    """

    def __init__(
        self,
        clip_model=None,
        ocr_engine=None,
    ):
        self.clip_model = clip_model
        self.ocr_engine = ocr_engine

    def extract_figures(
        self,
        pdf_path: str,
        page_images: list[Any] | None = None,
    ) -> list[Figure]:
        """Extract figures from PDF.

        Args:
            pdf_path: Path to PDF file.
            page_images: Optional pre-extracted page images.

        Returns:
            List of extracted figures.
        """
        figures = []

        # Extract figure captions from text
        captions = self._extract_captions_from_pdf(pdf_path)

        for i, caption in enumerate(captions):
            figure_id = f"fig_{i + 1}"

            # Determine figure type from caption
            fig_type = self._classify_figure_type(caption)

            # Generate embedding if CLIP available
            embedding = None
            if self.clip_model:
                embedding = self._generate_embedding(caption)

            figures.append(
                Figure(
                    figure_id=figure_id,
                    caption=caption,
                    figure_type=fig_type,
                    page=None,
                    embedding=embedding,
                    metadata={},
                )
            )

        return figures

    def _extract_captions_from_pdf(self, pdf_path: str) -> list[str]:
        """Extract figure captions from PDF text."""
        captions = []

        # Read PDF text
        try:
            from pathlib import Path

            path = Path(pdf_path)
            if not path.exists():
                return []

            # Simple extraction - would use pdfplumber/pymupdf in production
            text = ""
            try:
                import pdfplumber

                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or ""
            except ImportError as e:
                logger.debug(f"pdfplumber not available: {e}")

            # Find figure captions
            pattern = r"(?:Figure|Fig\.?)\s*\d+[.:]\s*([^\n]{10,300})"
            for match in re.finditer(pattern, text, re.IGNORECASE):
                captions.append(f"Figure: {match.group(1).strip()}")

        except Exception as e:
            logger.debug(f"Failed to extract captions from {pdf_path}: {e}")

        return captions

    def _classify_figure_type(self, caption: str) -> str:
        """Classify figure type from caption."""
        caption_lower = caption.lower()

        if any(kw in caption_lower for kw in ["graph", "plot", "chart", "curve"]):
            return "chart"
        elif any(kw in caption_lower for kw in ["diagram", "schematic", "model"]):
            return "diagram"
        elif any(kw in caption_lower for kw in ["image", "photo", "micrograph", "microscopy"]):
            return "photo"
        elif any(kw in caption_lower for kw in ["western blot", "gel", "blot"]):
            return "blot"
        elif any(kw in caption_lower for kw in ["flow cytometry", "facs"]):
            return "flow"
        else:
            return "other"

    def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for figure caption."""
        if self.clip_model:
            return self.clip_model.encode(text).tolist()
        # Placeholder
        return [0.0] * 512

    def search_figures(
        self,
        query: str,
        figures: list[Figure],
        top_k: int = 5,
    ) -> list[Figure]:
        """Search figures by query.

        Args:
            query: Search query.
            figures: List of figures to search.
            top_k: Number of results.

        Returns:
            Matching figures.
        """
        # Simple keyword matching
        query_words = set(query.lower().split())

        scored = []
        for fig in figures:
            caption_words = set(fig.caption.lower().split())
            overlap = len(query_words & caption_words)
            scored.append((fig, overlap))

        scored.sort(key=lambda x: x[1], reverse=True)

        return [fig for fig, _ in scored[:top_k]]


class TableExtractor:
    """Extracts and processes tables.

    Per RP-341:
    - Complex table structure analysis
    - Merged cell handling
    - Structured JSON output
    """

    def extract_tables(
        self,
        pdf_path: str,
    ) -> list[Table]:
        """Extract tables from PDF.

        Args:
            pdf_path: Path to PDF.

        Returns:
            List of extracted tables.
        """
        tables = []

        try:
            import pdfplumber

            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()

                    for i, table_data in enumerate(page_tables):
                        if not table_data or len(table_data) < 2:
                            continue

                        headers = table_data[0] if table_data else []
                        rows = table_data[1:] if len(table_data) > 1 else []

                        # Clean cells
                        headers = [str(h or "").strip() for h in headers]
                        rows = [[str(c or "").strip() for c in row] for row in rows]

                        tables.append(
                            Table(
                                table_id=f"table_p{page_num + 1}_{i + 1}",
                                caption=f"Table from page {page_num + 1}",
                                headers=headers,
                                rows=rows,
                                page=page_num + 1,
                                metadata={},
                            )
                        )
        except ImportError as e:
            logger.debug(f"pdfplumber not available: {e}")
        except Exception as e:
            logger.debug(f"Failed to extract tables from {pdf_path}: {e}")

        return tables

    def table_to_text(self, table: Table) -> str:
        """Convert table to searchable text."""
        lines = [table.caption]
        lines.append(" | ".join(table.headers))
        for row in table.rows:
            lines.append(" | ".join(row))
        return "\n".join(lines)
