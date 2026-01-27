"""Lightweight KG Store using SQLite.

Per RP-11, this provides a simple triple store for CPU environments.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class Triple:
    """A knowledge graph triple."""

    entity1: str
    relation: str
    entity2: str
    pmid: Optional[str] = None
    chunk_id: Optional[str] = None


class KGStore:
    """SQLite-based knowledge graph store."""

    def __init__(self, db_path: str = "kg.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS triples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity1 TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    entity2 TEXT NOT NULL,
                    pmid TEXT,
                    chunk_id TEXT,
                    UNIQUE(entity1, relation, entity2, chunk_id)
                )
            """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entity1 ON triples(entity1)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entity2 ON triples(entity2)")
            conn.commit()

    def add_triple(self, triple: Triple) -> bool:
        """Add a triple to the store."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO triples (entity1, relation, entity2, pmid, chunk_id) VALUES (?, ?, ?, ?, ?)",
                    (triple.entity1, triple.relation, triple.entity2, triple.pmid, triple.chunk_id),
                )
                conn.commit()
            return True
        except Exception:
            return False

    def add_triples(self, triples: List[Triple]) -> int:
        """Add multiple triples. Returns count added."""
        count = 0
        for t in triples:
            if self.add_triple(t):
                count += 1
        return count

    def find_by_entity(self, entity: str) -> List[Triple]:
        """Find triples involving an entity."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "SELECT entity1, relation, entity2, pmid, chunk_id FROM triples WHERE entity1 = ? OR entity2 = ?",
                (entity, entity),
            )
            return [
                Triple(entity1=r[0], relation=r[1], entity2=r[2], pmid=r[3], chunk_id=r[4])
                for r in cursor.fetchall()
            ]

    def find_neighbors(self, entity: str, hops: int = 1) -> List[str]:
        """Find neighboring entities within N hops."""
        visited = {entity}
        frontier = [entity]

        for _ in range(hops):
            next_frontier = []
            for e in frontier:
                triples = self.find_by_entity(e)
                for t in triples:
                    for neighbor in [t.entity1, t.entity2]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            next_frontier.append(neighbor)
            frontier = next_frontier

        visited.discard(entity)
        return list(visited)

    def get_chunk_ids_for_entities(self, entities: List[str]) -> List[str]:
        """Get chunk IDs related to entities."""
        chunk_ids = set()
        for entity in entities:
            triples = self.find_by_entity(entity)
            for t in triples:
                if t.chunk_id:
                    chunk_ids.add(t.chunk_id)
        return list(chunk_ids)

    def count(self) -> int:
        """Count total triples."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM triples")
            return cursor.fetchone()[0]
