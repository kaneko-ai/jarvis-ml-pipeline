"""Orchestrator for ops_extract mode."""

from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis_core.ingestion.normalizer import TextNormalizer
from jarvis_core.ingestion.rasterize_pdf import rasterize_pdf_to_images
from jarvis_core.ingestion.robust_extractor import ExtractionResult, RobustPDFExtractor
from jarvis_core.ingestion.yomitoku_cli import check_yomitoku_available, run_yomitoku_cli

from .contracts import OpsExtractConfig, expected_optional_paths
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
from .needs_ocr import NeedsOcrDecision, decide_needs_ocr, summarize_page_metrics
from .preflight import PreflightReport, run_preflight_checks


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
    normalized_pdf_text: str
    error: str | None = None


@dataclass
class _DocOcrResult:
    doc_index: int
    pdf_path: Path
    normalized_ocr_text: str
    ocr_text_path: str | None
    figure_count: int
    ocr_meta: dict[str, Any]
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
            page_metrics = summarize_page_metrics(extract_result.pages)
            decision = decide_needs_ocr(
                total_chars_extracted=int(page_metrics["total_chars_extracted"]),
                chars_per_page_mean=float(page_metrics["chars_per_page_mean"]),
                empty_page_ratio=float(page_metrics["empty_page_ratio"]),
                exceptions_in_text_extract=extract_result.warnings,
                thresholds=config.thresholds,
            )
            normalized = normalizer.normalize(extract_result.text or "").normalized
            return _DocParseResult(
                doc_index=doc_index,
                pdf_path=pdf_path,
                extract_result=extract_result,
                decision=decision,
                page_metrics=page_metrics,
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
                normalized_pdf_text="",
                error=str(exc),
            )

    @staticmethod
    def _ocr_document(
        parse_result: _DocParseResult,
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
            page_output_dir = doc_ocr_root / "input_pages"
            raster_meta = rasterize_pdf_to_images(
                pdf_path=pdf_path,
                output_dir=page_output_dir,
            )
            yomi_output_dir = doc_ocr_root / "yomitoku"
            yomi_result = run_yomitoku_cli(
                input_path=pdf_path,
                output_dir=yomi_output_dir,
                mode=config.yomitoku_mode,
                figure=config.yomitoku_figure,
            )
            normalized_ocr = normalizer.normalize(yomi_result.get("text", "") or "").normalized
            ocr_text_path = yomi_result.get("text_path")
            ocr_meta = {
                "file": str(pdf_path),
                "decision": asdict(decision),
                "raster": raster_meta,
                "yomitoku": {
                    "text_path": ocr_text_path,
                    "returncode": yomi_result.get("returncode"),
                },
            }
            return _DocOcrResult(
                doc_index=parse_result.doc_index,
                pdf_path=pdf_path,
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
        started_at = datetime.now(timezone.utc).isoformat()
        started_perf = time.perf_counter()
        input_paths = _collect_paths(input_paths)

        warning_records: list[dict[str, Any]] = []
        papers: list[dict[str, Any]] = []
        text_entries: list[dict[str, Any]] = []
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

        ingestion_dir = self.run_dir / "ingestion"
        ocr_dir = self.run_dir / "ocr"
        ingestion_dir.mkdir(parents=True, exist_ok=True)

        lessons_path = Path(self.config.lessons_path) if self.config.lessons_path else None
        preflight_report: PreflightReport = run_preflight_checks(
            input_paths=input_paths,
            config=self.config,
            lessons_path=lessons_path,
        )
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
            if not input_paths:
                raise RuntimeError("No input PDF files provided for ops_extract mode")

            missing_inputs = [str(path) for path in input_paths if not path.exists()]
            if missing_inputs:
                raise FileNotFoundError(f"Input file not found: {missing_inputs}")

            parse_results: list[_DocParseResult] = []
            with ThreadPoolExecutor(max_workers=max(1, int(self.config.parse_workers))) as pool:
                future_map = {
                    pool.submit(self._extract_document, idx, pdf_path, self.config): idx
                    for idx, pdf_path in enumerate(input_paths)
                }
                for future in as_completed(future_map):
                    parse_results.append(future.result())

            parse_results.sort(key=lambda item: item.doc_index)
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

            ocr_by_index: dict[int, _DocOcrResult] = {}
            if needs_ocr_docs and not run_errors:
                with ThreadPoolExecutor(max_workers=max(1, int(self.config.ocr_workers))) as pool:
                    future_map = {
                        pool.submit(self._ocr_document, item, self.config, ocr_dir): item.doc_index
                        for item in needs_ocr_docs
                    }
                    for future in as_completed(future_map):
                        ocr_result = future.result()
                        ocr_by_index[ocr_result.doc_index] = ocr_result

            method_flags: list[str] = []
            needs_ocr_reasons: list[str] = []

            for parse_result in parse_results:
                pdf_path = parse_result.pdf_path
                paper_id = f"ops_extract_{pdf_path.stem}"
                papers.append(
                    {
                        "paper_id": paper_id,
                        "title": pdf_path.stem,
                        "year": datetime.now().year,
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
                        normalized = parse_result.normalized_pdf_text
                        text_source = "pdf_text"
                        ocr_text_path = None
                    else:
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
                        "run_id": run_id,
                        "project": project,
                        "docs": ocr_meta_by_doc,
                    },
                )

            combined_text = "\n\n".join(x for x in combined_sections if x).strip()
            if not combined_text:
                combined_text = "# Extracted Text\n\n(no text extracted)"
            (ingestion_dir / "text.md").write_text(combined_text, encoding="utf-8")

            if ocr_used and any(flag == "pdf_text" for flag in method_flags):
                overall_text_source = "mixed"
            elif ocr_used:
                overall_text_source = "ocr_yomitoku"
            else:
                overall_text_source = "pdf_text"

            text_source_payload = {
                "run_id": run_id,
                "project": project,
                "source": overall_text_source,
                "entries": text_entries,
            }
            _write_json(ingestion_dir / "text_source.json", text_source_payload)

            quality_warnings = build_text_quality_warnings(combined_text)
            warning_records.extend(quality_warnings)

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
                        "run_id": run_id,
                        "project": project,
                        "source": "unknown",
                        "entries": [],
                    },
                )
            overall_text_source = "unknown"
            needs_ocr_reasons = ["runtime_error"]

        finished_at = datetime.now(timezone.utc).isoformat()
        duration_sec = time.perf_counter() - started_perf

        failure_analysis = build_failure_analysis(error_message, status=status)
        _write_json(self.run_dir / "failure_analysis.json", failure_analysis)
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

        _write_json(self.run_dir / "warnings.json", {"warnings": warning_records})
        _write_jsonl(self.run_dir / "warnings.jsonl", warning_records)

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
        )
        _write_json(self.run_dir / "metrics.json", metrics)

        run_metadata = {
            "run_id": run_id,
            "project": project,
            "mode": "ops_extract",
            "created_at": started_at,
            "finished_at": finished_at,
            "status": status,
            "config": asdict(self.config),
            "preflight": {
                "passed": preflight_report.passed,
                "errors": preflight_report.errors,
                "warnings": preflight_report.warnings,
                "checks": preflight_report.checks,
            },
        }
        _write_json(self.run_dir / "run_metadata.json", run_metadata)

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
        )
        write_manifest(self.run_dir / "manifest.json", manifest_payload)

        sync_state = sync_run_to_drive(
            run_dir=self.run_dir,
            enabled=self.config.sync_enabled,
            dry_run=self.config.sync_dry_run,
            upload_workers=self.config.upload_workers,
            access_token=self.config.drive_access_token or os.getenv("GOOGLE_DRIVE_ACCESS_TOKEN"),
            folder_id=self.config.drive_folder_id,
            retries=metrics["ops"]["retry_count"],
            max_retries=self.config.sync_max_retries,
            retry_backoff_sec=self.config.sync_retry_backoff_sec,
            verify_sha256=self.config.sync_verify_sha256,
        )

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
        output_entries = collect_output_entries(self.run_dir, exclude_relpaths={"manifest.json"})
        manifest_payload["outputs"] = output_entries
        write_manifest(self.run_dir / "manifest.json", manifest_payload)

        warning_messages = [str(w.get("message", "")).strip() for w in warning_records]
        warning_messages = [w for w in warning_messages if w]
        _write_json(self.run_dir / "warnings.json", {"warnings": warning_records})
        _write_jsonl(self.run_dir / "warnings.jsonl", warning_records)

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
