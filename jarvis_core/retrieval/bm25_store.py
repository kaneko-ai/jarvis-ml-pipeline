"""SQLite FTS5 based keyword search store."""
from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BM25Store:
    db_path: Path

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(
                    doc_id,
                    chunk_id,
                    title,
                    text,
                    source_type,
                    updated_at,
                    tokenize='porter'
                )
                """
            )

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute("DROP TABLE IF EXISTS docs")
        self.initialize()

    def add_documents(self, rows: Iterable[tuple[str, str, str, str, str, str]]) -> None:
        self.initialize()
        with self._connect() as conn:
            conn.executemany(
                "INSERT INTO docs (doc_id, chunk_id, title, text, source_type, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                rows,
            )

    def search(self, query: str, top_k: int = 20) -> list[tuple[str, float]]:
        self.initialize()
        if not query.strip():
            return []
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT chunk_id, bm25(docs) as score FROM docs WHERE docs MATCH ? ORDER BY score LIMIT ?",
                (query, top_k),
            )
            results = [(row[0], float(row[1])) for row in cursor.fetchall()]
        return results
