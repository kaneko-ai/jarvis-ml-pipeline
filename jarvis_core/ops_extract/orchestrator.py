"""Orchestrator for ops_extract mode."""

from __future__ import annotations

import json
import locale
import os
import platform
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from importlib.metadata import distributions
from pathlib import Path
from typing import Any

from jarvis_core.ingestion.normalizer import TextNormalizer
from jarvis_core.ingestion.rasterize_pdf import rasterize_pdf_to_images
from jarvis_core.ingestion.robust_extractor import ExtractionResult, RobustPDFExtractor
from jarvis_core.ingestion.yomitoku_cli import check_yomitoku_available, run_yomitoku_cli

from .contracts import OPS_EXTRACT_SCHEMA_VERSION, OpsExtractConfig, expected_optional_paths
from .drive_sync import sync_run_to_drive
from .failure_analysis import build_failure_analysis
from .learning import record_lesson
from .manifest import (
    build_input_entries,
    collect_output_entries,
    create_manifest_payload,
    write_manifest,
)
from .metrics import build_metrics, build_text_quality_warnings
from .needs_ocr import (
    NeedsOcrDecision,
    decide_needs_ocr,
    normalize_extraction_exceptions,
    summarize_page_metrics,
    unicode_category_distribution,
)
from .oauth_google import resolve_drive_access_token
from .preflight import PreflightReport, run_preflight_checks
from .pdf_diagnosis import diagnose_pdfs
from .retention import apply_ops_extract_retention
from .schema_validate import validate_run_contracts
from .security import masked_ops_extract_config
from .stage_cache import (
    cache_outputs_match,
    compute_input_hash,
    load_stage_cache,
    save_stage_cache,
    stage_outputs_from_paths,
    update_stage_cache_entry,
)
from .sync_queue import enqueue_sync_request


@dataclass
class OpsExtractOutcome:
    status: str
    answer: str
    papers: list[dict[str, Any]]
    warning_records: list[dict[str, Any]]
    warning_messages: list[str]
    metrics: dict[str, Any]
    failure_analysis: dict[str, Any]
    manifest: dict[str, Any]
    ocr_used: bool
    needs_ocr_reason: str
    text_source: str
    error: str | None = None
    text_source_payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class _DocParseResult:
    doc_index: int
    pdf_path: Path
    extract_result: ExtractionResult | None
    decision: NeedsOcrDecision | None
    page_metrics: dict[str, float | int]
    raw_pdf_text: str
    normalized_pdf_text: str
    error: str | None = None


@dataclass
class _DocOcrResult:
    doc_index: int
    pdf_path: Path
    raw_ocr_text: str
    normalized_ocr_text: str
    ocr_text_path: str | None
    figure_count: int
    ocr_meta: dict[str, Any]
    error: str | None = None


@dataclass
class _DocRasterResult:
    doc_index: int
    pdf_path: Path
    raster_meta: dict[str, Any]
    error: str | None = None


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _is_fixed_time_mode() -> bool:
    return bool(os.getenv("JARVIS_OPS_EXTRACT_FIXED_TIME"))


def _now_iso() -> str:
    fixed = os.getenv("JARVIS_OPS_EXTRACT_FIXED_TIME")
    if fixed:
        return fixed
    return datetime.now(timezone.utc).isoformat()


def _duration_since(started_perf: float) -> float:
    if _is_fixed_time_mode():
        return 0.0
    return max(0.0, time.perf_counter() - started_perf)


def _safe_read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _collect_paths(task_inputs: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for p in task_inputs:
        if p not in paths:
            paths.append(p)
    return paths


STAGE_IDS = [
    "preflight",
    "discover_inputs",
    "extract_text_pdf",
    "needs_ocr_decision",
    "rasterize_pdf",
    "ocr_yomitoku",
    "normalize_text",
    "extract_figures_tables",
    "compute_metrics_warnings",
    "write_contract_files",
    "enqueue_drive_sync",
    "retention_mark",
]


def _sha256_path(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    import hashlib

    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _trace_paths(paths: list[Path], run_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in paths:
        path = Path(raw)
        try:
            display = path.relative_to(run_dir).as_posix()
        except Exception:
            display = str(path)
        rows.append({"path": display, "sha256": _sha256_path(path)})
    return rows


def _collect_deps(limit: int = 200) -> list[str]:
    items: list[str] = []
    try:
        for dist in distributions():
            name = dist.metadata.get("Name") or dist.metadata.get("Summary") or "unknown"
            version = dist.version or "unknown"
            items.append(f"{name}=={version}")
    except Exception:
        return []
    items.sort()
    return items[:limit]


def _detect_gpu() -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
            return {"available": True, "devices": lines}
        return {"available": False, "detail": proc.stderr.strip() or "nvidia_smi_unavailable"}
    except Exception as exc:
        return {"available": False, "detail": str(exc)}


def _write_crash_dump(run_dir: Path, error_message: str) -> None:
    usage = shutil.disk_usage(Path.cwd())
    locale_info = locale.getpreferredencoding(False)
    payload = {
        "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "error": error_message,
        "environment": {
            "os": {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
            },
            "python": {
                "version": sys.version,
                "executable": sys.executable,
            },
            "locale": {
                "preferred_encoding": locale_info,
                "lang": os.getenv("LANG", ""),
            },
            "disk": {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
            },
            "gpu": _detect_gpu(),
            "deps": _collect_deps(),
        },
    }
    _write_json(run_dir / "crash_dump.json", payload)


class OpsExtractOrchestrator:
    def __init__(self, run_dir: Path, config: OpsExtractConfig):
        self.run_dir = Path(run_dir)
        self.config = config

    @staticmethod
    def _extract_document(
        doc_index: int, pdf_path: Path, config: OpsExtractConfig
    ) -> _DocParseResult:
        try:
            extractor = RobustPDFExtractor(enable_ocr=False, min_text_length=0)
            normalizer = TextNormalizer()
            extract_result = extractor.extract(pdf_path)
            raw_text = extract_result.text or ""
            page_metrics = summarize_page_metrics(extract_result.pages)
            extraction_exceptions = normalize_extraction_exceptions(extract_result.warnings)
            unicode_distribution = unicode_category_distribution(raw_text)
            decision = decide_needs_ocr(
                total_chars_extracted=int(page_metrics["total_chars_extracted"]),
                chars_per_page_mean=float(page_metrics["chars_per_page_mean"]),
                empty_page_ratio=float(page_metrics["empty_page_ratio"]),
                exceptions_in_text_extract=extract_result.warnings,
                extraction_exceptions=extraction_exceptions,
                unicode_distribution=unicode_distribution,
                thresholds=config.thresholds,
            )
            normalized = normalizer.normalize(raw_text).normalized
            return _DocParseResult(
                doc_index=doc_index,
                pdf_path=pdf_path,
                extract_result=extract_result,
                decision=decision,
                page_metrics=page_metrics,
                raw_pdf_text=raw_text,
                normalized_pdf_text=normalized,
                error=None,
            )
        except Exception as exc:
            return _DocParseResult(
                doc_index=doc_index,
                pdf_path=pdf_path,
                extract_result=None,
                decision=None,
                page_metrics={
                    "total_chars_extracted": 0,
                    "chars_per_page_mean": 0.0,
                    "empty_page_ratio": 1.0,
                    "page_count": 0,
                    "empty_pages": 0,
                },
                raw_pdf_text="",
                normalized_pdf_text="",
                error=str(exc),
            )

    @staticmethod
    def _rasterize_document(
        parse_result: _DocParseResult,
        ocr_dir: Path,
    ) -> _DocRasterResult:
        pdf_path = parse_result.pdf_path
        try:
            doc_ocr_root = ocr_dir / pdf_path.stem
            page_output_dir = doc_ocr_root / "input_pages"
            raster_meta = rasterize_pdf_to_images(
                pdf_path=pdf_path,
                output_dir=page_output_dir,
            )
            return _DocRasterResult(
                doc_index=parse_result.doc_index,
                pdf_path=pdf_path,
                raster_meta=raster_meta,
                error=None,
            )
        except Exception as exc:
            return _DocRasterResult(
                doc_index=parse_result.doc_index,
                pdf_path=pdf_path,
                raster_meta={},
                error=str(exc),
            )

    @staticmethod
    def _ocr_document(
        parse_result: _DocParseResult,
        raster_result: _DocRasterResult | None,
        config: OpsExtractConfig,
        ocr_dir: Path,
    ) -> _DocOcrResult:
        pdf_path = parse_result.pdf_path
        decision = parse_result.decision
        if decision is None:
            return _DocOcrResult(
                doc_index=parse_result.doc_index,
                pdf_path=pdf_path,
                normalized_ocr_text="",
                ocr_text_path=None,
                figure_count=0,
                ocr_meta={},
                error="ocr_requested_without_decision",
            )

        try:
            normalizer = TextNormalizer()
            doc_ocr_root = ocr_dir / pdf_path.stem
            raster_meta = (raster_result.raster_meta if raster_result is not None else {}) or {}
            if raster_result is not None and raster_result.error:
                raise RuntimeError(f"rasterize_failed:{raster_result.error}")
            yomi_output_dir = doc_ocr_root / "yomitoku"
            ocr_start = time.perf_counter()
            yomi_result = run_yomitoku_cli(
                input_path=pdf_path,
                output_dir=yomi_output_dir,
                mode=config.yomitoku_mode,
                figure=config.yomitoku_figure,
            )
            ocr_sec = round(time.perf_counter() - ocr_start, 6)
            raw_ocr_text = yomi_result.get("text", "") or ""
            normalized_ocr = normalizer.normalize(raw_ocr_text).normalized
            ocr_text_path = yomi_result.get("text_path")
            per_page_stats = [
                {"page": idx + 1, "image_path": str(path)}
                for idx, path in enumerate(raster_meta.get("image_paths", []) or [])
            ]
            ocr_meta = {
                "file": str(pdf_path),
                "decision": asdict(decision),
                "engine_version": str(yomi_result.get("engine_version", "yomitoku_cli")),
                "args": {
                    "mode": config.yomitoku_mode,
                    "figure": config.yomitoku_figure,
                },
                "timings": {
                    "rasterize_sec": float(raster_meta.get("elapsed_sec", 0.0)),
                    "ocr_sec": ocr_sec,
                    "total_sec": round(float(raster_meta.get("elapsed_sec", 0.0)) + ocr_sec, 6),
                },
                "per_page_stats": per_page_stats,
                "raster": raster_meta,
                "yomitoku": {
                    "text_path": ocr_text_path,
                    "returncode": yomi_result.get("returncode"),
                },
            }
            return _DocOcrResult(
                doc_index=parse_result.doc_index,
                pdf_path=pdf_path,
                raw_ocr_text=raw_ocr_text,
                normalized_ocr_text=normalized_ocr,
                ocr_text_path=ocr_text_path,
                figure_count=int(yomi_result.get("figure_count", 0)),
                ocr_meta=ocr_meta,
                error=None,
            )
        except Exception as exc:
            return _DocOcrResult(
                doc_index=parse_result.doc_index,
                pdf_path=pdf_path,
                raw_ocr_text="",
                normalized_ocr_text="",
                ocr_text_path=None,
                figure_count=0,
                ocr_meta={},
                error=str(exc),
            )

    def run(
        self,
        *,
        run_id: str,
        project: str,
        input_paths: list[Path],
    ) -> OpsExtractOutcome:
        started_at = _now_iso()
        started_perf = time.perf_counter()
        input_paths = _collect_paths(input_paths)

        warning_records: list[dict[str, Any]] = []
        papers: list[dict[str, Any]] = []
        text_entries: list[dict[str, Any]] = []
        combined_raw_sections: list[str] = []
        combined_sections: list[str] = []
        ocr_meta_by_doc: list[dict[str, Any]] = []
        figure_count = 0
        table_count = 0
        ocr_used = False
        status = "success"
        error_message: str | None = None
        total_chars_for_metric = 0
        total_pages_for_metric = 0
        total_empty_pages_for_metric = 0
        run_errors: list[str] = []
        combined_raw_text = ""

        ingestion_dir = self.run_dir / "ingestion"
        ocr_dir = self.run_dir / "ocr"
        stage_cache_path = self.run_dir / "stage_cache.json"
        ingestion_dir.mkdir(parents=True, exist_ok=True)
        ocr_dir.mkdir(parents=True, exist_ok=True)
        stage_cache_payload = load_stage_cache(stage_cache_path)

        trace_rows: list[dict[str, Any]] = []
        stage_starts: dict[str, tuple[str, float, list[Path]]] = {}

        def _start_stage(stage_id: str, inputs: list[Path]) -> None:
            stage_starts[stage_id] = (
                _now_iso(),
                time.perf_counter(),
                list(inputs),
            )

        def _finish_stage(
            stage_id: str,
            *,
            outputs: list[Path] | None = None,
            retry_count: int = 0,
            error: str | None = None,
        ) -> None:
            end_ts = _now_iso()
            start_ts, started_perf, inputs = stage_starts.pop(
                stage_id,
                (end_ts, time.perf_counter(), []),
            )
            trace_rows.append(
                {
                    "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
                    "stage_id": stage_id,
                    "start_ts": start_ts,
                    "end_ts": end_ts,
                    "duration": round(_duration_since(started_perf), 6),
                    "inputs": _trace_paths(inputs, self.run_dir),
                    "outputs": _trace_paths(outputs or [], self.run_dir),
                    "retry_count": int(retry_count),
                    "error": error,
                }
            )

        lessons_path = Path(self.config.lessons_path) if self.config.lessons_path else None
        _start_stage("preflight", input_paths)
        try:
            preflight_report: PreflightReport = run_preflight_checks(
                input_paths=input_paths,
                config=self.config,
                lessons_path=lessons_path,
            )
            network_diagnosis_payload = {
                "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
                "generated_at": _now_iso(),
                "profile": preflight_report.network_profile,
                "diagnosis": preflight_report.network_diagnosis or {},
            }
            _write_json(self.run_dir / "network_diagnosis.json", network_diagnosis_payload)
            _finish_stage("preflight", outputs=[self.run_dir / "network_diagnosis.json"])
        except Exception as exc:
            _finish_stage("preflight", error=str(exc))
            raise

        warning_records.extend(
            [
                {
                    "code": "PREFLIGHT_WARNING",
                    "message": msg,
                    "severity": "warning",
                }
                for msg in preflight_report.warnings
            ]
        )

        try:
            if not preflight_report.passed and self.config.stop_on_preflight_failure:
                raise RuntimeError(f"preflight_failed:{'; '.join(preflight_report.errors)}")
            _start_stage("discover_inputs", input_paths)
            try:
                if not input_paths:
                    raise RuntimeError("No input PDF files provided for ops_extract mode")

                missing_inputs = [str(path) for path in input_paths if not path.exists()]
                if missing_inputs:
                    raise FileNotFoundError(f"Input file not found: {missing_inputs}")
                _finish_stage("discover_inputs", outputs=input_paths)
            except Exception as exc:
                _finish_stage("discover_inputs", error=str(exc))
                raise

            _start_stage("extract_text_pdf", input_paths)
            try:
                diagnosis_payload = diagnose_pdfs(input_paths)
                _write_json(ingestion_dir / "pdf_diagnosis.json", diagnosis_payload)
                parse_results: list[_DocParseResult] = []
                with ThreadPoolExecutor(max_workers=max(1, int(self.config.parse_workers))) as pool:
                    future_map = {
                        pool.submit(self._extract_document, idx, pdf_path, self.config): idx
                        for idx, pdf_path in enumerate(input_paths)
                    }
                    for future in as_completed(future_map):
                        parse_results.append(future.result())
                parse_results.sort(key=lambda item: item.doc_index)
                _finish_stage("extract_text_pdf", outputs=[ingestion_dir / "pdf_diagnosis.json"])
                update_stage_cache_entry(
                    stage_cache_payload,
                    stage_id="extract_text_pdf",
                    input_hash=compute_input_hash([path.as_posix() for path in input_paths]),
                    outputs=stage_outputs_from_paths(
                        [ingestion_dir / "pdf_diagnosis.json"], self.run_dir
                    ),
                    status="computed",
                )
            except Exception as exc:
                _finish_stage("extract_text_pdf", error=str(exc))
                raise

            _start_stage("needs_ocr_decision", input_paths)
            needs_ocr_docs = [
                item
                for item in parse_results
                if item.error is None and item.decision is not None and item.decision.needs_ocr
            ]
            if needs_ocr_docs:
                yomi_ok = check_yomitoku_available()
                preflight_report.checks.append(
                    {
                        "name": "check_yomitoku_available_runtime",
                        "ok": yomi_ok,
                        "detail": "yomitoku_available" if yomi_ok else "yomitoku_missing",
                        "hard": True,
                        "configured_hard": True,
                    }
                )
                if not yomi_ok:
                    runtime_msg = "check_yomitoku_available_runtime:yomitoku_missing"
                    if str(self.config.preflight_rule_mode).lower() == "warn":
                        preflight_report.warnings.append(runtime_msg)
                    else:
                        preflight_report.errors.append(runtime_msg)
                        preflight_report.passed = False
                    run_errors.append("needs_ocr_detected_but_yomitoku_missing_at_runtime")
                    warning_records.append(
                        {
                            "code": "OCR_RUNTIME_PREREQUISITE_FAILED",
                            "message": "needs_ocr=true but YomiToku CLI is not available in this environment",
                            "severity": "error",
                        }
                    )
            _finish_stage("needs_ocr_decision")

            _start_stage("rasterize_pdf", [item.pdf_path for item in needs_ocr_docs])
            raster_by_index: dict[int, _DocRasterResult] = {}
            if needs_ocr_docs and not run_errors:
                with ThreadPoolExecutor(max_workers=max(1, int(self.config.ocr_workers))) as pool:
                    future_map = {
                        pool.submit(self._rasterize_document, item, ocr_dir): item.doc_index
                        for item in needs_ocr_docs
                    }
                    for future in as_completed(future_map):
                        raster_result = future.result()
                        raster_by_index[raster_result.doc_index] = raster_result
                for item in raster_by_index.values():
                    if item.error:
                        run_errors.append(f"rasterize_failed:{item.pdf_path.name}:{item.error}")
                        warning_records.append(
                            {
                                "code": "RASTERIZE_ERROR",
                                "message": f"{item.pdf_path.name}: {item.error}",
                                "severity": "error",
                            }
                        )
            _finish_stage(
                "rasterize_pdf",
                outputs=[
                    ocr_dir / item.pdf_path.stem / "input_pages"
                    for item in needs_ocr_docs
                    if (ocr_dir / item.pdf_path.stem / "input_pages").exists()
                ],
            )
            update_stage_cache_entry(
                stage_cache_payload,
                stage_id="rasterize_pdf",
                input_hash=compute_input_hash(
                    {
                        "docs": [item.pdf_path.as_posix() for item in needs_ocr_docs],
                        "count": len(needs_ocr_docs),
                    }
                ),
                outputs=stage_outputs_from_paths(
                    [
                        ocr_dir / item.pdf_path.stem / "input_pages"
                        for item in needs_ocr_docs
                        if (ocr_dir / item.pdf_path.stem / "input_pages").exists()
                    ],
                    self.run_dir,
                ),
                status="computed",
            )

            _start_stage("ocr_yomitoku", [item.pdf_path for item in needs_ocr_docs])
            ocr_by_index: dict[int, _DocOcrResult] = {}
            if needs_ocr_docs and not run_errors:
                with ThreadPoolExecutor(max_workers=max(1, int(self.config.ocr_workers))) as pool:
                    future_map = {
                        pool.submit(
                            self._ocr_document,
                            item,
                            raster_by_index.get(item.doc_index),
                            self.config,
                            ocr_dir,
                        ): item.doc_index
                        for item in needs_ocr_docs
                    }
                    for future in as_completed(future_map):
                        ocr_result = future.result()
                        ocr_by_index[ocr_result.doc_index] = ocr_result
            _finish_stage(
                "ocr_yomitoku",
                outputs=[
                    Path(item.ocr_text_path) for item in ocr_by_index.values() if item.ocr_text_path
                ],
            )
            update_stage_cache_entry(
                stage_cache_payload,
                stage_id="ocr_yomitoku",
                input_hash=compute_input_hash(
                    {
                        "docs": [item.pdf_path.as_posix() for item in needs_ocr_docs],
                        "count": len(needs_ocr_docs),
                    }
                ),
                outputs=stage_outputs_from_paths(
                    [
                        Path(item.ocr_text_path)
                        for item in ocr_by_index.values()
                        if item.ocr_text_path
                    ],
                    self.run_dir,
                ),
                status="computed",
            )

            _start_stage("normalize_text", input_paths)
            method_flags: list[str] = []
            needs_ocr_reasons: list[str] = []

            for parse_result in parse_results:
                pdf_path = parse_result.pdf_path
                paper_id = f"ops_extract_{pdf_path.stem}"
                papers.append(
                    {
                        "paper_id": paper_id,
                        "title": pdf_path.stem,
                        "year": (
                            int(_now_iso()[:4]) if len(_now_iso()) >= 4 else datetime.now().year
                        ),
                        "source": "local",
                        "filepath": str(pdf_path),
                    }
                )

                if parse_result.error:
                    run_errors.append(f"parse_failed:{pdf_path.name}:{parse_result.error}")
                    warning_records.append(
                        {
                            "code": "EXTRACT_ERROR",
                            "message": f"{pdf_path.name}: {parse_result.error}",
                            "severity": "error",
                        }
                    )
                    decision = NeedsOcrDecision(
                        needs_ocr=False,
                        reason="parse_failed",
                        metrics={
                            "total_chars_extracted": 0,
                            "chars_per_page_mean": 0.0,
                            "empty_page_ratio": 1.0,
                            "parser_exception": 1,
                        },
                    )
                    raw_text = ""
                    normalized = ""
                    text_source = "pdf_text"
                    ocr_text_path = None
                else:
                    decision = parse_result.decision or NeedsOcrDecision(
                        needs_ocr=False,
                        reason="not_needed",
                        metrics={
                            "total_chars_extracted": 0,
                            "chars_per_page_mean": 0.0,
                            "empty_page_ratio": 1.0,
                            "parser_exception": 0,
                        },
                    )
                    needs_ocr_reasons.append(decision.reason)
                    page_metrics = parse_result.page_metrics
                    total_pages_for_metric += int(page_metrics.get("page_count", 0))
                    total_empty_pages_for_metric += int(page_metrics.get("empty_pages", 0))

                    ocr_result = ocr_by_index.get(parse_result.doc_index)
                    if decision.needs_ocr and ocr_result and not ocr_result.error:
                        ocr_used = True
                        raw_text = ocr_result.raw_ocr_text
                        normalized = ocr_result.normalized_ocr_text
                        text_source = "ocr_yomitoku"
                        ocr_text_path = ocr_result.ocr_text_path
                        figure_count += int(ocr_result.figure_count)
                        if ocr_result.ocr_meta:
                            ocr_meta_by_doc.append(ocr_result.ocr_meta)
                    elif decision.needs_ocr and ocr_result and ocr_result.error:
                        run_errors.append(f"ocr_failed:{pdf_path.name}:{ocr_result.error}")
                        warning_records.append(
                            {
                                "code": "OCR_ERROR",
                                "message": f"{pdf_path.name}: {ocr_result.error}",
                                "severity": "error",
                            }
                        )
                        raw_text = parse_result.raw_pdf_text
                        normalized = parse_result.normalized_pdf_text
                        text_source = "pdf_text"
                        ocr_text_path = None
                    else:
                        raw_text = parse_result.raw_pdf_text
                        normalized = parse_result.normalized_pdf_text
                        text_source = "pdf_text"
                        ocr_text_path = None

                    if parse_result.extract_result:
                        for warning in parse_result.extract_result.warnings:
                            warning_records.append(
                                {
                                    "code": "EXTRACT_WARNING",
                                    "message": f"{pdf_path.name}: {warning}",
                                    "severity": "warning",
                                }
                            )

                method_flags.append(text_source)
                total_chars_for_metric += len(normalized)

                if not normalized.strip():
                    warning_records.append(
                        {
                            "code": "EMPTY_NORMALIZED_TEXT",
                            "message": f"Normalized text is empty for {pdf_path.name}",
                            "severity": "warning",
                        }
                    )

                section = f"## {pdf_path.name}\n\n{normalized}".strip()
                raw_section = f"## {pdf_path.name}\n\n{raw_text}".strip()
                combined_raw_sections.append(raw_section)
                combined_sections.append(section)
                text_entries.append(
                    {
                        "file": str(pdf_path),
                        "paper_id": paper_id,
                        "method": text_source,
                        "needs_ocr": decision.needs_ocr,
                        "needs_ocr_reason": decision.reason,
                        "stats": decision.metrics,
                        "extract_backend": (
                            parse_result.extract_result.method
                            if parse_result.extract_result is not None
                            else "failed"
                        ),
                        "ocr_text_path": ocr_text_path,
                    }
                )

            if run_errors:
                status = "failed"
                error_message = "; ".join(run_errors)

            if ocr_meta_by_doc:
                _write_json(
                    ocr_dir / "ocr_meta.json",
                    {
                        "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
                        "generated_at": _now_iso(),
                        "run_id": run_id,
                        "project": project,
                        "docs": ocr_meta_by_doc,
                    },
                )

            _start_stage("extract_figures_tables", input_paths)
            if any(err.startswith("ocr_failed:") for err in run_errors):
                figure_table_status = "failed"
            elif figure_count > 0 or table_count > 0:
                figure_table_status = "success"
            else:
                figure_table_status = "not_supported"
            warning_records.append(
                {
                    "code": "FIGURE_TABLE_EXTRACTION",
                    "message": f"figure_table_extraction_status={figure_table_status}",
                    "severity": "info",
                    "status": figure_table_status,
                }
            )
            _finish_stage("extract_figures_tables")

            combined_text = "\n\n".join(x for x in combined_sections if x).strip()
            combined_raw_text = "\n\n".join(x for x in combined_raw_sections if x).strip()
            if not combined_text:
                combined_text = "# Extracted Text\n\n(no text extracted)"
            if not combined_raw_text:
                combined_raw_text = combined_text

            if ocr_used and any(flag == "pdf_text" for flag in method_flags):
                overall_text_source = "mixed"
            elif ocr_used:
                overall_text_source = "ocr_yomitoku"
            else:
                overall_text_source = "pdf_text"

            text_source_payload = {
                "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
                "run_id": run_id,
                "project": project,
                "source": overall_text_source,
                "entries": text_entries,
            }
            normalize_outputs = [ingestion_dir / "text.md", ingestion_dir / "text_source.json"]
            normalize_input_hash = compute_input_hash(
                {
                    "raw": combined_raw_text,
                    "normalized": combined_text,
                    "source": overall_text_source,
                    "entries": text_entries,
                }
            )
            normalize_cache = stage_cache_payload.get("stages", {}).get("normalize_text", {})
            normalize_skipped = False
            if self.config.resume_enabled and normalize_cache:
                cache_hash = str(normalize_cache.get("input_hash", ""))
                cache_outputs = list(normalize_cache.get("outputs", []))
                if cache_hash == normalize_input_hash and cache_outputs_match(
                    self.run_dir, cache_outputs
                ):
                    normalize_skipped = True
                    combined_text = _safe_read_text(ingestion_dir / "text.md") or combined_text
                    if (ingestion_dir / "text_source.json").exists():
                        with open(ingestion_dir / "text_source.json", encoding="utf-8") as f:
                            text_source_payload = json.load(f)
                        overall_text_source = str(
                            text_source_payload.get("source", overall_text_source)
                        )
                else:
                    warning_records.append(
                        {
                            "code": "RECOMPUTED",
                            "message": "normalize_text recomputed due input hash mismatch or stale cache",
                            "severity": "info",
                            "stage_id": "normalize_text",
                        }
                    )

            if not normalize_skipped:
                (ingestion_dir / "text.md").write_text(combined_text, encoding="utf-8")
                _write_json(ingestion_dir / "text_source.json", text_source_payload)

            update_stage_cache_entry(
                stage_cache_payload,
                stage_id="normalize_text",
                input_hash=normalize_input_hash,
                outputs=stage_outputs_from_paths(normalize_outputs, self.run_dir),
                status="skipped" if normalize_skipped else "computed",
            )

            quality_warnings = build_text_quality_warnings(combined_text)
            warning_records.extend(quality_warnings)
            _finish_stage(
                "normalize_text",
                outputs=normalize_outputs,
            )

        except Exception as exc:
            status = "failed"
            error_message = str(exc)
            warning_records.append(
                {
                    "code": "OPS_EXTRACT_ERROR",
                    "message": error_message,
                    "severity": "error",
                }
            )
            if not (ingestion_dir / "text.md").exists():
                (ingestion_dir / "text.md").write_text(
                    "# Extracted Text\n\n(extraction failed)", encoding="utf-8"
                )
            if not (ingestion_dir / "text_source.json").exists():
                _write_json(
                    ingestion_dir / "text_source.json",
                    {
                        "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
                        "run_id": run_id,
                        "project": project,
                        "source": "unknown",
                        "entries": [],
                    },
                )
            if not (ingestion_dir / "pdf_diagnosis.json").exists():
                _write_json(
                    ingestion_dir / "pdf_diagnosis.json",
                    {
                        "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
                        "files": [],
                        "summary": {
                            "text-embedded": 0,
                            "image-only": 0,
                            "hybrid": 0,
                            "encrypted": 0,
                            "corrupted": 0,
                        },
                    },
                )
            overall_text_source = "unknown"
            needs_ocr_reasons = ["runtime_error"]

        finished_at = _now_iso()
        duration_sec = _duration_since(started_perf)
        _start_stage("compute_metrics_warnings", [ingestion_dir / "text.md"])
        failure_analysis = build_failure_analysis(error_message, status=status)
        if status == "failed":
            try:
                record_lesson(
                    run_id=run_id,
                    category=str(failure_analysis.get("category", "unknown")),
                    root_cause=str(failure_analysis.get("root_cause_guess", "")),
                    recommendation_steps=list(failure_analysis.get("recommendation_steps", [])),
                    preventive_checks=list(failure_analysis.get("preventive_checks", [])),
                    lessons_path=lessons_path,
                )
            except Exception as lesson_exc:  # pragma: no cover
                warning_records.append(
                    {
                        "code": "LESSON_WRITE_FAILED",
                        "message": f"Failed to write lesson: {lesson_exc}",
                        "severity": "warning",
                    }
                )

        text_for_metrics = _safe_read_text(ingestion_dir / "text.md")
        encoding_warnings_count = sum(
            1 for warning in warning_records if str(warning.get("code", "")).startswith("TEXT_")
        )

        if total_pages_for_metric <= 0:
            total_pages_for_metric = 1
        chars_per_page_mean = total_chars_for_metric / total_pages_for_metric
        empty_page_ratio = total_empty_pages_for_metric / total_pages_for_metric
        needs_ocr_reason = (
            ",".join(sorted(set(needs_ocr_reasons))) if needs_ocr_reasons else "not_needed"
        )

        expected_paths = expected_optional_paths(run_dir=self.run_dir, include_ocr_meta=ocr_used)
        required_outputs_present = all(
            path.exists()
            for path in expected_paths
            if path.name not in {"manifest.json", "sync_state.json"}
        )

        raw_text_hash = _sha256_text(combined_raw_text or text_for_metrics)
        normalized_text_hash = _sha256_text(text_for_metrics)
        metrics = build_metrics(
            run_duration_sec=duration_sec,
            text_source=overall_text_source,
            total_chars=len(text_for_metrics),
            chars_per_page_mean=chars_per_page_mean,
            empty_page_ratio=empty_page_ratio,
            encoding_warnings_count=encoding_warnings_count,
            figure_count=figure_count,
            table_count=table_count,
            ocr_used=ocr_used,
            needs_ocr_reason=needs_ocr_reason,
            retry_count=0,
            resume_count=0,
            sync_state="not_started",
            manifest_committed_local=True,
            manifest_committed_drive=False,
            required_outputs_present=required_outputs_present,
            raw_text_sha256=raw_text_hash,
            normalized_text_sha256=normalized_text_hash,
            schema_version=OPS_EXTRACT_SCHEMA_VERSION,
        )

        run_metadata = {
            "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
            "run_id": run_id,
            "project": project,
            "mode": "ops_extract",
            "created_at": started_at,
            "finished_at": finished_at,
            "status": status,
            "config": masked_ops_extract_config(self.config),
            "preflight": {
                "passed": preflight_report.passed,
                "errors": preflight_report.errors,
                "warnings": preflight_report.warnings,
                "checks": preflight_report.checks,
                "network_profile": preflight_report.network_profile,
            },
        }

        input_entries = build_input_entries(input_paths, source="local")
        output_entries = collect_output_entries(self.run_dir, exclude_relpaths={"manifest.json"})
        extract_payload = {
            "method": overall_text_source,
            "needs_ocr": ocr_used,
            "needs_ocr_reason": needs_ocr_reason,
            "total_chars": metrics["extract"]["total_chars"],
            "chars_per_page_mean": metrics["extract"]["chars_per_page_mean"],
            "empty_page_ratio": metrics["extract"]["empty_page_ratio"],
        }
        ops_payload = {
            "retries": 0,
            "resume_count": 0,
            "sync_state": "not_started",
        }
        manifest_payload = create_manifest_payload(
            run_id=run_id,
            project=project,
            created_at=started_at,
            finished_at=finished_at,
            status=status,
            inputs=input_entries,
            outputs=output_entries,
            extract=extract_payload,
            ops=ops_payload,
            committed=True,
            committed_local=True,
            committed_drive=False,
            schema_version=OPS_EXTRACT_SCHEMA_VERSION,
        )
        _finish_stage("compute_metrics_warnings")

        _start_stage("write_contract_files", [ingestion_dir / "text.md"])
        _write_json(self.run_dir / "failure_analysis.json", failure_analysis)
        _write_json(
            self.run_dir / "warnings.json",
            {
                "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
                "warnings": warning_records,
            },
        )
        _write_jsonl(self.run_dir / "warnings.jsonl", warning_records)
        _write_json(self.run_dir / "metrics.json", metrics)
        _write_json(self.run_dir / "run_metadata.json", run_metadata)
        write_manifest(self.run_dir / "manifest.json", manifest_payload)
        if status == "failed" and error_message:
            _write_crash_dump(self.run_dir, error_message)

        contract_errors = validate_run_contracts(self.run_dir)
        if contract_errors:
            status = "failed"
            error_message = "contract_validation_failed:" + " | ".join(contract_errors)
            warning_records.append(
                {
                    "code": "CONTRACT_VALIDATION_FAILED",
                    "message": error_message,
                    "severity": "error",
                }
            )
            failure_analysis = {
                **failure_analysis,
                "status": "failed",
                "category": "contract_violation",
                "root_cause_guess": error_message,
            }
            run_metadata["status"] = "failed"
            manifest_payload["status"] = "failed"
            _write_json(self.run_dir / "failure_analysis.json", failure_analysis)
            _write_json(
                self.run_dir / "warnings.json",
                {
                    "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
                    "warnings": warning_records,
                },
            )
            _write_jsonl(self.run_dir / "warnings.jsonl", warning_records)
            _write_json(self.run_dir / "run_metadata.json", run_metadata)
            write_manifest(self.run_dir / "manifest.json", manifest_payload)
            _write_crash_dump(self.run_dir, error_message)

        update_stage_cache_entry(
            stage_cache_payload,
            stage_id="write_contract_files",
            input_hash=compute_input_hash(
                {
                    "status": status,
                    "warning_count": len(warning_records),
                    "metrics": metrics.get("extract", {}),
                }
            ),
            outputs=stage_outputs_from_paths(
                [
                    self.run_dir / "failure_analysis.json",
                    self.run_dir / "warnings.json",
                    self.run_dir / "warnings.jsonl",
                    self.run_dir / "metrics.json",
                    self.run_dir / "run_metadata.json",
                    self.run_dir / "manifest.json",
                ],
                self.run_dir,
            ),
            status="computed",
        )
        save_stage_cache(stage_cache_path, stage_cache_payload)
        write_outputs = [
            self.run_dir / "failure_analysis.json",
            self.run_dir / "warnings.json",
            self.run_dir / "warnings.jsonl",
            self.run_dir / "metrics.json",
            self.run_dir / "run_metadata.json",
            self.run_dir / "manifest.json",
            stage_cache_path,
        ]
        if status == "failed" and error_message:
            write_outputs.append(self.run_dir / "crash_dump.json")
        _finish_stage("write_contract_files", outputs=write_outputs)

        _start_stage(
            "enqueue_drive_sync",
            [self.run_dir / "manifest.json", self.run_dir / "metrics.json"],
        )
        try:
            should_defer_sync = (
                self.config.sync_enabled
                and not self.config.sync_dry_run
                and preflight_report.network_profile != "ONLINE"
                and self.config.network_offline_policy == "defer"
            )
            if should_defer_sync:
                queue_path = enqueue_sync_request(
                    queue_dir=Path(self.config.sync_queue_dir),
                    run_dir=self.run_dir,
                    run_id=run_id,
                    reason=f"network_profile={preflight_report.network_profile}",
                    drive_folder_id=self.config.drive_folder_id,
                )
                sync_state = {
                    "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
                    "version": "ops_extract_sync_v2",
                    "state": "deferred",
                    "uploaded_files": [],
                    "pending_files": [{"path": "manifest.json"}],
                    "failed_files": [],
                    "retries": int(metrics["ops"]["retry_count"]),
                    "resume_count": int(metrics["ops"]["resume_count"]),
                    "last_error": "",
                    "dry_run": self.config.sync_dry_run,
                    "manifest_committed_drive": False,
                    "last_attempt_at": _now_iso(),
                    "queue_item": str(queue_path),
                }
                _write_json(self.run_dir / "sync_state.json", sync_state)
                warning_records.append(
                    {
                        "code": "SYNC_DEFERRED",
                        "message": f"Drive sync deferred ({preflight_report.network_profile})",
                        "severity": "warning",
                    }
                )
            else:
                resolved_drive_token = resolve_drive_access_token(
                    access_token=self.config.drive_access_token
                    or os.getenv("GOOGLE_DRIVE_ACCESS_TOKEN"),
                    refresh_token=self.config.drive_refresh_token,
                    client_id=self.config.drive_client_id,
                    client_secret=self.config.drive_client_secret,
                    token_cache_path=self.config.drive_token_cache_path,
                )
                sync_state = sync_run_to_drive(
                    run_dir=self.run_dir,
                    enabled=self.config.sync_enabled,
                    dry_run=self.config.sync_dry_run,
                    upload_workers=self.config.upload_workers,
                    access_token=resolved_drive_token,
                    folder_id=self.config.drive_folder_id,
                    api_base_url=self.config.drive_api_base_url,
                    upload_base_url=self.config.drive_upload_base_url,
                    chunk_bytes=self.config.sync_chunk_bytes,
                    resume_token=run_id,
                    retries=metrics["ops"]["retry_count"],
                    max_retries=self.config.sync_max_retries,
                    retry_backoff_sec=self.config.sync_retry_backoff_sec,
                    verify_sha256=self.config.sync_verify_sha256,
                    sync_lock_ttl_sec=self.config.sync_lock_ttl_sec,
                    check_public_permissions=self.config.drive_fail_on_public_permissions,
                )
            _finish_stage("enqueue_drive_sync", outputs=[self.run_dir / "sync_state.json"])
        except Exception as exc:
            _finish_stage("enqueue_drive_sync", error=str(exc))
            raise

        update_stage_cache_entry(
            stage_cache_payload,
            stage_id="enqueue_drive_sync",
            input_hash=compute_input_hash(
                {
                    "enabled": self.config.sync_enabled,
                    "dry_run": self.config.sync_dry_run,
                    "upload_workers": self.config.upload_workers,
                }
            ),
            outputs=stage_outputs_from_paths([self.run_dir / "sync_state.json"], self.run_dir),
            status="computed",
        )
        save_stage_cache(stage_cache_path, stage_cache_payload)

        sync_state_name = str(sync_state.get("state", "not_started"))
        manifest_committed_drive = bool(sync_state.get("manifest_committed_drive", False))
        if sync_state_name == "failed":
            warning_records.append(
                {
                    "code": "SYNC_FAILED",
                    "message": str(sync_state.get("last_error", "Drive sync failed")),
                    "severity": "warning",
                }
            )

        metrics["ops"]["sync_state"] = sync_state_name
        metrics["ops"]["manifest_committed_drive"] = manifest_committed_drive
        metrics["ops"]["retry_count"] = int(
            sync_state.get("retries", metrics["ops"]["retry_count"])
        )
        metrics["ops"]["resume_count"] = int(
            sync_state.get("resume_count", metrics["ops"]["resume_count"])
        )
        metrics["sync_state"] = sync_state_name
        _write_json(self.run_dir / "metrics.json", metrics)

        manifest_payload["ops"]["sync_state"] = sync_state_name
        manifest_payload["ops"]["retries"] = metrics["ops"]["retry_count"]
        manifest_payload["ops"]["resume_count"] = metrics["ops"]["resume_count"]
        manifest_payload["committed_drive"] = manifest_committed_drive
        manifest_payload["committed"] = bool(
            manifest_payload.get("committed_local", True)
        ) and bool(manifest_committed_drive or manifest_payload.get("committed", False))
        output_entries = collect_output_entries(self.run_dir, exclude_relpaths={"manifest.json"})
        manifest_payload["outputs"] = output_entries
        write_manifest(self.run_dir / "manifest.json", manifest_payload)

        warning_messages = [str(w.get("message", "")).strip() for w in warning_records]
        warning_messages = [w for w in warning_messages if w]
        _write_json(
            self.run_dir / "warnings.json",
            {
                "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
                "warnings": warning_records,
            },
        )
        _write_jsonl(self.run_dir / "warnings.jsonl", warning_records)

        _start_stage("retention_mark", [self.run_dir / "run_metadata.json"])
        retention_report_path = self.run_dir / "retention_report.json"
        try:
            retention_result = apply_ops_extract_retention(
                runs_base=self.run_dir.parent,
                lessons_path=lessons_path,
                failed_days=self.config.retention_failed_days,
                success_days=self.config.retention_success_days,
                trash_days=self.config.retention_trash_days,
                max_delete_per_run=self.config.retention_max_delete_per_run,
                dry_run=self.config.retention_dry_run,
                current_run_id=run_id,
            )
            _write_json(
                retention_report_path,
                {
                    "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
                    "retention_applied": True,
                    "dry_run": retention_result.dry_run,
                },
            )
            _finish_stage("retention_mark", outputs=[retention_report_path])
        except Exception as exc:
            warning_records.append(
                {
                    "code": "RETENTION_FAILED",
                    "message": str(exc),
                    "severity": "warning",
                }
            )
            _finish_stage("retention_mark", error=str(exc))

        _write_json(
            self.run_dir / "warnings.json",
            {
                "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
                "warnings": warning_records,
            },
        )
        _write_jsonl(self.run_dir / "warnings.jsonl", warning_records)

        if stage_starts:
            for dangling_stage in list(stage_starts.keys()):
                _finish_stage(
                    dangling_stage,
                    error=error_message or "aborted",
                )

        stage_order = {stage_id: idx for idx, stage_id in enumerate(STAGE_IDS)}
        recorded_stage_ids = {str(row.get("stage_id", "")) for row in trace_rows}
        now_iso = _now_iso()
        for stage_id in STAGE_IDS:
            if stage_id in recorded_stage_ids:
                continue
            trace_rows.append(
                {
                    "schema_version": OPS_EXTRACT_SCHEMA_VERSION,
                    "stage_id": stage_id,
                    "start_ts": now_iso,
                    "end_ts": now_iso,
                    "duration": 0.0,
                    "inputs": [],
                    "outputs": [],
                    "retry_count": 0,
                    "error": "skipped",
                }
            )

        ordered_trace = sorted(
            trace_rows,
            key=lambda row: stage_order.get(str(row.get("stage_id", "")), 10_000),
        )
        _write_jsonl(self.run_dir / "trace.jsonl", ordered_trace)

        final_expected_paths = expected_optional_paths(
            run_dir=self.run_dir, include_ocr_meta=ocr_used
        )
        metrics["ops"]["required_outputs_present"] = all(
            path.exists()
            for path in final_expected_paths
            if path.name not in {"manifest.json", "sync_state.json"}
        )
        _write_json(self.run_dir / "metrics.json", metrics)

        output_entries = collect_output_entries(self.run_dir, exclude_relpaths={"manifest.json"})
        manifest_payload["outputs"] = output_entries
        write_manifest(self.run_dir / "manifest.json", manifest_payload)

        warning_messages = [str(w.get("message", "")).strip() for w in warning_records]
        warning_messages = [w for w in warning_messages if w]

        answer = (
            f"Ops+Extract completed: files={len(input_paths)}, ocr_used={ocr_used}, "
            f"status={status}, total_chars={metrics['extract']['total_chars']}"
        )
        return OpsExtractOutcome(
            status=status,
            answer=answer,
            papers=papers,
            warning_records=warning_records,
            warning_messages=warning_messages,
            metrics=metrics,
            failure_analysis=failure_analysis,
            manifest=manifest_payload,
            ocr_used=ocr_used,
            needs_ocr_reason=needs_ocr_reason,
            text_source=overall_text_source,
            error=error_message,
            text_source_payload=json.loads(
                (ingestion_dir / "text_source.json").read_text(encoding="utf-8")
            ),
        )
