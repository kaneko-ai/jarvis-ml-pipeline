"""DOCX builder with optional term normalization and figure tags."""
from __future__ import annotations

from pathlib import Path
from typing import Optional
import importlib.util

from jarvis_core.style.term_normalizer import load_style_guide, normalize_markdown

DOCX_AVAILABLE = importlib.util.find_spec("docx") is not None

if DOCX_AVAILABLE:
    import docx


def _inject_figure_placeholders(text: str) -> str:
    """Inject figure placeholders if missing."""
    for match in ["Fig. 1", "Fig. 2", "Fig. 3"]:
        fig_id = match.replace("Fig.", "FIG").replace(" ", "")
        placeholder = f"[[FIGURE_PLACEHOLDER:{fig_id}]]"
        if match in text and placeholder not in text:
            text += f"\n\n{placeholder}"
    return text


def build_docx_from_markdown(
    markdown_text: str,
    output_path: Path,
    apply_term_normalization: bool = True,
    inject_figure_tags: bool = True,
) -> Path:
    """Build a DOCX file from markdown-like text."""
    if apply_term_normalization:
        style_guide = load_style_guide()
        markdown_text, _, _ = normalize_markdown(markdown_text, style_guide)
    if inject_figure_tags:
        markdown_text = _inject_figure_placeholders(markdown_text)
    if not DOCX_AVAILABLE:
        raise RuntimeError("python-docx is required to build DOCX files")

    document = docx.Document()
    for line in markdown_text.splitlines():
        document.add_paragraph(line)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(output_path))
    return output_path
