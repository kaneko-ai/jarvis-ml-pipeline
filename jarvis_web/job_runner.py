"""Job runner implementations."""
from __future__ import annotations

import json
import threading
import traceback
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jarvis_web import jobs


STEP_WEIGHTS = {
    "collect": 10,
    "download": 30,
    "extract": 25,
    "chunk": 25,
    "index": 10,
}

_chunks_lock = threading.Lock()


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


def run_collect_and_ingest(job_id: str, payload: Dict[str, Any]) -> None:
    from jarvis_tools.papers.collector import collect_papers
    from jarvis_core.ingestion.pipeline import TextChunker
    from jarvis_core.search import get_search_engine

    query = payload.get("query", "")
    max_results = int(payload.get("max_results", 50))
    oa_only = bool(payload.get("oa_only", False))

    jobs.set_status(job_id, "running")
    jobs.set_step(job_id, "collect")
    jobs.append_event(job_id, {"message": f"collecting: {query}", "level": "info"})

    try:
        result = collect_papers(query=query, max_results=max_results, oa_only=oa_only)
    except Exception as exc:
        jobs.set_error(job_id, f"collect failed: {exc}")
        jobs.set_status(job_id, "failed")
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
        _set_step_progress(job_id, 65, STEP_WEIGHTS["chunk"], idx, len(extracted))

    jobs.set_step(job_id, "index")
    try:
        engine = get_search_engine()
        indexed = engine.load_chunks(chunks_path)
        jobs.inc_counts(job_id, indexed=indexed)
        jobs.append_event(job_id, {"message": f"indexed {indexed} chunks", "level": "info"})
    except Exception as exc:
        jobs.set_error(job_id, f"index failed: {exc}")
        jobs.set_status(job_id, "failed")
        return

    jobs.set_progress(job_id, 100)
    jobs.set_step(job_id, "done")
    jobs.set_status(job_id, "success")
    jobs.append_event(job_id, {"message": "job complete", "level": "info"})


def run_job(job_id: str) -> None:
    job = jobs.read_job(job_id)
    job_type = job.get("type")
    payload = job.get("payload", {})

    try:
        if job_type == "collect_and_ingest":
            run_collect_and_ingest(job_id, payload)
        else:
            jobs.set_error(job_id, f"unknown job type: {job_type}")
            jobs.set_status(job_id, "failed")
    except Exception as exc:
        trimmed = "\n".join(traceback.format_exc().splitlines()[-6:])
        jobs.append_event(job_id, {"message": trimmed, "level": "error"})
        jobs.set_error(job_id, f"{type(exc).__name__}: {exc}")
        jobs.set_status(job_id, "failed")
