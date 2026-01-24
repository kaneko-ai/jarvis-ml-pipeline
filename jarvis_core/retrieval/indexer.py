"""Indexing for hybrid retrieval v2."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from jarvis_core.retrieval.bm25_store import BM25Store
from jarvis_core.retrieval.chunker import Chunker
from jarvis_core.retrieval.embeddings import EmbeddingProvider, HashEmbeddingProvider
from jarvis_core.retrieval.schema import Chunk, ChunkMeta, Provenance
from jarvis_core.retrieval.vector_store import VectorStore


@dataclass
class IndexManifest:
    created_at: str
    embedding_model: str
    chunks: int
    indexed_runs: list[str]
    kb_indexed_at: str | None

    def to_dict(self) -> dict:
        return {
            "created_at": self.created_at,
            "embedding_model": self.embedding_model,
            "chunks": self.chunks,
            "indexed_runs": self.indexed_runs,
            "kb_indexed_at": self.kb_indexed_at,
        }


class RetrievalIndexer:
    def __init__(
        self,
        index_dir: Path | str = Path("data/index/v2"),
        kb_dir: Path | str = Path("data/kb/notes"),
        runs_dir: Path | str = Path("data/runs"),
        legacy_runs_dir: Path | str = Path("logs/runs"),
        embedding_provider: EmbeddingProvider | None = None,
    ):
        self.index_dir = Path(index_dir)
        self.kb_dir = Path(kb_dir)
        self.runs_dir = Path(runs_dir)
        self.legacy_runs_dir = Path(legacy_runs_dir)
        self.embedding_provider = embedding_provider or HashEmbeddingProvider()
        self.vector_path = self.index_dir / "vector.faiss"
        self.bm25_path = self.index_dir / "bm25.sqlite"
        self.chunks_path = self.index_dir / "chunks.jsonl"
        self.manifest_path = self.index_dir / "manifest.json"
        self.chunker = Chunker()

    def _load_manifest(self) -> IndexManifest | None:
        if not self.manifest_path.exists():
            return None
        with open(self.manifest_path, encoding="utf-8") as f:
            payload = json.load(f)
        return IndexManifest(
            created_at=payload.get("created_at", ""),
            embedding_model=payload.get("embedding_model", ""),
            chunks=int(payload.get("chunks", 0)),
            indexed_runs=list(payload.get("indexed_runs", [])),
            kb_indexed_at=payload.get("kb_indexed_at"),
        )

    def _save_manifest(self, manifest: IndexManifest) -> None:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, ensure_ascii=False, indent=2)

    def _kb_updated_at(self) -> str | None:
        if not self.kb_dir.exists():
            return None
        latest = None
        for path in self.kb_dir.rglob("*.md"):
            ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if latest is None or ts > latest:
                latest = ts
        return latest.isoformat() if latest else None

    def _iter_runs(self) -> list[Path]:
        run_dirs = []
        if self.runs_dir.exists():
            run_dirs.extend([d for d in self.runs_dir.iterdir() if d.is_dir()])
        if self.legacy_runs_dir.exists():
            legacy = [d for d in self.legacy_runs_dir.iterdir() if d.is_dir()]
            run_dirs.extend([d for d in legacy if d.name not in {r.name for r in run_dirs}])
        return run_dirs

    def _load_kb_documents(self) -> list[dict]:
        documents: list[dict] = []
        topics_dir = self.kb_dir / "topics"
        papers_dir = self.kb_dir / "papers"
        for folder, source_type, prefix in [
            (topics_dir, "kb_topic", "kb:topic"),
            (papers_dir, "kb_paper", "kb:paper"),
        ]:
            if not folder.exists():
                continue
            for path in folder.glob("*.md"):
                text = path.read_text(encoding="utf-8")
                title = path.stem
                doc_id = f"{prefix}:{path.stem}"
                documents.append(
                    {
                        "doc_id": doc_id,
                        "title": title,
                        "text": text,
                        "source_type": source_type,
                        "provenance": Provenance(file_path=str(path)),
                        "meta": ChunkMeta(),
                        "updated_at": datetime.fromtimestamp(
                            path.stat().st_mtime, tz=timezone.utc
                        ).isoformat(),
                    }
                )
        return documents

    def _load_run_documents(self, run_dir: Path) -> list[dict]:
        documents: list[dict] = []
        run_id = run_dir.name
        report_path = run_dir / "report.md"
        if report_path.exists():
            documents.append(
                {
                    "doc_id": f"run:{run_id}:report",
                    "title": f"Run Report {run_id}",
                    "text": report_path.read_text(encoding="utf-8"),
                    "source_type": "run_report",
                    "provenance": Provenance(
                        run_id=run_id, section="report", file_path=str(report_path)
                    ),
                    "meta": ChunkMeta(),
                    "updated_at": datetime.fromtimestamp(
                        report_path.stat().st_mtime, tz=timezone.utc
                    ).isoformat(),
                }
            )
        qa_report = run_dir / "qa_report.md"
        if qa_report.exists():
            documents.append(
                {
                    "doc_id": f"run:{run_id}:qa_report",
                    "title": f"QA Report {run_id}",
                    "text": qa_report.read_text(encoding="utf-8"),
                    "source_type": "run_report",
                    "provenance": Provenance(
                        run_id=run_id, section="qa_report", file_path=str(qa_report)
                    ),
                    "meta": ChunkMeta(),
                    "updated_at": datetime.fromtimestamp(
                        qa_report.stat().st_mtime, tz=timezone.utc
                    ).isoformat(),
                }
            )
        claims_dir = run_dir / "claims"
        if claims_dir.exists():
            for claim_file in claims_dir.glob("*.jsonl"):
                for line in claim_file.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    claim_text = payload.get("claim") or payload.get("text") or ""
                    evidence = payload.get("evidence") or ""
                    combined = "\n".join([claim_text, evidence]).strip()
                    if not combined:
                        continue
                    doc_id = (
                        f"run:{run_id}:claim:{payload.get('id', stable_id(run_id, claim_text))}"
                    )
                    documents.append(
                        {
                            "doc_id": doc_id,
                            "title": payload.get("title")
                            or f"Claim {payload.get('id', '')}".strip(),
                            "text": combined,
                            "source_type": "claim",
                            "provenance": Provenance(
                                run_id=run_id, section="claim", file_path=str(claim_file)
                            ),
                            "meta": ChunkMeta(),
                            "updated_at": datetime.fromtimestamp(
                                claim_file.stat().st_mtime, tz=timezone.utc
                            ).isoformat(),
                        }
                    )
        rank_path = run_dir / "research_rank.json"
        if rank_path.exists():
            try:
                rank_payload = json.loads(rank_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                rank_payload = []
            if isinstance(rank_payload, dict):
                items = rank_payload.get("items", [])
            else:
                items = rank_payload
            for item in items[:50]:
                title = item.get("title") or "Ranked Paper"
                abstract = item.get("abstract") or item.get("summary") or ""
                text = "\n".join([title, abstract]).strip()
                if not text:
                    continue
                pmid = str(item.get("pmid")) if item.get("pmid") else None
                doc_id = (
                    f"paper:PMID_{pmid}"
                    if pmid
                    else f"run:{run_id}:paper:{stable_id(run_id, title)}"
                )
                meta = ChunkMeta(
                    year=item.get("year"),
                    journal=item.get("journal"),
                    tier=item.get("tier"),
                    score=item.get("score"),
                    oa=item.get("oa"),
                    topics=item.get("topics", []),
                )
                documents.append(
                    {
                        "doc_id": doc_id,
                        "title": title,
                        "text": text,
                        "source_type": "run_report",
                        "provenance": Provenance(
                            run_id=run_id,
                            pmid=pmid,
                            section="research_rank",
                            file_path=str(rank_path),
                        ),
                        "meta": meta,
                        "updated_at": datetime.fromtimestamp(
                            rank_path.stat().st_mtime, tz=timezone.utc
                        ).isoformat(),
                    }
                )
        return documents

    def _load_all_documents(
        self, run_ids: Iterable[str] | None = None, include_kb: bool = True
    ) -> list[dict]:
        documents: list[dict] = []
        if include_kb:
            documents.extend(self._load_kb_documents())
        runs = self._iter_runs()
        for run_dir in runs:
            if run_ids and run_dir.name not in set(run_ids):
                continue
            documents.extend(self._load_run_documents(run_dir))
        return documents

    def _write_chunks(self, chunks: Iterable[Chunk]) -> None:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        with open(self.chunks_path, "a", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk.to_dict(), ensure_ascii=False))
                f.write("\n")

    def _load_existing_chunk_ids(self) -> set:
        if not self.chunks_path.exists():
            return set()
        existing = set()
        with open(self.chunks_path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                existing.add(payload.get("chunk_id"))
        return existing

    def rebuild(self) -> IndexManifest:
        if self.index_dir.exists():
            for path in self.index_dir.iterdir():
                if path.is_file():
                    path.unlink()
        self.index_dir.mkdir(parents=True, exist_ok=True)
        bm25 = BM25Store(self.bm25_path)
        bm25.clear()
        vector_store = VectorStore.load(self.vector_path)
        vector_store.chunk_ids = []
        vector_store.vectors = vector_store.vectors[:0]
        all_documents = self._load_all_documents(include_kb=True)
        chunks = self._documents_to_chunks(all_documents)
        self._write_chunks(chunks)
        self._build_indexes(chunks, vector_store, bm25)
        indexed_runs = [run.name for run in self._iter_runs()]
        manifest = IndexManifest(
            created_at=datetime.now(timezone.utc).isoformat(),
            embedding_model=self.embedding_provider.model_name,
            chunks=len(chunks),
            indexed_runs=indexed_runs,
            kb_indexed_at=self._kb_updated_at(),
        )
        self._save_manifest(manifest)
        return manifest

    def update(self) -> IndexManifest:
        manifest = self._load_manifest()
        if manifest is None:
            return self.rebuild()
        indexed_runs = set(manifest.indexed_runs)
        current_runs = {run.name for run in self._iter_runs()}
        new_runs = sorted(current_runs - indexed_runs)
        kb_updated_at = self._kb_updated_at()
        include_kb = kb_updated_at and kb_updated_at != manifest.kb_indexed_at
        documents = self._load_all_documents(run_ids=new_runs, include_kb=include_kb)
        if not documents:
            return manifest
        existing_chunk_ids = self._load_existing_chunk_ids()
        chunks = [
            chunk
            for chunk in self._documents_to_chunks(documents)
            if chunk.chunk_id not in existing_chunk_ids
        ]
        if not chunks:
            return manifest
        self._write_chunks(chunks)
        bm25 = BM25Store(self.bm25_path)
        vector_store = VectorStore.load(self.vector_path)
        self._build_indexes(chunks, vector_store, bm25)
        updated_runs = sorted(indexed_runs | set(new_runs))
        manifest = IndexManifest(
            created_at=manifest.created_at,
            embedding_model=self.embedding_provider.model_name,
            chunks=manifest.chunks + len(chunks),
            indexed_runs=updated_runs,
            kb_indexed_at=kb_updated_at or manifest.kb_indexed_at,
        )
        self._save_manifest(manifest)
        return manifest

    def _documents_to_chunks(self, documents: list[dict]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for doc in documents:
            for chunk in self.chunker.create_chunks(
                doc_id=doc["doc_id"],
                title=doc["title"],
                text=doc["text"],
                source_type=doc["source_type"],
                provenance=doc["provenance"],
                meta=doc.get("meta"),
                updated_at=doc.get("updated_at"),
            ):
                if chunk.provenance and (chunk.provenance.file_path or chunk.provenance.run_id):
                    chunks.append(chunk)
        return chunks

    def _build_indexes(
        self, chunks: list[Chunk], vector_store: VectorStore, bm25: BM25Store
    ) -> None:
        if not chunks:
            return
        texts = [chunk.text for chunk in chunks]
        embedding_result = self.embedding_provider.embed(texts)
        vector_store.add(
            [chunk.chunk_id for chunk in chunks], embedding_result.vectors, embedding_result.model
        )
        vector_store.save()
        bm25_rows = [
            (
                chunk.doc_id,
                chunk.chunk_id,
                chunk.title,
                chunk.text,
                chunk.source_type,
                chunk.updated_at,
            )
            for chunk in chunks
        ]
        bm25.add_documents(bm25_rows)


def stable_id(run_id: str, text: str) -> str:
    import hashlib

    return hashlib.sha1(f"{run_id}|{text}".encode(), usedforsecurity=False).hexdigest()[:12]
