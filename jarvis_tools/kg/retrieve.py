"""Graph 2-Hop Retrieval.

Per RP-131, retrieves 2-hop subgraphs for context enrichment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Set


@dataclass
class Triple:
    """A knowledge graph triple."""

    subject: str
    predicate: str
    object: str

    def __hash__(self):
        return hash((self.subject, self.predicate, self.object))


@dataclass
class Subgraph:
    """A retrieved subgraph."""

    center_entity: str
    triples: List[Triple]
    entities: Set[str]
    hop1_entities: Set[str]
    hop2_entities: Set[str]


class KnowledgeGraph:
    """Simple in-memory knowledge graph."""

    def __init__(self):
        self._triples: List[Triple] = []
        self._subject_index: Dict[str, List[Triple]] = {}
        self._object_index: Dict[str, List[Triple]] = {}

    def add_triple(self, subject: str, predicate: str, obj: str) -> None:
        """Add a triple to the graph."""
        triple = Triple(subject, predicate, obj)
        self._triples.append(triple)

        # Index by subject
        if subject not in self._subject_index:
            self._subject_index[subject] = []
        self._subject_index[subject].append(triple)

        # Index by object
        if obj not in self._object_index:
            self._object_index[obj] = []
        self._object_index[obj].append(triple)

    def get_neighbors(self, entity: str) -> List[Triple]:
        """Get all triples involving an entity."""
        result = []
        result.extend(self._subject_index.get(entity, []))
        result.extend(self._object_index.get(entity, []))
        return result

    def get_outgoing(self, entity: str) -> List[Triple]:
        """Get triples where entity is subject."""
        return self._subject_index.get(entity, [])

    def get_incoming(self, entity: str) -> List[Triple]:
        """Get triples where entity is object."""
        return self._object_index.get(entity, [])


def retrieve_2hop(
    kg: KnowledgeGraph,
    entity: str,
    max_hop1: int = 10,
    max_hop2: int = 20,
) -> Subgraph:
    """Retrieve 2-hop subgraph around an entity.

    Args:
        kg: Knowledge graph.
        entity: Center entity.
        max_hop1: Max triples in first hop.
        max_hop2: Max triples in second hop.

    Returns:
        Subgraph with 2-hop neighborhood.
    """
    entity_norm = entity.upper()

    # Hop 1
    hop1_triples = kg.get_neighbors(entity_norm)[:max_hop1]
    hop1_entities: Set[str] = set()

    for triple in hop1_triples:
        if triple.subject != entity_norm:
            hop1_entities.add(triple.subject)
        if triple.object != entity_norm:
            hop1_entities.add(triple.object)

    # Hop 2
    hop2_triples: List[Triple] = []
    hop2_entities: Set[str] = set()

    for hop1_entity in hop1_entities:
        for triple in kg.get_neighbors(hop1_entity):
            if triple not in hop1_triples:
                hop2_triples.append(triple)
                if triple.subject not in hop1_entities and triple.subject != entity_norm:
                    hop2_entities.add(triple.subject)
                if triple.object not in hop1_entities and triple.object != entity_norm:
                    hop2_entities.add(triple.object)

                if len(hop2_triples) >= max_hop2:
                    break
        if len(hop2_triples) >= max_hop2:
            break

    all_triples = hop1_triples + hop2_triples
    all_entities = {entity_norm} | hop1_entities | hop2_entities

    return Subgraph(
        center_entity=entity,
        triples=all_triples,
        entities=all_entities,
        hop1_entities=hop1_entities,
        hop2_entities=hop2_entities,
    )


def summarize_subgraph(subgraph: Subgraph, max_triples: int = 10) -> str:
    """Summarize subgraph as text for LLM context.

    Args:
        subgraph: The subgraph.
        max_triples: Max triples to include.

    Returns:
        Text summary of subgraph.
    """
    lines = [f"Knowledge about {subgraph.center_entity}:"]

    for triple in subgraph.triples[:max_triples]:
        lines.append(f"- {triple.subject} {triple.predicate} {triple.object}")

    if len(subgraph.triples) > max_triples:
        lines.append(f"... and {len(subgraph.triples) - max_triples} more relationships")

    return "\n".join(lines)
