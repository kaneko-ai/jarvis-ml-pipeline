from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from xml.etree import ElementTree
from difflib import SequenceMatcher


@dataclass
class SectionDiff:
    section: str
    summary: str


@dataclass
class DiffReport:
    docx_sections: List[SectionDiff]
    md_sections: List[SectionDiff]
    pptx_sections: List[SectionDiff]

    def is_empty(self) -> bool:
        return not (self.docx_sections or self.md_sections or self.pptx_sections)


_DOCX_NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}
_PPTX_NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}


def extract_docx_sections(path: Path) -> Tuple[List[Tuple[str, str]], int]:
    paragraphs = _extract_docx_paragraphs(path)
    sections: List[Tuple[str, str]] = []
    heading_count = 0
    current_heading = "本文"
    buffer: List[str] = []

    for text, is_heading in paragraphs:
        if is_heading:
            if buffer:
                sections.append((current_heading, "\n".join(buffer).strip()))
                buffer = []
            current_heading = text or "無題"
            heading_count += 1
        else:
            if text:
                buffer.append(text)

    if buffer or not sections:
        sections.append((current_heading, "\n".join(buffer).strip()))

    return sections, heading_count


def _extract_docx_paragraphs(path: Path) -> List[Tuple[str, bool]]:
    paragraphs: List[Tuple[str, bool]] = []
    if not path or not path.exists():
        return paragraphs

    with zipfile.ZipFile(path) as zf:
        if "word/document.xml" not in zf.namelist():
            return paragraphs
        xml = zf.read("word/document.xml")

    root = ElementTree.fromstring(xml)
    for para in root.findall(".//w:p", _DOCX_NS):
        texts = [node.text for node in para.findall(".//w:t", _DOCX_NS) if node.text]
        text = "".join(texts).strip()
        style = para.find(".//w:pStyle", _DOCX_NS)
        style_val = style.attrib.get(f"{{{_DOCX_NS['w']}}}val") if style is not None else ""
        is_heading = bool(style_val and style_val.lower().startswith("heading"))
        paragraphs.append((text, is_heading))

    return paragraphs


def extract_pptx_slides(path: Path) -> List[Tuple[str, str]]:
    slides: List[Tuple[str, str]] = []
    if not path or not path.exists():
        return slides

    with zipfile.ZipFile(path) as zf:
        slide_names = sorted(
            [name for name in zf.namelist() if name.startswith("ppt/slides/slide")],
            key=_slide_sort_key,
        )
        for name in slide_names:
            xml = zf.read(name)
            root = ElementTree.fromstring(xml)
            texts = [node.text for node in root.findall(".//a:t", _PPTX_NS) if node.text]
            slide_number = _slide_number_from_name(name)
            slides.append((f"Slide {slide_number}", "\n".join(texts).strip()))

    return slides


def extract_md_sections(path: Path) -> List[Tuple[str, str]]:
    if not path or not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        lines = [line.rstrip() for line in f]

    sections: List[Tuple[str, str]] = []
    current_heading = "本文"
    buffer: List[str] = []
    for line in lines:
        if line.startswith("#"):
            if buffer:
                sections.append((current_heading, "\n".join(buffer).strip()))
                buffer = []
            current_heading = line.lstrip("#").strip() or "無題"
        else:
            buffer.append(line)

    if buffer or not sections:
        sections.append((current_heading, "\n".join(buffer).strip()))
    return sections


def diff_sections(old_sections: Iterable[Tuple[str, str]], new_sections: Iterable[Tuple[str, str]]) -> List[SectionDiff]:
    old_map = {title: content for title, content in old_sections}
    new_map = {title: content for title, content in new_sections}
    all_titles = list(dict.fromkeys(list(new_map.keys()) + list(old_map.keys())))

    diffs: List[SectionDiff] = []
    for title in all_titles:
        old_text = old_map.get(title, "")
        new_text = new_map.get(title, "")
        if not old_text and new_text:
            summary = _summarize_text_change("追加", new_text)
        elif old_text and not new_text:
            summary = _summarize_text_change("削除", old_text)
        else:
            ratio = SequenceMatcher(None, old_text, new_text).ratio() if old_text or new_text else 1.0
            if ratio >= 0.98:
                continue
            summary = f"更新（変更度 {int((1 - ratio) * 100)}%）"
        diffs.append(SectionDiff(section=title, summary=summary))

    return diffs


def generate_diff_report(
    current_docx: Optional[Path],
    previous_docx: Optional[Path],
    current_md: Optional[Path],
    previous_md: Optional[Path],
    current_pptx: Optional[Path],
    previous_pptx: Optional[Path],
) -> DiffReport:
    docx_sections = []
    if current_docx:
        new_sections, _ = extract_docx_sections(current_docx)
        old_sections, _ = extract_docx_sections(previous_docx) if previous_docx else ([], 0)
        docx_sections = diff_sections(old_sections, new_sections)

    md_sections = []
    if current_md:
        new_sections = extract_md_sections(current_md)
        old_sections = extract_md_sections(previous_md) if previous_md else []
        md_sections = diff_sections(old_sections, new_sections)

    pptx_sections = []
    if current_pptx:
        new_sections = extract_pptx_slides(current_pptx)
        old_sections = extract_pptx_slides(previous_pptx) if previous_pptx else []
        pptx_sections = diff_sections(old_sections, new_sections)

    return DiffReport(docx_sections=docx_sections, md_sections=md_sections, pptx_sections=pptx_sections)


def _summarize_text_change(label: str, text: str) -> str:
    preview = re.sub(r"\s+", " ", text).strip()
    if len(preview) > 120:
        preview = preview[:117] + "..."
    if preview:
        return f"{label}: {preview}"
    return f"{label}"


def _slide_sort_key(name: str) -> Tuple[int, str]:
    number = _slide_number_from_name(name)
    return (number, name)


def _slide_number_from_name(name: str) -> int:
    match = re.search(r"slide(\d+)", name)
    return int(match.group(1)) if match else 0
