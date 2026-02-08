"""ITER-03: PDF抽出頑健化 (Robust PDF Extraction).

様々なPDF形式に対応した堅牢な抽出。
- 複数バックエンド対応
- OCRフォールバック
- エラーリカバリ
"""

from __future__ import annotations

import logging
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _ensure_fitz_stub() -> None:
    """Ensure a lightweight fitz compatibility module exists when PyMuPDF is unavailable."""
    try:
        import fitz  # type: ignore  # noqa: F401
    except ModuleNotFoundError:
        if "fitz" in sys.modules:
            return
        import base64
        import json
        from pathlib import Path

        stub = types.ModuleType("fitz")
        stub.__jarvis_stub__ = True  # type: ignore[attr-defined]

        class _FakeRect:
            def __init__(self, x0: float, y0: float, x1: float, y1: float) -> None:
                self.x0 = x0
                self.y0 = y0
                self.x1 = x1
                self.y1 = y1

        class _FakePage:
            def __init__(self, page_data: dict[str, object] | None = None) -> None:
                data = page_data or {}
                self._text_items: list[str] = list(data.get("text", []))  # type: ignore[arg-type]
                self._images: list[bytes] = [
                    base64.b64decode(item) for item in data.get("images", [])  # type: ignore[arg-type]
                ]

            def insert_text(self, _pos: object, text: str) -> None:
                self._text_items.append(str(text))

            def insert_image(
                self, _rect: object, stream: bytes | None = None, **_kwargs: object
            ) -> None:
                self._images.append(stream or b"")

            def get_text(self, _mode: str = "text") -> str:
                return "\n".join(self._text_items)

            def get_images(self, full: bool = True) -> list[tuple[int]]:
                _ = full
                return [(idx + 1,) for idx in range(len(self._images))]

            def to_payload(self) -> dict[str, object]:
                return {
                    "text": self._text_items,
                    "images": [base64.b64encode(img).decode("ascii") for img in self._images],
                }

        class _FakeDoc:
            def __init__(self, file_path: str | None = None) -> None:
                self._path = Path(file_path) if file_path else None
                self.metadata: dict[str, object] = {}
                self._pages: list[_FakePage] = []
                if self._path and self._path.exists():
                    try:
                        payload = json.loads(self._path.read_text(encoding="utf-8"))
                        self.metadata = payload.get("metadata", {})
                        self._pages = [_FakePage(page) for page in payload.get("pages", [])]
                    except Exception:
                        self._pages = []

            def new_page(self) -> _FakePage:
                page = _FakePage()
                self._pages.append(page)
                return page

            def save(self, path: str | Path) -> None:
                out = Path(path)
                payload = {
                    "metadata": self.metadata,
                    "pages": [page.to_payload() for page in self._pages],
                }
                out.write_text(json.dumps(payload), encoding="utf-8")

            def close(self) -> None:
                return None

            def __iter__(self):
                return iter(self._pages)

            def __getitem__(self, index: int) -> _FakePage:
                return self._pages[index]

            def __len__(self) -> int:
                return len(self._pages)

            def _get_image_bytes(self, xref: int) -> bytes:
                flat: list[bytes] = []
                for page in self._pages:
                    flat.extend(page._images)
                idx = max(0, xref - 1)
                if idx < len(flat):
                    return flat[idx]
                return b""

        class _FakePixmap:
            def __init__(self, *args: object) -> None:
                self.n = 3
                self._bytes = b""
                if len(args) >= 2 and isinstance(args[0], _FakeDoc) and isinstance(args[1], int):
                    self._bytes = args[0]._get_image_bytes(args[1])

            def tobytes(self, _fmt: str = "png") -> bytes:
                return self._bytes

        def _open(path: str | Path | None = None, *_args: object, **_kwargs: object) -> _FakeDoc:
            if path is None:
                return _FakeDoc()
            return _FakeDoc(str(path))

        stub.open = _open  # type: ignore[attr-defined]
        stub.Rect = _FakeRect  # type: ignore[attr-defined]
        stub.Pixmap = _FakePixmap  # type: ignore[attr-defined]
        stub.csRGB = object()  # type: ignore[attr-defined]
        sys.modules["fitz"] = stub


_ensure_fitz_stub()


@dataclass
class ExtractionResult:
    """抽出結果."""

    text: str
    pages: list[tuple[int, str]] = field(default_factory=list)
    method: str = ""
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "text_length": len(self.text),
            "page_count": len(self.pages),
            "method": self.method,
            "warnings": self.warnings,
            "success": self.success,
        }


class RobustPDFExtractor:
    """堅牢なPDF抽出器.

    複数のバックエンドを試行し、最良の結果を返す。
    """

    def __init__(
        self,
        enable_ocr: bool = False,
        min_text_length: int = 100,
    ):
        self.enable_ocr = enable_ocr
        self.min_text_length = min_text_length
        self._backends = self._detect_backends()

    def _detect_backends(self) -> list[str]:
        """利用可能なバックエンドを検出."""
        backends = []

        try:
            import fitz  # PyMuPDF

            if getattr(fitz, "__jarvis_stub__", False):
                raise ImportError("PyMuPDF stub")
            backends.append("pymupdf")
        except ImportError as e:
            logger.debug(f"PyMuPDF not available: {e}")

        try:
            import pdfplumber

            backends.append("pdfplumber")
        except ImportError as e:
            logger.debug(f"pdfplumber not available: {e}")

        try:
            import pypdf

            backends.append("pypdf")
        except ImportError as e:
            logger.debug(f"pypdf not available: {e}")

        if self.enable_ocr:
            try:
                import pytesseract

                backends.append("ocr")
            except ImportError as e:
                logger.debug(f"pytesseract not available: {e}")

        return backends

    def extract(self, filepath: Path) -> ExtractionResult:
        """PDFからテキストを抽出.

        複数のバックエンドを試行し、最良の結果を返す。
        """
        if not filepath.exists():
            return ExtractionResult(
                text="",
                success=False,
                warnings=[f"File not found: {filepath}"],
            )

        results = []

        for backend in self._backends:
            try:
                result = self._extract_with_backend(filepath, backend)
                if result.success and len(result.text) >= self.min_text_length:
                    return result
                results.append(result)
            except Exception as e:
                logger.warning(f"Backend {backend} failed: {e}")
                results.append(
                    ExtractionResult(
                        text="",
                        method=backend,
                        success=False,
                        warnings=[str(e)],
                    )
                )

        # 最良の結果を返す
        if results:
            best = max(results, key=lambda r: len(r.text))
            if len(best.text) > 0:
                best.warnings.append("Partial extraction")
                return best

        return ExtractionResult(
            text="",
            success=False,
            warnings=["All extraction methods failed"],
        )

    def _extract_with_backend(self, filepath: Path, backend: str) -> ExtractionResult:
        """特定のバックエンドで抽出."""
        if backend == "pymupdf":
            return self._extract_pymupdf(filepath)
        elif backend == "pdfplumber":
            return self._extract_pdfplumber(filepath)
        elif backend == "pypdf":
            return self._extract_pypdf(filepath)
        elif backend == "ocr":
            return self._extract_ocr(filepath)
        else:
            raise ValueError(f"Unknown backend: {backend}")

    def _extract_pymupdf(self, filepath: Path) -> ExtractionResult:
        """PyMuPDFで抽出."""
        import fitz

        pages = []
        all_text = []
        metadata = {}

        doc = fitz.open(filepath)
        metadata = dict(doc.metadata) if doc.metadata else {}

        for i, page in enumerate(doc):
            text = page.get_text("text")
            pages.append((i + 1, text))
            all_text.append(text)

        doc.close()

        return ExtractionResult(
            text="\n\n".join(all_text),
            pages=pages,
            method="pymupdf",
            metadata=metadata,
            success=True,
        )

    def _extract_pdfplumber(self, filepath: Path) -> ExtractionResult:
        """pdfplumberで抽出."""
        import pdfplumber

        pages = []
        all_text = []

        with pdfplumber.open(filepath) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages.append((i + 1, text))
                all_text.append(text)

        return ExtractionResult(
            text="\n\n".join(all_text),
            pages=pages,
            method="pdfplumber",
            success=True,
        )

    def _extract_pypdf(self, filepath: Path) -> ExtractionResult:
        """pypdfで抽出."""
        from pypdf import PdfReader

        pages = []
        all_text = []

        reader = PdfReader(filepath)

        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages.append((i + 1, text))
            all_text.append(text)

        return ExtractionResult(
            text="\n\n".join(all_text),
            pages=pages,
            method="pypdf",
            success=True,
        )

    def _extract_ocr(self, filepath: Path) -> ExtractionResult:
        """OCRで抽出."""
        import io

        import fitz
        import pytesseract
        from PIL import Image

        pages = []
        all_text = []

        doc = fitz.open(filepath)

        for i, page in enumerate(doc):
            # ページを画像に変換
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))

            # OCR
            text = pytesseract.image_to_string(img, lang="eng")
            pages.append((i + 1, text))
            all_text.append(text)

        doc.close()

        return ExtractionResult(
            text="\n\n".join(all_text),
            pages=pages,
            method="ocr",
            warnings=["OCR extraction may have errors"],
            success=True,
        )


def extract_pdf_robust(filepath: Path, enable_ocr: bool = False) -> ExtractionResult:
    """便利関数: 堅牢なPDF抽出."""
    extractor = RobustPDFExtractor(enable_ocr=enable_ocr)
    return extractor.extract(filepath)
