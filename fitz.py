"""Minimal PyMuPDF-compatible stub for test environments.

This project has tests that import `fitz` directly even when PyMuPDF is not
installed. The stub provides just enough behavior for those tests while marking
itself as non-production via `__jarvis_stub__`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

__jarvis_stub__ = True


# Marker object used by Pixmap(csRGB, pix) conversion path.
csRGB = object()


_DOC_STORE: dict[str, dict[str, Any]] = {}


@dataclass
class Rect:
    x0: float
    y0: float
    x1: float
    y1: float


class _Page:
    def __init__(self, doc: "_Document", xrefs: list[int] | None = None, text: str = "") -> None:
        self._doc = doc
        self._xrefs = xrefs or []
        self._text = text

    def insert_image(self, _rect: Rect, stream: bytes) -> None:
        xref = self._doc._next_xref
        self._doc._next_xref += 1
        self._doc._images[xref] = bytes(stream)
        self._xrefs.append(xref)

    def insert_text(self, _point: tuple[float, float], text: str) -> None:
        if self._text:
            self._text += "\n"
        self._text += text

    def get_images(self, full: bool = False) -> list[tuple[int, int, int, int, int, int, int, int, int]]:
        _ = full
        return [(xref, 0, 0, 0, 0, 0, 0, 0, 0) for xref in self._xrefs]

    def get_text(self, _mode: str = "text") -> str:
        return self._text


class _Document:
    def __init__(
        self,
        pages: list[_Page] | None = None,
        images: dict[int, bytes] | None = None,
        next_xref: int = 1,
    ) -> None:
        self._pages = pages or []
        self._images = images or {}
        self._next_xref = next_xref
        self.metadata: dict[str, Any] = {}

    def new_page(self) -> _Page:
        page = _Page(self)
        self._pages.append(page)
        return page

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        # Ensure the path exists for callers that check file existence.
        p.write_bytes(b"%PDF-STUB%\n")
        _DOC_STORE[str(p.resolve())] = self._serialize()

    def close(self) -> None:
        return None

    def __iter__(self):
        return iter(self._pages)

    def __len__(self) -> int:
        return len(self._pages)

    def __getitem__(self, index: int) -> _Page:
        return self._pages[index]

    def _serialize(self) -> dict[str, Any]:
        return {
            "pages": [{"xrefs": list(p._xrefs), "text": p._text} for p in self._pages],
            "images": {int(k): v for k, v in self._images.items()},
            "next_xref": self._next_xref,
        }

    @classmethod
    def _from_serialized(cls, data: dict[str, Any]) -> "_Document":
        images = {int(k): v for k, v in data.get("images", {}).items()}
        doc = cls(images=images, next_xref=int(data.get("next_xref", 1)))
        pages_data = data.get("pages", [])
        doc._pages = [
            _Page(doc, xrefs=[int(x) for x in p.get("xrefs", [])], text=str(p.get("text", "")))
            for p in pages_data
        ]
        return doc


class Pixmap:
    def __init__(self, *args: Any) -> None:
        self.n = 3
        self._bytes = b""

        if len(args) == 2 and isinstance(args[0], _Document):
            doc, xref = args
            self._bytes = doc._images.get(int(xref), b"")
            return

        if len(args) == 2 and args[0] is csRGB and isinstance(args[1], Pixmap):
            self._bytes = args[1]._bytes
            return

        raise TypeError("Unsupported Pixmap constructor arguments for stub")

    def tobytes(self, _fmt: str = "png") -> bytes:
        return self._bytes


def open(path: str | Path | None = None) -> _Document:
    if path is None:
        return _Document()

    p = Path(path)
    resolved = str(p.resolve())
    if resolved in _DOC_STORE:
        return _Document._from_serialized(_DOC_STORE[resolved])
    if not p.exists():
        raise FileNotFoundError(f"No such file: {p}")
    return _Document()
