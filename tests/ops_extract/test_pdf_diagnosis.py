from __future__ import annotations

import sys
import types
from pathlib import Path

from jarvis_core.ops_extract.pdf_diagnosis import diagnose_pdf


class _FakeObj:
    def __init__(self, subtype: str):
        self.subtype = subtype

    def get_object(self):
        return {"/Subtype": self.subtype}


class _FakeRef:
    def __init__(self, payload: dict):
        self.payload = payload

    def get_object(self):
        return self.payload


class _FakePage:
    def __init__(self, text: str, has_image: bool = False):
        self.text = text
        self.has_image = has_image

    def extract_text(self):
        return self.text

    def get(self, key: str):
        if key != "/Resources" or not self.has_image:
            return None
        return {"/XObject": _FakeRef({"/Im1": _FakeObj("/Image")})}


def _set_fake_reader(monkeypatch, factory):
    fake_module = types.SimpleNamespace(PdfReader=factory)
    monkeypatch.setitem(sys.modules, "pypdf", fake_module)


def test_pdf_diagnosis_text_embedded(monkeypatch, tmp_path: Path):
    class _Reader:
        is_encrypted = False
        pages = [_FakePage("abc", has_image=False)]

    _set_fake_reader(monkeypatch, lambda _path: _Reader())
    result = diagnose_pdf(tmp_path / "doc.pdf")
    assert result.type == "text-embedded"


def test_pdf_diagnosis_image_only(monkeypatch, tmp_path: Path):
    class _Reader:
        is_encrypted = False
        pages = [_FakePage("", has_image=False)]

    _set_fake_reader(monkeypatch, lambda _path: _Reader())
    result = diagnose_pdf(tmp_path / "doc.pdf")
    assert result.type == "image-only"


def test_pdf_diagnosis_hybrid(monkeypatch, tmp_path: Path):
    class _Reader:
        is_encrypted = False
        pages = [_FakePage("abc", has_image=True)]

    _set_fake_reader(monkeypatch, lambda _path: _Reader())
    result = diagnose_pdf(tmp_path / "doc.pdf")
    assert result.type == "hybrid"


def test_pdf_diagnosis_encrypted(monkeypatch, tmp_path: Path):
    class _Reader:
        is_encrypted = True
        pages = [_FakePage("", has_image=False)]

    _set_fake_reader(monkeypatch, lambda _path: _Reader())
    result = diagnose_pdf(tmp_path / "doc.pdf")
    assert result.type == "encrypted"


def test_pdf_diagnosis_corrupted(monkeypatch, tmp_path: Path):
    def _raise(_path):
        raise RuntimeError("broken")

    _set_fake_reader(monkeypatch, _raise)
    result = diagnose_pdf(tmp_path / "doc.pdf")
    assert result.type == "corrupted"
