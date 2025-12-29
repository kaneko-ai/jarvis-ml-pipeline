"""Job runner implementations."""
from __future__ import annotations

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

    run_id = job_id
    logger = get_logger(run_id=run_id, job_id=job_id, component="scheduler")
    metrics.record_run_start(run_id=run_id, job_id=job_id, component="scheduler")
    run_start = time.time()

    jobs.set_status(job_id, "running")
    jobs.set_step(job_id, "collect")
    jobs.append_event(job_id, {"message": f"collecting: {query}", "level": "info"})
    logger.step_start("Collecting", data={"query": query, "max_results": max_results, "oa_only": oa_only})

    try:
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

    jobs.set_step(job_id, "download")
    step_start = time.time()
    logger.step_start("Downloading")
    for idx, paper in enumerate(result.papers, start=1):
        try:
            text = "\n\n".join([p for p in [paper.title, paper.abstract] if p])
            if not text.strip():
                jobs.inc_counts(job_id, failed=1)
                jobs.append_event(job_id, {"message": f"no text for PMID {paper.pmid}", "level": "warning"})
                logger.warning(f"no text for PMID {paper.pmid}", step="Downloading")
            else:
                downloaded.append((paper, text))
                jobs.inc_counts(job_id, downloaded=1)
        except Exception as exc:
            jobs.inc_counts(job_id, failed=1)
            jobs.append_event(job_id, {"message": f"download failed for PMID {paper.pmid}: {exc}", "level": "warning"})
            logger.warning(f"download failed for PMID {paper.pmid}", step="Downloading", data={"error": str(exc)})
        _set_step_progress(job_id, STEP_WEIGHTS["collect"], STEP_WEIGHTS["download"], idx, total_papers)
    logger.step_end("Downloading", data={"downloaded": len(downloaded)})
    metrics.record_step_duration(run_id, "Downloading", (time.time() - step_start) * 1000)

    jobs.set_step(job_id, "extract")
    step_start = time.time()
    logger.step_start("Extracting")
    extracted: List[Tuple[Any, str]] = []
    for idx, (paper, text) in enumerate(downloaded, start=1):
        try:
            extracted.append((paper, text))
            jobs.inc_counts(job_id, extracted=1)
        except Exception as exc:
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
            paper_id = paper.pmcid or f"PMID:{paper.pmid}"
            chunks = chunker.chunk(text=text, paper_id=paper_id)
            chunk_lines = []
            for chunk in chunks:
                chunk_data = chunk.to_dict()
                chunk_data["paper_id"] = paper_id
                chunk_data["paper_title"] = paper.title or paper_id
                chunk_lines.append(chunk_data)
            _append_chunk_lines(chunks_path, chunk_lines)
            jobs.inc_counts(job_id, chunked=len(chunk_lines))
        except Exception as exc:
            jobs.inc_counts(job_id, failed=1)
            jobs.append_event(job_id, {"message": f"chunk failed for PMID {paper.pmid}: {exc}", "level": "warning"})
            logger.warning(f"chunk failed for PMID {paper.pmid}", step="Chunking", data={"error": str(exc)})
        _set_step_progress(job_id, 65, STEP_WEIGHTS["chunk"], idx, len(extracted))
    logger.step_end("Chunking")
    metrics.record_step_duration(run_id, "Chunking", (time.time() - step_start) * 1000)

    jobs.set_step(job_id, "index")
    step_start = time.time()
    logger.step_start("Indexing")
    try:
        engine = get_search_engine()
        indexed = engine.load_chunks(chunks_path)
        jobs.inc_counts(job_id, indexed=indexed)
        jobs.append_event(job_id, {"message": f"indexed {indexed} chunks", "level": "info"})
        logger.info(f"indexed {indexed} chunks", step="Indexing", data={"indexed": indexed})
    except Exception as exc:
        jobs.set_error(job_id, f"index failed: {exc}")
        jobs.set_status(job_id, "failed")
        logger.error("index failed", step="Indexing", exc=exc)
        metrics.record_run_end(
            run_id=run_id,
            job_id=job_id,
            status="failed",
            duration_ms=(time.time() - run_start) * 1000,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        return
    logger.step_end("Indexing")
    metrics.record_step_duration(run_id, "Indexing", (time.time() - step_start) * 1000)

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

    jobs.set_progress(job_id, 100)
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
    logger = get_logger(run_id=job_id, job_id=job_id, component="scheduler")
    start_time = time.time()

    try:
        if job_type == "collect_and_ingest":
            run_collect_and_ingest(job_id, payload)
        else:
            jobs.set_error(job_id, f"unknown job type: {job_type}")
            jobs.set_status(job_id, "failed")
            logger.error("unknown job type", step="Dispatch", data={"job_type": job_type})
            metrics.record_run_end(
                run_id=job_id,
                job_id=job_id,
                status="failed",
                duration_ms=(time.time() - start_time) * 1000,
                error_type="UnknownJobType",
                error_message=str(job_type),
            )
    except Exception as exc:
        trimmed = "\n".join(traceback.format_exc().splitlines()[-6:])
        jobs.append_event(job_id, {"message": trimmed, "level": "error"})
        jobs.set_error(job_id, f"{type(exc).__name__}: {exc}")
        jobs.set_status(job_id, "failed")
        logger.error("job crashed", step="Dispatch", exc=exc)
        metrics.record_run_end(
            run_id=job_id,
            job_id=job_id,
            status="failed",
            duration_ms=(time.time() - start_time) * 1000,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
