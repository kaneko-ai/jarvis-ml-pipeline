from __future__ import annotations

import builtins
import json
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest

from jarvis_core.extraction import semantic_search as semantic_module
from jarvis_core.ingestion import pdf_parser as pdf_parser_module
from jarvis_core.multimodal import figure_table as figure_module
from jarvis_core.ops import drift_detector as drift_module


def test_parse_pdf_file_not_found(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setitem(__import__("sys").modules, "fitz", ModuleType("fitz"))
    with pytest.raises(FileNotFoundError):
        pdf_parser_module.parse_pdf(tmp_path / "missing.pdf")


def test_parse_pdf_importerror(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pdf = tmp_path / "x.pdf"
    pdf.write_text("dummy", encoding="utf-8")
    orig_import = builtins.__import__

    def _mock_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "fitz":
            raise ImportError("forced")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _mock_import)
    with pytest.raises(RuntimeError):
        pdf_parser_module.parse_pdf(pdf)


def test_parse_pdf_happy_path_with_table_and_figure_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_text("dummy", encoding="utf-8")

    class _Page:
        def __init__(self, text: str) -> None:
            self._text = text

        def get_text(self, _mode: str) -> str:
            return self._text

    class _Doc:
        def __iter__(self):
            return iter(
                [
                    _Page(
                        "Sample Title\nAbstract: trial summary.\nINTRODUCTION\nBody\nREFERENCES\nRef 1\nRef 2"
                    )
                ]
            )

        def close(self) -> None:
            return None

    fake_fitz = ModuleType("fitz")
    fake_fitz.open = lambda _path: _Doc()
    monkeypatch.setitem(__import__("sys").modules, "fitz", fake_fitz)
    monkeypatch.setattr(pdf_parser_module, "extract_tables", lambda _path: [])
    monkeypatch.setattr(pdf_parser_module, "extract_figures", lambda _path: [])

    parsed = pdf_parser_module.parse_pdf(pdf)

    assert parsed.title == "Sample Title"
    assert "trial summary" in parsed.abstract
    assert parsed.references == ["Ref 1", "Ref 2"]


def test_parse_pdf_handles_table_figure_exceptions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_text("dummy", encoding="utf-8")

    class _Page:
        def get_text(self, _mode: str) -> str:
            return "Title\nABSTRACT: X.\nMETHODS\nY"

    class _Doc:
        def __iter__(self):
            return iter([_Page()])

        def close(self) -> None:
            return None

    fake_fitz = ModuleType("fitz")
    fake_fitz.open = lambda _path: _Doc()
    monkeypatch.setitem(__import__("sys").modules, "fitz", fake_fitz)
    monkeypatch.setattr(
        pdf_parser_module, "extract_tables", lambda _path: (_ for _ in ()).throw(ValueError("x"))
    )
    monkeypatch.setattr(
        pdf_parser_module, "extract_figures", lambda _path: (_ for _ in ()).throw(ValueError("y"))
    )

    parsed = pdf_parser_module.parse_pdf(pdf)
    assert parsed.tables == []
    assert parsed.figures == []


def test_pdf_parser_helper_extractors() -> None:
    lines = [
        "Title",
        "Abstract: One.",
        "Two.",
        "INTRODUCTION",
        "RESULTS",
        "Line A",
        "REFERENCES",
        "R1",
    ]
    assert "One." in pdf_parser_module._extract_abstract(lines)
    sections = pdf_parser_module._extract_sections(lines)
    assert any(sec.title == "Results" for sec in sections)
    refs = pdf_parser_module._extract_references(lines)
    assert refs == ["R1"]


def test_embedding_model_fallback_and_query_embedding(monkeypatch: pytest.MonkeyPatch) -> None:
    orig_import = builtins.__import__

    def _mock_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "sentence_transformers":
            raise ImportError("forced")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _mock_import)
    model = semantic_module.EmbeddingModel("dummy")
    emb = model.embed(["a", "b"])
    q = model.embed_query("query")
    assert emb.shape == (2, 384)
    assert q.shape == (384,)


def test_semantic_index_numpy_fallback_search_and_io(tmp_path: Path) -> None:
    class _Model:
        def embed(self, texts: list[str]) -> np.ndarray:
            return np.array([[float(i + 1), 1.0] for i, _ in enumerate(texts)], dtype=np.float32)

        def embed_query(self, _query: str) -> np.ndarray:
            return np.array([1.0, 1.0], dtype=np.float32)

    index = semantic_module.SemanticIndex(embedding_model=_Model())
    index._get_faiss = lambda: None
    docs = [{"id": "d1", "text": "alpha"}, {"id": "d2", "text": "beta"}]
    index.add_documents(docs)
    results = index.search("alpha", top_k=1)
    assert len(results) == 1
    assert results[0].doc_id in {"d1", "d2"}

    save_path = tmp_path / "idx.json"
    index.save(str(save_path))
    loaded = semantic_module.SemanticIndex(embedding_model=_Model())
    loaded._get_faiss = lambda: None
    loaded.load(str(save_path))
    assert len(loaded.documents) == 2


def test_semantic_index_faiss_path(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Model:
        def embed(self, texts: list[str]) -> np.ndarray:
            return np.array([[1.0, 0.0] for _ in texts], dtype=np.float32)

        def embed_query(self, _query: str) -> np.ndarray:
            return np.array([1.0, 0.0], dtype=np.float32)

    class _FakeIndex:
        def __init__(self, _dim: int) -> None:
            self.data: np.ndarray | None = None

        def add(self, arr: np.ndarray) -> None:
            self.data = arr

        def search(self, _query: np.ndarray, _k: int):
            return np.array([[0.9]], dtype=np.float32), np.array([[0]], dtype=np.int64)

    fake_faiss = SimpleNamespace(IndexFlatIP=_FakeIndex)
    index = semantic_module.SemanticIndex(embedding_model=_Model())
    monkeypatch.setattr(index, "_get_faiss", lambda: fake_faiss)
    index.add_documents([{"id": "id-1", "text": "txt"}])
    results = index.search("q", top_k=1)
    assert results[0].doc_id == "id-1"


def test_figure_understanding_extraction_and_search(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Clip:
        def encode(self, _text: str) -> np.ndarray:
            return np.array([0.5, 0.6], dtype=np.float32)

    fu = figure_module.FigureUnderstanding(clip_model=_Clip())
    monkeypatch.setattr(
        fu,
        "_extract_captions_from_pdf",
        lambda _path: ["Figure: growth curve", "Figure: microscopy image"],
    )
    figs = fu.extract_figures("x.pdf")
    assert figs[0].figure_type == "chart"
    assert len(figs[0].embedding or []) == 2

    out = fu.search_figures("growth image", figs, top_k=1)
    assert len(out) == 1


def test_figure_type_classifier_and_default_embedding() -> None:
    fu = figure_module.FigureUnderstanding()
    assert fu._classify_figure_type("graph and curve") == "chart"
    assert fu._classify_figure_type("schematic model") == "diagram"
    assert fu._classify_figure_type("microscopy image") == "photo"
    assert fu._classify_figure_type("western blot lane") == "blot"
    assert fu._classify_figure_type("flow cytometry data") == "flow"
    assert fu._classify_figure_type("unknown") == "other"
    assert len(fu._generate_embedding("x")) == 512


def test_extract_captions_from_pdf_missing_file(tmp_path: Path) -> None:
    fu = figure_module.FigureUnderstanding()
    caps = fu._extract_captions_from_pdf(str(tmp_path / "missing.pdf"))
    assert caps == []


def test_extract_captions_from_pdf_with_fake_pdfplumber(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fu = figure_module.FigureUnderstanding()
    pdf = tmp_path / "f.pdf"
    pdf.write_text("x", encoding="utf-8")

    class _Page:
        def extract_text(self) -> str:
            return "Figure 1: trend over time\nFig. 2: cell image"

    class _Ctx:
        def __enter__(self):
            return SimpleNamespace(pages=[_Page()])

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    fake_pdfplumber = SimpleNamespace(open=lambda _path: _Ctx())
    monkeypatch.setitem(__import__("sys").modules, "pdfplumber", fake_pdfplumber)
    caps = fu._extract_captions_from_pdf(str(pdf))
    assert len(caps) == 2


def test_table_extractor_extract_tables_and_to_text(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pdf = tmp_path / "tab.pdf"
    pdf.write_text("x", encoding="utf-8")

    class _Page:
        def __init__(self, tables: list[list[list[str]]]) -> None:
            self._tables = tables

        def extract_tables(self) -> list[list[list[str]]]:
            return self._tables

    class _Ctx:
        def __enter__(self):
            return SimpleNamespace(pages=[_Page([[["H1", "H2"], ["v1", "v2"]], [["only"]]])])

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    fake_pdfplumber = SimpleNamespace(open=lambda _path: _Ctx())
    monkeypatch.setitem(__import__("sys").modules, "pdfplumber", fake_pdfplumber)

    extractor = figure_module.TableExtractor()
    tables = extractor.extract_tables(str(pdf))
    assert len(tables) == 1
    text = extractor.table_to_text(tables[0])
    assert "H1 | H2" in text


def test_table_extractor_importerror_branch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pdf = tmp_path / "tab.pdf"
    pdf.write_text("x", encoding="utf-8")
    monkeypatch.delitem(__import__("sys").modules, "pdfplumber", raising=False)
    orig_import = builtins.__import__

    def _mock_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "pdfplumber":
            raise ImportError("forced")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _mock_import)
    assert figure_module.TableExtractor().extract_tables(str(pdf)) == []


def test_golden_runner_compare_and_run(tmp_path: Path) -> None:
    runner = drift_module.GoldenTestRunner(golden_dir=tmp_path)
    sim, diffs = runner.compare_outputs({"a": 1.0, "b": "x"}, {"a": 1.01, "b": "x"}, tolerance=0.02)
    assert sim == 1.0
    assert diffs == []

    case = drift_module.GoldenTestCase("t1", {"q": 1}, {"a": 1.0}, tolerance=0.01)
    result = runner.run_test(case, {"a": 1.0})
    assert result.passed is True


def test_golden_runner_save_and_load(tmp_path: Path) -> None:
    runner = drift_module.GoldenTestRunner(golden_dir=tmp_path)
    runner.save_golden("abc", {"x": 1})
    loaded = runner.load_golden("abc")
    assert loaded == {"x": 1}
    assert runner.load_golden("missing") is None


def test_spec_freezer_freeze_check_and_list(tmp_path: Path) -> None:
    freezer = drift_module.SpecFreezer(spec_dir=tmp_path)
    snap = freezer.freeze("s1", {"k": 1}, version="1.2")
    assert snap.frozen is True
    assert freezer.check("s1", {"k": 1}) is True
    assert freezer.check("s1", {"k": 2}) is False
    frozen = freezer.list_frozen()
    assert any(s.spec_id == "s1" for s in frozen)


def test_drift_detector_set_detect_and_check(tmp_path: Path) -> None:
    path = tmp_path / "baseline.json"
    detector = drift_module.DriftDetector(baseline_path=path)
    detector.set_baseline("acc", 0.9)
    alerts = detector.detect({"acc": 0.6, "new_metric": 1.0})
    assert len(alerts) == 1
    assert alerts[0].severity in {"critical", "high", "medium", "low"}
    assert detector.get_all_alerts()

    alert = detector.check_drift("acc", current_value=0.7, threshold=0.1)
    assert alert is not None
    assert detector.check_drift("none", current_value=0.1) is None
    assert detector.check_drift("acc", current_value=0.9, baseline=0.0) is None
    assert detector.check_drift("acc", current_value=0.91, baseline=0.9, threshold=0.2) is None


def test_top_level_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Freezer:
        def freeze(self, spec_id: str, schema: dict[str, object], version: str):
            return drift_module.SpecSnapshot(spec_id, version, "h", "t", frozen=True)

    class _Detector:
        def detect(self, metrics: dict[str, float]):
            return [
                drift_module.DriftAlert(
                    metric_name="m",
                    baseline_value=1.0,
                    current_value=2.0,
                    drift_percent=100.0,
                    severity="critical",
                    timestamp="t",
                    message="x",
                )
            ]

    monkeypatch.setattr(drift_module, "SpecFreezer", lambda: _Freezer())
    monkeypatch.setattr(drift_module, "DriftDetector", lambda: _Detector())
    snap = drift_module.freeze_spec("s", {"x": 1}, "1.0")
    alerts = drift_module.detect_drift({"m": 2.0})
    assert snap.spec_id == "s"
    assert len(alerts) == 1


def test_dataclass_to_dict_methods() -> None:
    snap = drift_module.SpecSnapshot("id", "1", "h", "now", frozen=True)
    alert = drift_module.DriftAlert("m", 1.0, 2.0, 100.0, "critical", "now", "msg")
    assert snap.to_dict()["spec_id"] == "id"
    assert alert.to_dict()["message"] == "msg"
    serialized = json.dumps(alert.to_dict())
    assert "critical" in serialized
