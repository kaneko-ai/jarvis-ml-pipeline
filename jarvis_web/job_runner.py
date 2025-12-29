"""Job runner implementations."""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jarvis_web import jobs
from jarvis_core.obs.logger import get_logger
from jarvis_core.obs import metrics


STEP_WEIGHTS = {
    "collect": 10,
    "download": 30,
    "extract": 25,
    "chunk": 25,
    "index": 10,
}

_chunks_lock = threading.Lock()
_jsonl_lock = threading.Lock()


def _normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def _stable_chunk_id(
    paper_id: str,
    section: str,
    char_start: int,
    char_end: int,
    text: str,
) -> str:
    payload = f"{paper_id}|{section}|{char_start}|{char_end}|{_normalize_text(text)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _notify_job_failed(job_id: str, reason: str) -> None:
    from jarvis_web.alerting import alert_event

    try:
        job = jobs.read_job(job_id)
    except FileNotFoundError:
        job = {"job_id": job_id}
    alert_event(
        event="job_failed",
        detail={
            "job_id": job_id,
            "job_type": job.get("type"),
            "status": job.get("status"),
            "error": reason,
            "counts": job.get("counts", {}),
            "payload": job.get("payload", {}),
        },
        level="error",
    )


def _set_step_progress(job_id: str, base: int, weight: int, done: int, total: int) -> None:
    if total <= 0:
        jobs.set_progress(job_id, base + weight)
        return
    progress = base + int(weight * (done / total))
    jobs.set_progress(job_id, progress)


def _append_chunk_lines(chunks_path: Path, chunk_lines: List[Dict[str, Any]]) -> None:
    chunks_path.parent.mkdir(parents=True, exist_ok=True)
    with _chunks_lock:
        with open(chunks_path, "a", encoding="utf-8") as f:
            for chunk in chunk_lines:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def _append_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _jsonl_lock:
        with open(path, "a", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _split_sentences(text: str) -> List[str]:
    normalized = text.replace("\n", " ").strip()
    sentences = [s.strip() for s in normalized.split(".") if s.strip()]
    return [s + "." if not s.endswith(".") else s for s in sentences]


def _infer_claim_type(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["method", "materials", "procedure"]):
        return "method"
    if any(word in lowered for word in ["result", "finding", "observed", "increased", "decreased"]):
        return "result"
    if any(word in lowered for word in ["conclude", "conclusion", "suggest"]):
        return "conclusion"
    if any(word in lowered for word in ["limitation", "limited", "weakness"]):
        return "limitation"
    return "background"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_collect_and_ingest(job_id: str, payload: Dict[str, Any]) -> None:
    from jarvis_tools.papers.collector import collect_papers
    from jarvis_core.ingestion.pipeline import TextChunker
    from jarvis_core.search import get_search_engine
    from jarvis_web import dedup
    from jarvis_web.health import start_worker_heartbeat
    from jarvis_core.oa import OAResolver
    from jarvis_core.metadata import audit_records
    from jarvis_core.dedup import DedupEngine
    from jarvis_core.provenance.aligner import align_claim_to_chunks
    from jarvis_core.provenance.schema import ClaimUnit, EvidenceItem
    from jarvis_core.scoring.paper_score import score_paper
    from jarvis_core.repro.run_manifest import create_run_manifest

    query = payload.get("query", "")
    max_results = int(payload.get("max_results", 50))
    oa_only = bool(payload.get("oa_only", False))

    heartbeat_stop = threading.Event()
    heartbeat_thread = threading.Thread(
        target=start_worker_heartbeat,
        args=(heartbeat_stop,),
        daemon=True,
    )
    heartbeat_thread.start()

    try:
        jobs.set_status(job_id, "running")
        jobs.set_step(job_id, "collect")
        jobs.append_event(job_id, {"message": f"collecting: {query}", "level": "info"})
        result = collect_papers(query=query, max_results=max_results, oa_only=oa_only)
    except Exception as exc:
        jobs.set_error(job_id, f"collect failed: {exc}")
        jobs.set_status(job_id, "failed")
        logger.error("collect failed", step="Collecting", exc=exc)
        metrics.record_run_end(
            run_id=run_id,
            job_id=job_id,
            status="failed",
            duration_ms=(time.time() - run_start) * 1000,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        return

    jobs.inc_counts(job_id, found=result.total_found)
    if result.warnings:
        for warning in result.warnings:
            jobs.append_event(job_id, {"message": warning.get("message", "warning"), "level": "warning"})
            logger.warning(warning.get("message", "warning"), step="Collecting")

    jobs.set_progress(job_id, STEP_WEIGHTS["collect"])
    metrics.record_progress(run_id, "Collecting", STEP_WEIGHTS["collect"])
    logger.step_end("Collecting", data={"found": result.total_found})

    research_dir = Path("data/research") / job_id
    research_dir.mkdir(parents=True, exist_ok=True)
    papers_path = research_dir / "papers.jsonl"
    chunks_path = research_dir / "chunks.jsonl"
    claims_path = research_dir / "claims.jsonl"
    scores_path = research_dir / "scores.json"
    audit_summary_path = research_dir / "audit_summary.json"
    manifest_path = research_dir / "manifest.json"

    oa_resolver = OAResolver(unpaywall_email=os.getenv("UNPAYWALL_EMAIL"))
    papers: List[Dict[str, Any]] = []
    oa_count = 0
    for paper in result.papers:
        record = paper.to_dict()
        record["pdf_url"] = paper.pdf_url or ""
        record["fulltext_url"] = paper.xml_url or ""
        record.update(oa_resolver.resolve(record))
        if record.get("is_oa") or record.get("oa_status") == "oa":
            oa_count += 1
        papers.append(record)
    if papers:
        _append_jsonl(papers_path, papers)

    audited_papers, audit_summary = audit_records(papers)
    with open(audit_summary_path, "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, ensure_ascii=False, indent=2)

    dedup_engine = DedupEngine()
    dedup_result = dedup_engine.deduplicate(audited_papers)
    canonical_papers = dedup_result.canonical_papers
    jobs.inc_counts(job_id, deduped=dedup_result.merged_count, canonical_papers=len(canonical_papers))
    jobs.inc_counts(job_id, oa_count=oa_count)
    _append_jsonl(research_dir / "canonical_papers.jsonl", canonical_papers)

    total_papers = len(result.papers)
    downloaded: List[Tuple[Any, str]] = []

        try:
            result = collect_papers(query=query, max_results=max_results, oa_only=oa_only)
        except Exception as exc:
            jobs.set_error(job_id, f"collect failed: {exc}")
            jobs.set_status(job_id, "failed")
            _notify_job_failed(job_id, f"collect failed: {exc}")
            return

        jobs.inc_counts(job_id, found=result.total_found)
        if result.warnings:
            for warning in result.warnings:
                jobs.append_event(job_id, {"message": warning.get("message", "warning"), "level": "warning"})

        jobs.set_progress(job_id, STEP_WEIGHTS["collect"])

        total_papers = len(result.papers)
        downloaded: List[Tuple[Any, str]] = []

        jobs.set_step(job_id, "download")
        for idx, paper in enumerate(result.papers, start=1):
            try:
                text = "\n\n".join([p for p in [paper.title, paper.abstract] if p])
                if not text.strip():
                    jobs.inc_counts(job_id, failed=1)
                    jobs.append_event(job_id, {"message": f"no text for PMID {paper.pmid}", "level": "warning"})
                else:
                    downloaded.append((paper, text))
                    jobs.inc_counts(job_id, downloaded=1)
            except Exception as exc:
                jobs.inc_counts(job_id, failed=1)
                jobs.append_event(job_id, {"message": f"download failed for PMID {paper.pmid}: {exc}", "level": "warning"})
            _set_step_progress(job_id, STEP_WEIGHTS["collect"], STEP_WEIGHTS["download"], idx, total_papers)

        jobs.set_step(job_id, "extract")
        extracted: List[Tuple[Any, str]] = []
        for idx, (paper, text) in enumerate(downloaded, start=1):
            try:
                extracted.append((paper, text))
                jobs.inc_counts(job_id, extracted=1)
            except Exception as exc:
                jobs.inc_counts(job_id, failed=1)
                jobs.append_event(job_id, {"message": f"extract failed for PMID {paper.pmid}: {exc}", "level": "warning"})
            _set_step_progress(job_id, 40, STEP_WEIGHTS["extract"], idx, len(downloaded))

        jobs.set_step(job_id, "chunk")
        chunker = TextChunker()
        chunks_path = Path("data/chunks.jsonl")
        try:
            redis_client = dedup.get_redis()
        except Exception as exc:
            redis_client = None
            jobs.append_event(job_id, {"message": f"chunk dedupe unavailable: {exc}", "level": "warning"})

        for idx, (paper, text) in enumerate(extracted, start=1):
            try:
                paper_id = paper.pmcid or f"PMID:{paper.pmid}"
                chunks = chunker.chunk(text=text, paper_id=paper_id)
                chunk_lines = []
                appended = 0
                for chunk in chunks:
                    chunk_id = _stable_chunk_id(
                        paper_id=paper_id,
                        section=chunk.section,
                        char_start=chunk.char_start,
                        char_end=chunk.char_end,
                        text=chunk.text,
                    )
                    if redis_client is not None:
                        try:
                            if not dedup.claim_chunk_seen(redis_client, chunk_id):
                                continue
                        except Exception as exc:
                            jobs.append_event(job_id, {"message": f"chunk dedupe error: {exc}", "level": "warning"})
                            redis_client = None
                    chunk_data = chunk.to_dict()
                    chunk_data["chunk_id"] = chunk_id
                    chunk_data["paper_id"] = paper_id
                    chunk_data["paper_title"] = paper.title or paper_id
                    chunk_lines.append(chunk_data)
                    appended += 1
                if chunk_lines:
                    _append_chunk_lines(chunks_path, chunk_lines)
                jobs.inc_counts(job_id, chunked=appended)
            except Exception as exc:
                jobs.inc_counts(job_id, failed=1)
                jobs.append_event(job_id, {"message": f"chunk failed for PMID {paper.pmid}: {exc}", "level": "warning"})
            _set_step_progress(job_id, 65, STEP_WEIGHTS["chunk"], idx, len(extracted))

        jobs.set_step(job_id, "index")
            jobs.inc_counts(job_id, failed=1)
            jobs.append_event(job_id, {"message": f"extract failed for PMID {paper.pmid}: {exc}", "level": "warning"})
            logger.warning(f"extract failed for PMID {paper.pmid}", step="Extracting", data={"error": str(exc)})
        _set_step_progress(job_id, 40, STEP_WEIGHTS["extract"], idx, len(downloaded))
    logger.step_end("Extracting", data={"extracted": len(extracted)})
    metrics.record_step_duration(run_id, "Extracting", (time.time() - step_start) * 1000)

    jobs.set_step(job_id, "chunk")
    step_start = time.time()
    logger.step_start("Chunking")
    chunker = TextChunker()
    for idx, (paper, text) in enumerate(extracted, start=1):
        try:
            engine = get_search_engine()
            indexed = engine.load_chunks(chunks_path)
            jobs.inc_counts(job_id, indexed=indexed)
            jobs.append_event(job_id, {"message": f"indexed {indexed} chunks", "level": "info"})
        except Exception as exc:
            jobs.set_error(job_id, f"index failed: {exc}")
            jobs.set_status(job_id, "failed")
            _notify_job_failed(job_id, f"index failed: {exc}")
            return

        job = jobs.read_job(job_id)
        counts = job.get("counts", {})
        if counts.get("found", 0) > 0 and counts.get("chunked", 0) == 0:
            message = "integrity_failed: found>0 but chunked==0"
            jobs.set_error(job_id, message)
            jobs.set_status(job_id, "failed")
            jobs.append_event(job_id, {"message": message, "level": "error"})
            _notify_job_failed(job_id, message)
            return

        jobs.set_progress(job_id, 100)
        jobs.set_step(job_id, "done")
        jobs.set_status(job_id, "success")
        jobs.append_event(job_id, {"message": "job complete", "level": "info"})
    finally:
        heartbeat_stop.set()
    claims: List[Dict[str, Any]] = []
    scores: Dict[str, Any] = {}
    chunk_records: Dict[str, List[Dict[str, Any]]] = {}
    if chunks_path.exists():
        with open(chunks_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                chunk = json.loads(line)
                chunk_records.setdefault(chunk.get("paper_id", ""), []).append(chunk)

    for paper in canonical_papers:
        paper_id = paper.get("canonical_paper_id") or paper.get("paper_id") or ""
        chunk_key = paper.get("pmcid") or (
            f"PMID:{paper.get('pmid')}" if paper.get("pmid") else paper_id
        )
        paper_claims: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(_split_sentences(paper.get("abstract") or "")):
            if not sentence:
                continue
            claim_id = f"{paper_id}-claim-{idx}"
            claim_type = _infer_claim_type(sentence)
            evidence_candidates = align_claim_to_chunks(sentence, chunk_records.get(chunk_key, []))
            if not evidence_candidates and chunk_records.get(chunk_key):
                fallback = chunk_records[chunk_key][0]
                evidence_candidates = [
                    EvidenceItem(
                        chunk_id=fallback.get("chunk_id", ""),
                        locator={
                            "section": fallback.get("section") or "",
                            "paragraph_index": fallback.get("paragraph_index") or 0,
                            "sentence_index": 0,
                        },
                        quote=" ".join((fallback.get("text") or "").split()[:25]),
                        score=0.1,
                    )
                ]
            if not evidence_candidates:
                evidence_candidates = [
                    EvidenceItem(
                        chunk_id="unknown",
                        locator={"section": "", "paragraph_index": 0, "sentence_index": 0},
                        quote=sentence,
                        score=0.0,
                    )
                ]
            evidence_items = [
                EvidenceItem(
                    chunk_id=item.chunk_id,
                    locator=item.locator,
                    quote=item.quote,
                    score=item.score,
                ).to_dict()
                if hasattr(item, "chunk_id")
                else item.to_dict()
                for item in evidence_candidates
            ]
            claim = ClaimUnit(
                claim_id=claim_id,
                paper_id=paper_id,
                claim_text=sentence,
                claim_type=claim_type,
                evidence=[
                    EvidenceItem(
                        chunk_id=item["chunk_id"],
                        locator=item["locator"],
                        quote=item["quote"],
                        score=item["score"],
                    )
                    for item in evidence_items
                ],
                generated_at=_now(),
                model_info={"summarizer": "heuristic-sentence-splitter", "aligner": "heuristic-v1"},
            ).to_dict()
            if evidence_items and max(item["score"] for item in evidence_items) < 0.4:
                claim["audit_flags"] = ["weak_evidence"]
            paper_claims.append(claim)

        claims.extend(paper_claims)
        jobs.inc_counts(job_id, claims=len(paper_claims))
        if any("weak_evidence" in (claim.get("audit_flags") or []) for claim in paper_claims):
            paper.setdefault("audit_flags", []).append("weak_evidence")
        score_result = score_paper(paper, paper_claims, query=query, domain=payload.get("domain", ""))
        scores[paper_id] = score_result.to_dict()

    if claims:
        _append_jsonl(claims_path, claims)
    with open(scores_path, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)

    manifest = create_run_manifest(
        run_id=job_id,
        targets={
            "query": query,
            "filters": {},
            "max_results": max_results,
            "oa_only": oa_only,
            "domain": payload.get("domain", ""),
        },
        resolver_versions={
            "oa_resolver": "v1",
            "dedup_engine": "v1",
            "scorer": "v1",
        },
        model_info={"embedder": "local-heuristic", "summarizer": "heuristic-sentence-splitter"},
        index_version={"generated_at": _now(), "path": str(chunks_path)},
        input_counts={
            "found": result.total_found,
            "downloaded": len(downloaded),
            "extracted": len(extracted),
            "chunked": jobs.read_job(job_id)["counts"].get("chunked", 0),
        },
        output_counts={
            "deduped": dedup_result.merged_count,
            "canonical_papers": len(canonical_papers),
            "claims": len(claims),
        },
        warnings_summary={"audit": audit_summary},
    )
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest.to_dict(), f, ensure_ascii=False, indent=2)

    jobs.update_job(job_id, manifest_path=str(manifest_path))

    try:
        from jarvis_core.kb import ingest_run, generate_weekly_pack

        kb_result = ingest_run(research_dir, run_id=job_id)
        jobs.append_event(job_id, {"message": f"kb updated: {kb_result}", "level": "info"})
        pack_path = generate_weekly_pack()
        jobs.append_event(job_id, {"message": f"weekly pack: {pack_path}", "level": "info"})
    except Exception as exc:  # pragma: no cover - best effort
        jobs.append_event(job_id, {"message": f"kb update skipped: {exc}", "level": "warning"})

    jobs.set_progress(job_id, 100)
    _maybe_generate_exports(job_id, payload)
    jobs.set_step(job_id, "done")
    jobs.set_status(job_id, "success")
    jobs.append_event(job_id, {"message": "job complete", "level": "info"})
    logger.step_end("RunComplete", data={"status": "success"})
    metrics.record_counts(run_id, jobs.read_job(job_id)["counts"])
    metrics.record_run_end(
        run_id=run_id,
        job_id=job_id,
        status="success",
        duration_ms=(time.time() - run_start) * 1000,
    )


def run_job(job_id: str) -> None:
    job = jobs.read_job(job_id)
    job_type = job.get("type")
    payload = job.get("payload", {})
    schedule_run_id = payload.get("schedule_run_id")

    try:
        if schedule_run_id:
            from jarvis_core.scheduler import runner as schedule_runner

            schedule_runner.mark_run_running(schedule_run_id)

        if job_type == "collect_and_ingest":
            run_collect_and_ingest(job_id, payload)
        elif job_type == "writing_generate":
            run_writing_generate(job_id, payload)
        else:
            jobs.set_error(job_id, f"unknown job type: {job_type}")
            jobs.set_status(job_id, "failed")
            _notify_job_failed(job_id, f"unknown job type: {job_type}")
    except Exception as exc:
        trimmed = "\n".join(traceback.format_exc().splitlines()[-6:])
        jobs.append_event(job_id, {"message": trimmed, "level": "error"})
        jobs.set_error(job_id, f"{type(exc).__name__}: {exc}")
        jobs.set_status(job_id, "failed")
        _notify_job_failed(job_id, f"{type(exc).__name__}: {exc}")
    finally:
        if schedule_run_id:
            from jarvis_core.obs import alert as obs_alert
            from jarvis_core.scheduler import retry as schedule_retry
            from jarvis_core.scheduler import store as schedule_store

            latest = jobs.read_job(job_id)
            status = latest.get("status")
            error = latest.get("error")
            run = schedule_store.read_run(schedule_run_id)
            if not run:
                return
            schedule_id = run.get("schedule_id")
            schedule = schedule_store.get_schedule(schedule_id) if schedule_id else None
            if status == "success":
                schedule_store.update_run(schedule_run_id, status="success", error=None, next_retry_at=None)
                schedule_store.update_schedule_status(schedule_id, "success")
                return
            attempts = (run.get("attempts", 0) or 0) + 1
            schedule_store.update_run(schedule_run_id, status="failed", error=error, attempts=attempts)
            if not schedule:
                return
            limits = schedule.get("limits", {})
            max_retries = int(limits.get("max_retries", 0))
            if attempts > max_retries:
                schedule_store.update_schedule(schedule_id, {"enabled": False, "degraded": True})
                obs_alert(
                    "schedule_failed",
                    "high",
                    f"Schedule {schedule_id} disabled after {attempts} failures",
                )
                return
            next_retry = schedule_retry.next_retry_at(attempts, int(limits.get("cooldown_minutes_after_failure", 30)))
            schedule_store.update_run(schedule_run_id, next_retry_at=next_retry)
