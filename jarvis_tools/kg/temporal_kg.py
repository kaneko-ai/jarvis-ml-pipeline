"""Temporal Knowledge Graph.

Per RP-323, implements time-aware knowledge graph.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from enum import Enum


class TemporalRelation(Enum):
    """Temporal relation types."""

    BEFORE = "before"
    AFTER = "after"
    DURING = "during"
    OVERLAPS = "overlaps"


@dataclass
class TemporalTriple:
    """A triple with temporal bounds."""

    subject: str
    predicate: str
    object: str
    valid_from: Optional[datetime]
    valid_to: Optional[datetime]
    source_paper: Optional[str]
    confidence: float = 1.0


@dataclass
class KnowledgeChange:
    """A change in knowledge over time."""

    entity: str
    attribute: str
    old_value: str
    new_value: str
    change_date: datetime
    source: str


class TemporalKnowledgeGraph:
    """Time-aware knowledge graph.
    
    Per RP-323:
    - Triples with valid_from/valid_to
    - Time-point queries ("as of 2020")
    - Knowledge evolution visualization
    """

    def __init__(self):
        self._triples: List[TemporalTriple] = []
        self._index_subject: Dict[str, List[int]] = {}
        self._index_object: Dict[str, List[int]] = {}

    def add_triple(
        self,
        subject: str,
        predicate: str,
        obj: str,
        valid_from: Optional[datetime] = None,
        valid_to: Optional[datetime] = None,
        source_paper: Optional[str] = None,
        confidence: float = 1.0,
    ) -> TemporalTriple:
        """Add a temporal triple.
        
        Args:
            subject: Subject entity.
            predicate: Relationship.
            obj: Object entity.
            valid_from: Start of validity.
            valid_to: End of validity.
            source_paper: Source paper ID.
            confidence: Confidence score.
            
        Returns:
            Created triple.
        """
        triple = TemporalTriple(
            subject=subject,
            predicate=predicate,
            object=obj,
            valid_from=valid_from,
            valid_to=valid_to,
            source_paper=source_paper,
            confidence=confidence,
        )

        idx = len(self._triples)
        self._triples.append(triple)

        # Index
        if subject not in self._index_subject:
            self._index_subject[subject] = []
        self._index_subject[subject].append(idx)

        if obj not in self._index_object:
            self._index_object[obj] = []
        self._index_object[obj].append(idx)

        return triple

    def query_as_of(
        self,
        entity: str,
        as_of: datetime,
        predicate: Optional[str] = None,
    ) -> List[TemporalTriple]:
        """Query knowledge as of a specific time.
        
        Args:
            entity: Entity to query.
            as_of: Time point.
            predicate: Optional predicate filter.
            
        Returns:
            Valid triples at that time.
        """
        results = []

        indices = set()
        indices.update(self._index_subject.get(entity, []))
        indices.update(self._index_object.get(entity, []))

        for idx in indices:
            triple = self._triples[idx]

            # Check temporal validity
            if triple.valid_from and triple.valid_from > as_of:
                continue
            if triple.valid_to and triple.valid_to < as_of:
                continue

            # Check predicate filter
            if predicate and triple.predicate != predicate:
                continue

            results.append(triple)

        return results

    def query_range(
        self,
        entity: str,
        start: datetime,
        end: datetime,
    ) -> List[TemporalTriple]:
        """Query knowledge over a time range.
        
        Args:
            entity: Entity to query.
            start: Range start.
            end: Range end.
            
        Returns:
            Triples overlapping the range.
        """
        results = []

        indices = set()
        indices.update(self._index_subject.get(entity, []))
        indices.update(self._index_object.get(entity, []))

        for idx in indices:
            triple = self._triples[idx]

            # Check overlap
            t_start = triple.valid_from or datetime.min
            t_end = triple.valid_to or datetime.max

            if t_start <= end and t_end >= start:
                results.append(triple)

        return results

    def track_changes(
        self,
        entity: str,
        predicate: str,
    ) -> List[KnowledgeChange]:
        """Track how knowledge changed over time.
        
        Args:
            entity: Entity to track.
            predicate: Predicate to track.
            
        Returns:
            List of changes.
        """
        triples = [
            t for t in self._triples
            if t.subject == entity and t.predicate == predicate
        ]

        # Sort by valid_from
        triples.sort(key=lambda t: t.valid_from or datetime.min)

        changes = []
        for i in range(1, len(triples)):
            prev = triples[i - 1]
            curr = triples[i]

            if prev.object != curr.object:
                changes.append(KnowledgeChange(
                    entity=entity,
                    attribute=predicate,
                    old_value=prev.object,
                    new_value=curr.object,
                    change_date=curr.valid_from or datetime.now(),
                    source=curr.source_paper or "",
                ))

        return changes

    def get_timeline(
        self,
        entity: str,
    ) -> List[Tuple[datetime, str, TemporalTriple]]:
        """Get timeline of knowledge about entity.
        
        Args:
            entity: Entity.
            
        Returns:
            Timeline events.
        """
        events = []

        indices = set()
        indices.update(self._index_subject.get(entity, []))
        indices.update(self._index_object.get(entity, []))

        for idx in indices:
            triple = self._triples[idx]

            if triple.valid_from:
                events.append((triple.valid_from, "started", triple))
            if triple.valid_to:
                events.append((triple.valid_to, "ended", triple))

        events.sort(key=lambda x: x[0])
        return events
