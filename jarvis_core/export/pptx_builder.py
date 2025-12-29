"""PPTX builder with optional term normalization."""
from __future__ import annotations

from pathlib import Path
from typing import List
import importlib.util

from jarvis_core.style.term_normalizer import load_style_guide, normalize_markdown

PPTX_AVAILABLE = importlib.util.find_spec("pptx") is not None

if PPTX_AVAILABLE:
    import pptx


def build_pptx_from_slides(
    slides: List[str],
    output_path: Path,
    apply_term_normalization: bool = True,
    footnote_template: str = "※ データはmean ± SDで記載",
) -> Path:
    """Build a PPTX file from slide text."""
    if apply_term_normalization:
        style_guide = load_style_guide()
        normalized_slides = []
        for slide in slides:
            normalized, _, _ = normalize_markdown(slide, style_guide)
            normalized_slides.append(normalized)
        slides = normalized_slides

    if not PPTX_AVAILABLE:
        raise RuntimeError("python-pptx is required to build PPTX files")

    presentation = pptx.Presentation()
    for slide_text in slides:
        slide = presentation.slides.add_slide(presentation.slide_layouts[1])
        body = slide.shapes.placeholders[1].text_frame
        body.text = slide_text
        body.add_paragraph().text = footnote_template
    output_path.parent.mkdir(parents=True, exist_ok=True)
    presentation.save(str(output_path))
    return output_path
