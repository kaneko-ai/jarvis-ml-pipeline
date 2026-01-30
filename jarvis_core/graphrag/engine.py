"""JARVIS GraphRAG & Knowledge Graph Module - Phase 1 Features (1-15)"""

import hashlib
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field


# ============================================
# 1. GRAPHRAG ENGINE
# ============================================
@dataclass
class GraphNode:
    """Graph node representing an entity."""

    id: str
    type: str  # paper, author, concept, gene, drug
    properties: dict = field(default_factory=dict)


@dataclass
class GraphEdge:
    """Graph edge representing a relationship."""

    source: str
    target: str
    type: str  # cites, authored_by, relates_to, etc.
    weight: float = 1.0
    properties: dict = field(default_factory=dict)


class GraphRAGEngine:
    """Knowledge Graph + RAG unified engine."""

    def __init__(self):
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []
        self.adjacency: dict[str, list[str]] = defaultdict(list)
        self.reverse_adjacency: dict[str, list[str]] = defaultdict(list)

    def add_node(self, node: GraphNode):
        """Add node to graph."""
        self.nodes[node.id] = node

    def add_edge(self, edge: GraphEdge):
        """Add edge to graph."""
        self.edges.append(edge)
        self.adjacency[edge.source].append(edge.target)
        self.reverse_adjacency[edge.target].append(edge.source)

    def multi_hop_query(self, start_id: str, hops: int = 2) -> list[GraphNode]:
        """Multi-hop graph traversal for reasoning.

        Args:
            start_id: Starting node ID
            hops: Number of hops

        Returns:
            List of reachable nodes
        """
        visited = set()
        current_level = {start_id}

        for _ in range(hops):
            next_level = set()
            for node_id in current_level:
                for neighbor in self.adjacency.get(node_id, []):
                    if neighbor not in visited:
                        next_level.add(neighbor)
                        visited.add(neighbor)
            current_level = next_level

        return [self.nodes[nid] for nid in visited if nid in self.nodes]

    def find_path(self, source: str, target: str, max_depth: int = 5) -> list[str] | None:
        """Find path between two nodes (BFS).

        Args:
            source: Source node ID
            target: Target node ID
            max_depth: Maximum search depth

        Returns:
            Path as list of node IDs or None
        """
        if source not in self.nodes or target not in self.nodes:
            return None

        queue = [(source, [source])]
        visited = {source}

        while queue:
            current, path = queue.pop(0)
            if len(path) > max_depth:
                continue

            if current == target:
                return path

            for neighbor in self.adjacency.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def get_subgraph(self, node_ids: list[str]) -> tuple[list[GraphNode], list[GraphEdge]]:
        """Extract subgraph containing specified nodes."""
        nodes = [self.nodes[nid] for nid in node_ids if nid in self.nodes]
        node_set = set(node_ids)
        edges = [e for e in self.edges if e.source in node_set and e.target in node_set]
        return nodes, edges


# ============================================
# 2. ADAPTIVE RAG
# ============================================
class AdaptiveRAG:
    """Dynamic retrieval decision system."""

    def __init__(self, knowledge_base: dict[str, str] = None):
        self.internal_kb = knowledge_base or {}
        self.query_history: list[dict] = []

    def assess_query_complexity(self, query: str) -> dict:
        """Assess query complexity to decide retrieval strategy.

        Args:
            query: User query

        Returns:
            Complexity assessment
        """
        words = query.lower().split()

        # Complexity indicators
        has_comparison = any(
            w in words for w in ["compare", "versus", "vs", "difference", "between"]
        )
        has_temporal = any(w in words for w in ["recent", "latest", "2024", "2025", "trend", "new"])
        has_specific = any(w in words for w in ["specific", "exact", "particular", "pmid"])
        has_multi_hop = (
            len([w for w in words if w in ["how", "why", "cause", "effect", "mechanism"]]) > 0
        )

        complexity_score = sum([has_comparison, has_temporal, has_specific, has_multi_hop])

        return {
            "query": query,
            "complexity_score": complexity_score,
            "needs_external": has_temporal or complexity_score >= 2,
            "strategy": self._select_strategy(complexity_score, has_temporal),
        }

    def _select_strategy(self, score: int, needs_recent: bool) -> str:
        if needs_recent:
            return "external_first"
        elif score >= 3:
            return "hybrid"
        elif score >= 2:
            return "internal_then_external"
        else:
            return "internal_only"

    def retrieve(self, query: str) -> dict:
        """Retrieve with adaptive strategy."""
        assessment = self.assess_query_complexity(query)
        strategy = assessment["strategy"]

        results = {"strategy": strategy, "sources": []}

        if strategy in ["internal_only", "internal_then_external", "hybrid"]:
            # Check internal knowledge
            internal_matches = self._search_internal(query)
            results["internal"] = internal_matches
            results["sources"].append("internal")

        if strategy in ["external_first", "internal_then_external", "hybrid"]:
            results["needs_external_search"] = True
            results["sources"].append("external")

        return results

    def _search_internal(self, query: str) -> list[str]:
        """Simple internal KB search."""
        query_words = set(query.lower().split())
        matches = []
        for key, value in self.internal_kb.items():
            key_words = set(key.lower().split())
            if query_words & key_words:
                matches.append(value)
        return matches


# ============================================
# 3. CORRECTIVE RAG (CRAG)
# ============================================
class CorrectiveRAG:
    """Self-correcting RAG pipeline."""

    def __init__(self):
        self.confidence_threshold = 0.7

    def evaluate_retrieval(self, query: str, retrieved_docs: list[dict]) -> dict:
        """Evaluate retrieval quality.

        Args:
            query: Original query
            retrieved_docs: Retrieved documents

        Returns:
            Evaluation with confidence scores
        """
        if not retrieved_docs:
            return {"status": "empty", "action": "retry_with_expanded_query"}

        scores = []
        for doc in retrieved_docs:
            score = self._calculate_relevance(query, doc)
            scores.append({"doc": doc, "score": score})

        avg_score = sum(s["score"] for s in scores) / len(scores)

        if avg_score >= self.confidence_threshold:
            return {"status": "confident", "action": "use_results", "scores": scores}
        elif avg_score >= 0.4:
            return {"status": "ambiguous", "action": "refine_and_retry", "scores": scores}
        else:
            return {"status": "poor", "action": "expand_search", "scores": scores}

    def _calculate_relevance(self, query: str, doc: dict) -> float:
        """Calculate relevance score."""
        query_words = set(query.lower().split())
        doc_text = f"{doc.get('title', '')} {doc.get('abstract', '')}".lower()
        doc_words = set(doc_text.split())

        overlap = len(query_words & doc_words)
        return min(overlap / max(len(query_words), 1), 1.0)

    def detect_hallucination(self, answer: str, sources: list[dict]) -> dict:
        """Detect potential hallucinations.

        Args:
            answer: Generated answer
            sources: Source documents

        Returns:
            Hallucination detection result
        """
        # Extract claims from answer
        claims = [s.strip() for s in answer.split(".") if len(s.strip()) > 20]

        source_text = " ".join([d.get("abstract", "") for d in sources]).lower()

        verified = []
        suspicious = []

        for claim in claims:
            claim_words = set(claim.lower().split())
            # Check if key words appear in sources
            overlap = len(claim_words & set(source_text.split()))
            if overlap >= len(claim_words) * 0.3:
                verified.append(claim)
            else:
                suspicious.append(claim)

        return {
            "verified_claims": len(verified),
            "suspicious_claims": len(suspicious),
            "hallucination_risk": len(suspicious) / max(len(claims), 1),
            "suspicious": suspicious[:3],  # Top 3 for review
        }


# ============================================
# 4. REAL-TIME PAPER STREAM
# ============================================
class PaperStreamMonitor:
    """Real-time paper feed monitoring."""

    SOURCES = {
        "arxiv": "http://export.arxiv.org/api/query",
        "biorxiv": "https://api.biorxiv.org/details/biorxiv",
        "medrxiv": "https://api.biorxiv.org/details/medrxiv",
    }

    def __init__(self):
        self.filters: list[dict] = []
        self.seen_ids: set[str] = set()
        self.callbacks: list[callable] = []

    def add_filter(
        self, keywords: list[str], authors: list[str] = None, journals: list[str] = None
    ):
        """Add monitoring filter."""
        self.filters.append(
            {"keywords": keywords, "authors": authors or [], "journals": journals or []}
        )

    def check_match(self, paper: dict) -> bool:
        """Check if paper matches any filter."""
        title = paper.get("title", "").lower()
        abstract = paper.get("abstract", "").lower()
        authors = paper.get("authors", "").lower()

        for f in self.filters:
            # Keyword match
            if any(kw.lower() in title or kw.lower() in abstract for kw in f["keywords"]):
                return True
            # Author match
            if any(a.lower() in authors for a in f["authors"]):
                return True

        return False

    def process_new_papers(self, papers: list[dict]) -> list[dict]:
        """Process and filter new papers."""
        new_matches = []

        for paper in papers:
            paper_id = paper.get("id") or paper.get("pmid") or paper.get("arxiv_id")
            if paper_id and paper_id not in self.seen_ids:
                self.seen_ids.add(paper_id)
                if self.check_match(paper):
                    new_matches.append(paper)

        return new_matches


# ============================================
# 5. PAPER KNOWLEDGE GRAPH BUILDER
# ============================================
class KnowledgeGraphBuilder:
    """Automatic KG construction from papers."""

    ENTITY_PATTERNS = {
        "gene": r"\b([A-Z][A-Z0-9]{2,})\b",
        "drug": r"\b([A-Z][a-z]+(?:mab|nib|lib|cept|tide))\b",
        "disease": r"\b([A-Z][a-z]+ (?:cancer|disease|syndrome|disorder))\b",
    }

    def __init__(self):
        self.graph = GraphRAGEngine()

    def extract_entities(self, text: str) -> list[dict]:
        """Extract entities from text."""
        entities = []

        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            matches = re.findall(pattern, text)
            for match in set(matches):
                entities.append({"text": match, "type": entity_type})

        return entities

    def build_from_paper(self, paper: dict) -> dict:
        """Build KG nodes and edges from a paper."""
        paper_id = (
            paper.get("pmid")
            or paper.get("id")
            or hashlib.md5(paper.get("title", "").encode(), usedforsecurity=False).hexdigest()[:8]
        )

        # Add paper node
        paper_node = GraphNode(
            id=paper_id,
            type="paper",
            properties={
                "title": paper.get("title"),
                "year": paper.get("year"),
                "journal": paper.get("journal"),
            },
        )
        self.graph.add_node(paper_node)

        # Extract and add entities
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
        entities = self.extract_entities(text)

        for entity in entities:
            entity_id = f"{entity['type']}_{hashlib.md5(entity['text'].encode(), usedforsecurity=False).hexdigest()[:6]}"
            entity_node = GraphNode(
                id=entity_id, type=entity["type"], properties={"name": entity["text"]}
            )
            self.graph.add_node(entity_node)

            # Add edge from paper to entity
            edge = GraphEdge(source=paper_id, target=entity_id, type="mentions")
            self.graph.add_edge(edge)

        # Add author edges
        authors = paper.get("authors", "").split(", ")
        for author in authors[:5]:
            if author:
                author_id = (
                    f"author_{hashlib.md5(author.encode(), usedforsecurity=False).hexdigest()[:6]}"
                )
                author_node = GraphNode(id=author_id, type="author", properties={"name": author})
                self.graph.add_node(author_node)
                edge = GraphEdge(source=paper_id, target=author_id, type="authored_by")
                self.graph.add_edge(edge)

        return {"paper_id": paper_id, "entities": len(entities), "authors": len(authors)}


# ============================================
# 6. CITATION NETWORK ANALYZER
# ============================================
class CitationNetworkAnalyzer:
    """Analyze citation networks."""

    def __init__(self, graph: GraphRAGEngine = None):
        self.graph = graph or GraphRAGEngine()

    def calculate_pagerank(self, damping: float = 0.85, iterations: int = 20) -> dict[str, float]:
        """Calculate PageRank for papers."""
        nodes = [n for n in self.graph.nodes.values() if n.type == "paper"]
        n = len(nodes)
        if n == 0:
            return {}

        # Initialize scores
        scores = {node.id: 1 / n for node in nodes}

        for _ in range(iterations):
            new_scores = {}
            for node in nodes:
                incoming = self.graph.reverse_adjacency.get(node.id, [])
                rank = (1 - damping) / n
                for source in incoming:
                    outgoing_count = len(self.graph.adjacency.get(source, []))
                    if outgoing_count > 0:
                        rank += damping * scores.get(source, 0) / outgoing_count
                new_scores[node.id] = rank
            scores = new_scores

        return scores

    def find_influential_papers(self, top_n: int = 10) -> list[dict]:
        """Find most influential papers."""
        rankings = self.calculate_pagerank()
        sorted_papers = sorted(rankings.items(), key=lambda x: x[1], reverse=True)

        results = []
        for paper_id, score in sorted_papers[:top_n]:
            if paper_id in self.graph.nodes:
                node = self.graph.nodes[paper_id]
                results.append(
                    {
                        "id": paper_id,
                        "title": node.properties.get("title", "Unknown"),
                        "influence_score": round(score * 1000, 2),
                    }
                )

        return results

    def detect_emerging_topics(self, year_threshold: int = 2023) -> list[dict]:
        """Detect emerging research topics."""
        recent_papers = [
            n
            for n in self.graph.nodes.values()
            if n.type == "paper" and n.properties.get("year", 0) >= year_threshold
        ]

        # Count entity co-occurrences
        entity_counts = defaultdict(int)
        for paper in recent_papers:
            neighbors = self.graph.adjacency.get(paper.id, [])
            for neighbor in neighbors:
                if neighbor in self.graph.nodes and self.graph.nodes[neighbor].type != "author":
                    entity_counts[neighbor] += 1

        # Return top emerging entities
        sorted_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"entity": e, "mentions": c} for e, c in sorted_entities[:10]]


# ============================================
# 7. SEMANTIC PAPER CLUSTERING
# ============================================
class SemanticClustering:
    """Embedding-based paper clustering."""

    def __init__(self):
        self.embeddings: dict[str, list[float]] = {}

    def simple_embed(self, text: str, dim: int = 64) -> list[float]:
        """Simple TF-based embedding (placeholder for real embeddings)."""
        words = text.lower().split()
        # Create a simple hash-based embedding
        embedding = [0.0] * dim
        for word in words:
            h = hash(word) % dim
            embedding[h] += 1
        # Normalize
        norm = math.sqrt(sum(x * x for x in embedding)) or 1
        return [x / norm for x in embedding]

    def add_paper(self, paper_id: str, text: str):
        """Add paper embedding."""
        self.embeddings[paper_id] = self.simple_embed(text)

    def cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity."""
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        return dot / (norm1 * norm2) if norm1 and norm2 else 0

    def find_similar(self, paper_id: str, top_n: int = 5) -> list[tuple[str, float]]:
        """Find similar papers."""
        if paper_id not in self.embeddings:
            return []

        target = self.embeddings[paper_id]
        similarities = []

        for other_id, embedding in self.embeddings.items():
            if other_id != paper_id:
                sim = self.cosine_similarity(target, embedding)
                similarities.append((other_id, sim))

        return sorted(similarities, key=lambda x: x[1], reverse=True)[:top_n]

    def cluster_papers(self, n_clusters: int = 5) -> dict[int, list[str]]:
        """Simple k-means-like clustering."""
        if len(self.embeddings) < n_clusters:
            return {0: list(self.embeddings.keys())}

        # Initialize centroids randomly (first n papers)
        paper_ids = list(self.embeddings.keys())
        centroids = [self.embeddings[paper_ids[i]] for i in range(n_clusters)]

        # Assign papers to clusters
        clusters = defaultdict(list)
        for paper_id, embedding in self.embeddings.items():
            best_cluster = 0
            best_sim = -1
            for i, centroid in enumerate(centroids):
                sim = self.cosine_similarity(embedding, centroid)
                if sim > best_sim:
                    best_sim = sim
                    best_cluster = i
            clusters[best_cluster].append(paper_id)

        return dict(clusters)


# ============================================
# 8-15: Additional Features
# ============================================


class HierarchicalConceptExtractor:
    """Extract hierarchical concepts from papers."""

    CONCEPT_HIERARCHY = {
        "disease": ["cancer", "diabetes", "cardiovascular", "neurological"],
        "treatment": ["drug", "therapy", "surgery", "immunotherapy"],
        "technology": ["AI", "machine learning", "deep learning", "genomics"],
    }

    def extract(self, text: str) -> dict:
        text_lower = text.lower()
        hierarchy = {}
        for category, concepts in self.CONCEPT_HIERARCHY.items():
            found = [c for c in concepts if c in text_lower]
            if found:
                hierarchy[category] = found
        return hierarchy


class CrossLingualSearch:
    """Cross-lingual paper search."""

    TRANSLATIONS = {
        "がん": "cancer",
        "治療": "treatment",
        "機械学習": "machine learning",
        "深層学習": "deep learning",
        "遺伝子": "gene",
        "タンパク質": "protein",
    }

    def translate_query(self, query: str) -> str:
        result = query
        for jp, en in self.TRANSLATIONS.items():
            result = result.replace(jp, en)
        return result


class TemporalKnowledgeTracker:
    """Track knowledge evolution over time."""

    def __init__(self):
        self.timeline: dict[int, list[dict]] = defaultdict(list)

    def add_event(self, year: int, event: dict):
        self.timeline[year].append(event)

    def get_trend(self, concept: str) -> list[tuple[int, int]]:
        trend = []
        for year in sorted(self.timeline.keys()):
            count = sum(1 for e in self.timeline[year] if concept.lower() in str(e).lower())
            trend.append((year, count))
        return trend


class EntityResolver:
    """Resolve and normalize entities."""

    def __init__(self):
        self.aliases: dict[str, str] = {}

    def add_alias(self, alias: str, canonical: str):
        self.aliases[alias.lower()] = canonical

    def resolve(self, entity: str) -> str:
        return self.aliases.get(entity.lower(), entity)


class HypothesisLinkDiscovery:
    """Discover potential hypothesis links."""

    def find_implicit_links(self, papers: list[dict], graph: GraphRAGEngine) -> list[dict]:
        links = []
        paper_entities = {}

        for paper in papers:
            pid = paper.get("pmid", paper.get("id"))
            entities = set()
            for neighbor in graph.adjacency.get(pid, []):
                if neighbor in graph.nodes:
                    entities.add(neighbor)
            paper_entities[pid] = entities

        # Find papers with shared entities but no direct citation
        paper_ids = list(paper_entities.keys())
        for i, p1 in enumerate(paper_ids):
            for p2 in paper_ids[i + 1 :]:
                shared = paper_entities[p1] & paper_entities[p2]
                if len(shared) >= 2:
                    # Check if not already connected
                    if p2 not in graph.adjacency.get(p1, []):
                        links.append(
                            {
                                "paper1": p1,
                                "paper2": p2,
                                "shared_entities": list(shared),
                                "potential_link_strength": len(shared),
                            }
                        )

        return sorted(links, key=lambda x: x["potential_link_strength"], reverse=True)


class EvidenceStrengthScorer:
    """Score evidence strength in papers."""

    STRENGTH_INDICATORS = {
        "high": [
            "randomized",
            "double-blind",
            "meta-analysis",
            "systematic review",
            "large cohort",
        ],
        "medium": ["cohort", "case-control", "prospective", "retrospective"],
        "low": ["case report", "case series", "opinion", "narrative review"],
    }

    def score(self, abstract: str) -> dict:
        abstract_lower = abstract.lower()

        for level, indicators in self.STRENGTH_INDICATORS.items():
            if any(ind in abstract_lower for ind in indicators):
                return {"level": level, "matched": [i for i in indicators if i in abstract_lower]}

        return {"level": "unknown", "matched": []}


class ContradictionDetector:
    """Detect contradictions between papers."""

    CONTRADICTION_PAIRS = [
        ("increases", "decreases"),
        ("positive", "negative"),
        ("effective", "ineffective"),
        ("significant", "not significant"),
        ("improves", "worsens"),
        ("beneficial", "harmful"),
    ]

    def detect(self, paper1: dict, paper2: dict) -> dict:
        text1 = f"{paper1.get('title', '')} {paper1.get('abstract', '')}".lower()
        text2 = f"{paper2.get('title', '')} {paper2.get('abstract', '')}".lower()

        contradictions = []
        for pos, neg in self.CONTRADICTION_PAIRS:
            if (pos in text1 and neg in text2) or (neg in text1 and pos in text2):
                contradictions.append((pos, neg))

        return {
            "has_potential_contradiction": len(contradictions) > 0,
            "contradiction_pairs": contradictions,
            "confidence": min(len(contradictions) / 3, 1.0),
        }


# ============================================
# FACTORY FUNCTIONS
# ============================================
def get_graphrag_engine() -> GraphRAGEngine:
    return GraphRAGEngine()


def get_adaptive_rag() -> AdaptiveRAG:
    return AdaptiveRAG()


def get_corrective_rag() -> CorrectiveRAG:
    return CorrectiveRAG()


def get_kg_builder() -> KnowledgeGraphBuilder:
    return KnowledgeGraphBuilder()


def get_citation_analyzer() -> CitationNetworkAnalyzer:
    return CitationNetworkAnalyzer()


def get_semantic_clustering() -> SemanticClustering:
    return SemanticClustering()


if __name__ == "__main__":
    print("=== GraphRAG Engine Demo ===")
    engine = GraphRAGEngine()
    engine.add_node(GraphNode("p1", "paper", {"title": "AI in Medicine"}))
    engine.add_node(GraphNode("p2", "paper", {"title": "Deep Learning Healthcare"}))
    engine.add_edge(GraphEdge("p1", "p2", "cites"))
    print(f"Nodes: {len(engine.nodes)}, Edges: {len(engine.edges)}")

    print("\n=== Adaptive RAG Demo ===")
    arag = AdaptiveRAG()
    assessment = arag.assess_query_complexity("What are the latest 2025 AI trends?")
    print(f"Strategy: {assessment['strategy']}")

    print("\n=== CRAG Demo ===")
    crag = CorrectiveRAG()
    result = crag.evaluate_retrieval("cancer treatment", [{"title": "Cancer drug discovery"}])
    print(f"Status: {result['status']}, Action: {result['action']}")
