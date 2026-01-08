"""
JARVIS Knowledge Graph Plugin - KG & GraphRAG

知識グラフ構築、エンティティ正規化、GraphRAGインデックス。
"""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from jarvis_core.contracts.types import (
    Artifacts, ArtifactsDelta, Claim, EvidenceLink, RuntimeConfig, TaskContext
)


@dataclass
class Entity:
    """エンティティ."""
    entity_id: str
    name: str
    type: str  # gene, protein, drug, disease, pathway, method
    aliases: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Relation:
    """関係."""
    relation_id: str
    source_id: str
    target_id: str
    relation_type: str  # interacts, inhibits, causes, treats, etc.
    evidence: List[EvidenceLink] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class KnowledgeGraph:
    """知識グラフ."""
    entities: Dict[str, Entity] = field(default_factory=dict)
    relations: List[Relation] = field(default_factory=list)

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.entity_id] = entity

    def add_relation(self, relation: Relation) -> None:
        self.relations.append(relation)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": {k: {"name": v.name, "type": v.type, "aliases": v.aliases}
                        for k, v in self.entities.items()},
            "relations": [
                {"source": r.source_id, "target": r.target_id,
                 "type": r.relation_type, "confidence": r.confidence}
                for r in self.relations
            ]
        }


class EntityExtractor:
    """
    エンティティ抽出器.
    
    テキストから遺伝子、タンパク質、薬剤、疾患などを抽出。
    """

    # 簡易パターン（本番ではNER/辞書使用）
    PATTERNS = {
        "gene": r'\b([A-Z][A-Z0-9]{1,5})\b',  # e.g., TP53, BRCA1
        "protein": r'\b([A-Z][a-z]+(?:\s+[a-z]+)?(?:\s+protein)?)\b',
        "drug": r'\b([A-Z][a-z]+(?:mab|nib|cept|ide|ine|ol|ast))\b',
        "pathway": r'\b([A-Z]+(?:/[A-Z]+)?(?:\s+pathway|\s+signaling))\b',
    }

    # 既知エンティティ辞書
    KNOWN_ENTITIES = {
        "TP53": ("gene", ["p53", "tumor protein p53"]),
        "BRCA1": ("gene", ["BRCA1 DNA repair"]),
        "EGFR": ("gene", ["epidermal growth factor receptor"]),
        "TNF": ("gene", ["tumor necrosis factor", "TNF-alpha"]),
        "IL6": ("gene", ["interleukin 6"]),
        "pembrolizumab": ("drug", ["Keytruda"]),
        "trastuzumab": ("drug", ["Herceptin"]),
        "imatinib": ("drug", ["Gleevec"]),
    }

    def extract(self, text: str, doc_id: str = "") -> List[Entity]:
        """テキストからエンティティを抽出."""
        entities = []
        seen = set()

        # Known entities
        text_upper = text.upper()
        for name, (etype, aliases) in self.KNOWN_ENTITIES.items():
            if name.upper() in text_upper:
                if name not in seen:
                    entities.append(Entity(
                        entity_id=self._make_id(name),
                        name=name,
                        type=etype,
                        aliases=aliases
                    ))
                    seen.add(name)

        # Pattern-based extraction
        for etype, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text)
            for match in matches:
                if match not in seen and len(match) > 2:
                    entities.append(Entity(
                        entity_id=self._make_id(match),
                        name=match,
                        type=etype
                    ))
                    seen.add(match)

        return entities

    def _make_id(self, name: str) -> str:
        """エンティティIDを生成."""
        return f"ent-{hashlib.md5(name.encode()).hexdigest()[:8]}"


class RelationExtractor:
    """
    関係抽出器.
    
    エンティティ間の関係を抽出。
    """

    RELATION_PATTERNS = [
        (r"(\w+)\s+(?:inhibits?|blocks?|suppresses?)\s+(\w+)", "inhibits"),
        (r"(\w+)\s+(?:activates?|induces?|promotes?)\s+(\w+)", "activates"),
        (r"(\w+)\s+(?:binds?|interacts?)\s+(?:with\s+)?(\w+)", "interacts"),
        (r"(\w+)\s+(?:causes?|leads?\s+to)\s+(\w+)", "causes"),
        (r"(\w+)\s+(?:treats?|reduces?)\s+(\w+)", "treats"),
        (r"(\w+)\s+(?:regulates?|modulates?)\s+(\w+)", "regulates"),
    ]

    def extract(self, text: str, entities: List[Entity],
                doc_id: str = "") -> List[Relation]:
        """テキストから関係を抽出."""
        relations = []
        entity_names = {e.name.lower(): e.entity_id for e in entities}

        for pattern, rel_type in self.RELATION_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                source = match.group(1).lower()
                target = match.group(2).lower()

                source_id = entity_names.get(source)
                target_id = entity_names.get(target)

                if source_id and target_id and source_id != target_id:
                    relations.append(Relation(
                        relation_id=f"rel-{uuid.uuid4().hex[:8]}",
                        source_id=source_id,
                        target_id=target_id,
                        relation_type=rel_type,
                        confidence=0.7,
                        evidence=[EvidenceLink(
                            doc_id=doc_id,
                            section="extracted",
                            chunk_id=f"{doc_id}_rel",
                            start=match.start(),
                            end=match.end(),
                            confidence=0.7,
                            text=match.group(0)
                        )]
                    ))

        return relations


class EntityNormalizer:
    """
    エンティティ正規化.
    
    同義語・別名を統一IDに紐付け。
    """

    def __init__(self):
        self.normalized: Dict[str, str] = {}  # alias -> canonical
        self.canonical: Dict[str, Entity] = {}

    def normalize(self, entities: List[Entity]) -> List[Entity]:
        """エンティティを正規化."""
        result = []

        for entity in entities:
            # Check if already normalized
            canonical_id = self.normalized.get(entity.name.lower())

            if canonical_id:
                # Merge with existing
                canonical = self.canonical[canonical_id]
                if entity.name not in canonical.aliases:
                    canonical.aliases.append(entity.name)
            else:
                # New canonical entity
                self.normalized[entity.name.lower()] = entity.entity_id
                for alias in entity.aliases:
                    self.normalized[alias.lower()] = entity.entity_id
                self.canonical[entity.entity_id] = entity
                result.append(entity)

        return result

    def resolve(self, name: str) -> Optional[str]:
        """名前からcanonical IDを解決."""
        return self.normalized.get(name.lower())


class ControversyMapper:
    """
    論争マッパー.
    
    矛盾する主張、議論のあるトピックを検出。
    """

    def find_controversies(self, claims: List[Claim]) -> List[Dict[str, Any]]:
        """矛盾する主張を検出."""
        controversies = []

        # Simple: find claims with opposing sentiment
        positive_words = {"increase", "promote", "activate", "effective", "beneficial"}
        negative_words = {"decrease", "inhibit", "suppress", "ineffective", "harmful"}

        # Group claims by topic (simple keyword overlap)
        for i, c1 in enumerate(claims):
            for c2 in claims[i+1:]:
                # Check topic similarity
                words1 = set(c1.claim_text.lower().split())
                words2 = set(c2.claim_text.lower().split())

                overlap = len(words1 & words2) / max(len(words1 | words2), 1)

                if overlap > 0.3:
                    # Check for opposing sentiment
                    pos1 = any(w in c1.claim_text.lower() for w in positive_words)
                    neg1 = any(w in c1.claim_text.lower() for w in negative_words)
                    pos2 = any(w in c2.claim_text.lower() for w in positive_words)
                    neg2 = any(w in c2.claim_text.lower() for w in negative_words)

                    if (pos1 and neg2) or (neg1 and pos2):
                        controversies.append({
                            "claim1_id": c1.claim_id,
                            "claim2_id": c2.claim_id,
                            "claim1_text": c1.claim_text,
                            "claim2_text": c2.claim_text,
                            "topic_overlap": overlap,
                            "type": "opposing_claims"
                        })

        return controversies


class GraphRAGIndexer:
    """
    GraphRAGインデクサー.
    
    知識グラフをRAG用にインデックス化。
    """

    def __init__(self):
        self.entity_embeddings: Dict[str, List[float]] = {}
        self.relation_texts: Dict[str, str] = {}

    def index(self, kg: KnowledgeGraph) -> Dict[str, Any]:
        """グラフをインデックス化."""
        # Create text representations for entities
        entity_texts = {}
        for eid, entity in kg.entities.items():
            text = f"{entity.name} ({entity.type})"
            if entity.aliases:
                text += f", also known as: {', '.join(entity.aliases)}"
            entity_texts[eid] = text

        # Create text for relations
        for rel in kg.relations:
            source = kg.entities.get(rel.source_id)
            target = kg.entities.get(rel.target_id)
            if source and target:
                text = f"{source.name} {rel.relation_type} {target.name}"
                self.relation_texts[rel.relation_id] = text

        return {
            "entity_count": len(kg.entities),
            "relation_count": len(kg.relations),
            "entity_texts": entity_texts,
            "indexed": True
        }

    def query(self, query: str, kg: KnowledgeGraph,
              top_k: int = 5) -> List[Dict[str, Any]]:
        """グラフをクエリ."""
        query_words = set(query.lower().split())
        results = []

        # Search entities
        for eid, entity in kg.entities.items():
            name_words = set(entity.name.lower().split())
            score = len(query_words & name_words) / max(len(query_words), 1)

            if score > 0:
                results.append({
                    "type": "entity",
                    "id": eid,
                    "name": entity.name,
                    "score": score
                })

        # Search relations
        for rel in kg.relations:
            text = self.relation_texts.get(rel.relation_id, "")
            text_words = set(text.lower().split())
            score = len(query_words & text_words) / max(len(query_words), 1)

            if score > 0:
                results.append({
                    "type": "relation",
                    "id": rel.relation_id,
                    "text": text,
                    "score": score
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


class KnowledgeGraphPlugin:
    """Knowledge Graph統合プラグイン."""

    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.relation_extractor = RelationExtractor()
        self.normalizer = EntityNormalizer()
        self.controversy_mapper = ControversyMapper()
        self.graphrag = GraphRAGIndexer()
        self.is_active = False

    def activate(self, runtime: RuntimeConfig, config: Dict[str, Any]) -> None:
        self.is_active = True

    def run(self, context: TaskContext, artifacts: Artifacts) -> ArtifactsDelta:
        """KG構築を実行."""
        delta: ArtifactsDelta = {}

        kg = KnowledgeGraph()

        # Extract entities from all papers
        all_entities = []
        for paper in artifacts.papers:
            text = paper.title + " " + (paper.abstract or "")
            for section_text in paper.sections.values():
                text += " " + section_text

            entities = self.entity_extractor.extract(text, paper.doc_id)
            all_entities.extend(entities)

        # Normalize entities
        normalized = self.normalizer.normalize(all_entities)
        for entity in normalized:
            kg.add_entity(entity)

        # Extract relations
        for paper in artifacts.papers:
            text = paper.title + " " + (paper.abstract or "")
            for section_text in paper.sections.values():
                text += " " + section_text

            relations = self.relation_extractor.extract(text, normalized, paper.doc_id)
            for rel in relations:
                kg.add_relation(rel)

        # Find controversies
        controversies = self.controversy_mapper.find_controversies(artifacts.claims)

        # Index for GraphRAG
        index_result = self.graphrag.index(kg)

        # Store in artifacts
        artifacts.graphs["knowledge_graph"] = kg.to_dict()

        delta["knowledge_graph"] = kg.to_dict()
        delta["controversies"] = controversies
        delta["graphrag_index"] = index_result

        return delta

    def deactivate(self) -> None:
        self.is_active = False


def get_knowledge_graph_plugin() -> KnowledgeGraphPlugin:
    return KnowledgeGraphPlugin()
