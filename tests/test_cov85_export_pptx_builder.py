from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace
import sys
import types

import pytest


def _import_pptx_builder(monkeypatch: pytest.MonkeyPatch):
    # Avoid circular import from jarvis_core.writing.__init__ during module import.
    writing_pkg = types.ModuleType("jarvis_core.writing")
    writing_pkg.__path__ = []  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "jarvis_core.writing", writing_pkg)

    outline_stub = types.ModuleType("jarvis_core.writing.outline_builder")

    class ClaimDatum:  # noqa: D401
        """Test stub for type import only."""

        pass

    outline_stub.ClaimDatum = ClaimDatum
    monkeypatch.setitem(sys.modules, "jarvis_core.writing.outline_builder", outline_stub)

    utils_stub = types.ModuleType("jarvis_core.writing.utils")

    def load_overview(run_dir: Path) -> str:
        overview_path = run_dir / "notes" / "00_RUN_OVERVIEW.md"
        if overview_path.exists():
            return overview_path.read_text(encoding="utf-8")
        return ""

    utils_stub.load_overview = load_overview
    monkeypatch.setitem(sys.modules, "jarvis_core.writing.utils", utils_stub)

    sys.modules.pop("jarvis_core.export.pptx_builder", None)
    return importlib.import_module("jarvis_core.export.pptx_builder")


class _FakeFont:
    def __init__(self) -> None:
        self.size = None


class _FakeRun:
    def __init__(self) -> None:
        self.text = ""
        self.font = _FakeFont()


class _FakeParagraph:
    def __init__(self) -> None:
        self.text = ""
        self.level = 0

    def add_run(self) -> _FakeRun:
        return _FakeRun()


class _FakeTextFrame:
    def __init__(self) -> None:
        self.paragraphs = [_FakeParagraph()]

    def clear(self) -> None:
        self.paragraphs = [_FakeParagraph()]

    def add_paragraph(self) -> _FakeParagraph:
        paragraph = _FakeParagraph()
        self.paragraphs.append(paragraph)
        return paragraph


class _FakePlaceholder:
    def __init__(self) -> None:
        self.text = ""
        self.text_frame = _FakeTextFrame()


class _FakeShape:
    def __init__(self) -> None:
        self.text_frame = _FakeTextFrame()


class _FakeShapes:
    def __init__(self) -> None:
        self.title = SimpleNamespace(text="")
        self.placeholders = [None, _FakePlaceholder()]

    def add_textbox(self, *args, **kwargs) -> _FakeShape:
        return _FakeShape()


class _FakeSlide:
    def __init__(self) -> None:
        self.shapes = _FakeShapes()
        self.placeholders = [None, SimpleNamespace(text="")]


class _FakeSlides:
    def __init__(self) -> None:
        self.items: list[_FakeSlide] = []

    def add_slide(self, _layout) -> _FakeSlide:
        slide = _FakeSlide()
        self.items.append(slide)
        return slide


class _FakePresentation:
    last_instance = None

    def __init__(self) -> None:
        self.slide_layouts = [object(), object()]
        self.slides = _FakeSlides()
        self.saved_path: Path | None = None
        _FakePresentation.last_instance = self

    def save(self, output_path: Path) -> None:
        output_path.write_bytes(b"fake-pptx")
        self.saved_path = output_path


def test_evidence_footer_text_handles_missing_and_present_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pb = _import_pptx_builder(monkeypatch)
    assert pb._evidence_footer_text(None) == "Evidence: unknown"
    assert pb._evidence_footer_text(SimpleNamespace(evidence=[])) == "Evidence: unknown"

    claim = SimpleNamespace(evidence=[SimpleNamespace(paper_id="P1", chunk_id="C2")])
    assert pb._evidence_footer_text(claim) == "Evidence: P1/C2"


def test_build_pptx_raises_when_pptx_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pb = _import_pptx_builder(monkeypatch)
    monkeypatch.setattr(pb, "PPTX_AVAILABLE", False)
    with pytest.raises(RuntimeError):
        pb.build_pptx_from_slides(tmp_path, [], tmp_path / "out.pptx")


def test_build_pptx_from_slides_with_fake_presentation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pb = _import_pptx_builder(monkeypatch)
    run_dir = tmp_path / "run"
    notes_dir = run_dir / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "00_RUN_OVERVIEW.md").write_text("Overview line\nmore", encoding="utf-8")

    claims = [
        SimpleNamespace(
            text="Claim A",
            evidence=[SimpleNamespace(paper_id="paper-a", chunk_id="chunk-a")],
        ),
        SimpleNamespace(
            text="Claim B",
            evidence=[SimpleNamespace(paper_id="paper-b", chunk_id="chunk-b")],
        ),
    ]
    output_path = tmp_path / "slides" / "deck.pptx"

    monkeypatch.setattr(pb, "PPTX_AVAILABLE", True)
    monkeypatch.setattr(pb, "Presentation", _FakePresentation)
    monkeypatch.setattr(pb, "Inches", lambda x: x)
    monkeypatch.setattr(pb, "Pt", lambda x: x)

    result = pb.build_pptx_from_slides(run_dir, claims, output_path)

    assert result == output_path
    assert output_path.exists()
    pres = _FakePresentation.last_instance
    assert pres is not None
    assert len(pres.slides.items) == 10
    assert pres.saved_path == output_path
