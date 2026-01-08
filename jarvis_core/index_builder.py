"""Index Builder.

Per RP-19, provides unified index building with manifest management.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from .storage import IndexRegistry
from .telemetry import init_logger


def build_index(
    query: str | None = None,
    source: str = "pubmed",
    output_dir: str = "data/index",
    max_papers: int = 50,
    local_pdf_dir: str | None = None,
) -> dict:
    """Build search index from papers.

    This is the unified entry point for index construction.
    Steps: fetch → extract → chunk → index → manifest update

    Args:
        query: PubMed query (required if source=pubmed).
        source: Data source ("pubmed" or "local").
        output_dir: Output directory.
        max_papers: Maximum papers to fetch.
        local_pdf_dir: Local PDF directory (if source=local).

    Returns:
        Build result with index_version, doc_count, etc.
    """
    run_id = str(uuid.uuid4())
    logger = init_logger(run_id)

    # Log start
    logger.log_event(
        event="INDEX_BUILD_START",
        event_type="ACTION",
        trace_id=run_id,
        payload={
            "query": query,
            "source": source,
            "max_papers": max_papers,
        },
    )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    errors = []
    papers = []
    chunks = []

    try:
        # Step 1: Fetch papers
        if source == "pubmed" and query:
            from jarvis_tools.papers import pubmed_esearch, pubmed_esummary

            pmids = pubmed_esearch(query, max_results=max_papers)
            papers = pubmed_esummary(pmids)

            logger.log_event(
                event="FETCH_COMPLETE",
                event_type="ACTION",
                trace_id=run_id,
                payload={"paper_count": len(papers)},
            )

        elif source == "local" and local_pdf_dir:
            # Local PDF mode - just list files
            pdf_path = Path(local_pdf_dir).expanduser()
            if pdf_path.exists():
                from jarvis_tools.papers import PaperRecord

                for pdf_file in pdf_path.glob("*.pdf"):
                    papers.append(PaperRecord(
                        paper_id=pdf_file.stem,
                        title=pdf_file.stem,
                        pdf_path=str(pdf_file),
                        source="local",
                    ))

        # Step 2: Extract text from PDFs
        from jarvis_tools.papers import extract_text_from_pdf, split_pages_into_chunks

        for paper in papers:
            if paper.pdf_path:
                try:
                    pages = extract_text_from_pdf(paper.pdf_path)
                    paper_chunks = split_pages_into_chunks(
                        pages,
                        paper_id=paper.paper_id,
                        pmid=paper.pmid,
                    )
                    chunks.extend(paper_chunks)
                except Exception as e:
                    errors.append({"paper_id": paper.paper_id, "error": str(e)})

        logger.log_event(
            event="EXTRACT_COMPLETE",
            event_type="ACTION",
            trace_id=run_id,
            payload={"chunk_count": len(chunks)},
        )

        # Step 3: Build TF-IDF index (simplified)
        index_version = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_dir = output_path / index_version
        version_dir.mkdir(parents=True, exist_ok=True)

        # Save chunks
        import json
        chunks_file = version_dir / "chunks.jsonl"
        with open(chunks_file, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")

        # Save papers metadata
        papers_file = version_dir / "papers.jsonl"
        with open(papers_file, "w", encoding="utf-8") as f:
            for paper in papers:
                f.write(json.dumps(paper.to_dict(), ensure_ascii=False) + "\n")

        # Step 4: Update manifest (only on success)
        registry = IndexRegistry(output_dir)
        registry.register(
            version=index_version,
            source=f"{source}:{query}" if query else source,
            doc_count=len(chunks),
            build_args={
                "query": query,
                "source": source,
                "max_papers": max_papers,
                "local_pdf_dir": local_pdf_dir,
            },
        )

        logger.log_event(
            event="INDEX_BUILD_END",
            event_type="ACTION",
            trace_id=run_id,
            payload={
                "index_version": index_version,
                "doc_count": len(chunks),
                "paper_count": len(papers),
            },
        )

        return {
            "success": True,
            "run_id": run_id,
            "index_version": index_version,
            "doc_count": len(chunks),
            "paper_count": len(papers),
            "output_dir": str(version_dir),
            "errors": errors,
        }

    except Exception as e:
        logger.log_event(
            event="INDEX_BUILD_ERROR",
            event_type="ACTION",
            trace_id=run_id,
            level="ERROR",
            payload={"error": str(e), "error_type": type(e).__name__},
        )

        return {
            "success": False,
            "run_id": run_id,
            "error": str(e),
            "errors": errors,
        }
