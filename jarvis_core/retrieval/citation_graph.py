"""Citation Graph Retrieval.

Per RP-306, uses citation graph for related paper discovery.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
import time


@dataclass
class CitationNode:
    """A node in the citation graph."""
    
    paper_id: str
    title: str
    year: Optional[int]
    citation_count: int
    references: List[str] = field(default_factory=list)
    cited_by: List[str] = field(default_factory=list)


@dataclass
class CitationPath:
    """A path through the citation graph."""
    
    source_id: str
    target_id: str
    path: List[str]
    hop_count: int
    score: float


class CitationGraphRetriever:
    """Uses citation graph for discovery.
    
    Per RP-306:
    - Semantic Scholar API integration
    - 2-hop citation/reference exploration
    - Citation count scoring
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        max_hops: int = 2,
        cache: Optional[Dict] = None,
    ):
        self.api_key = api_key
        self.max_hops = max_hops
        self._cache = cache or {}
        self._graph: Dict[str, CitationNode] = {}
    
    def build_graph(
        self,
        seed_papers: List[str],
        depth: int = 2,
    ) -> Dict[str, CitationNode]:
        """Build citation graph from seed papers.
        
        Args:
            seed_papers: List of paper IDs (DOI, PMID, etc.).
            depth: Exploration depth.
            
        Returns:
            Citation graph.
        """
        visited: Set[str] = set()
        queue = [(pid, 0) for pid in seed_papers]
        
        while queue:
            paper_id, current_depth = queue.pop(0)
            
            if paper_id in visited or current_depth > depth:
                continue
            
            visited.add(paper_id)
            
            # Fetch paper data
            node = self._fetch_paper(paper_id)
            if node:
                self._graph[paper_id] = node
                
                # Add references and citations to queue
                if current_depth < depth:
                    for ref_id in node.references[:10]:  # Limit
                        if ref_id not in visited:
                            queue.append((ref_id, current_depth + 1))
                    for citer_id in node.cited_by[:10]:
                        if citer_id not in visited:
                            queue.append((citer_id, current_depth + 1))
        
        return self._graph
    
    def _fetch_paper(self, paper_id: str) -> Optional[CitationNode]:
        """Fetch paper data from API or cache."""
        if paper_id in self._cache:
            return self._cache[paper_id]
        
        # Placeholder - would use Semantic Scholar API
        # In production: requests.get(f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}")
        
        node = CitationNode(
            paper_id=paper_id,
            title=f"Paper {paper_id}",
            year=2023,
            citation_count=10,
            references=[],
            cited_by=[],
        )
        
        self._cache[paper_id] = node
        return node
    
    def find_related(
        self,
        paper_id: str,
        top_k: int = 10,
    ) -> List[CitationNode]:
        """Find related papers via citation graph.
        
        Args:
            paper_id: Source paper ID.
            top_k: Number of results.
            
        Returns:
            Related papers sorted by relevance.
        """
        if paper_id not in self._graph:
            self.build_graph([paper_id])
        
        source = self._graph.get(paper_id)
        if not source:
            return []
        
        # Score by citation connection
        scores: Dict[str, float] = {}
        
        # Direct references (high score)
        for ref_id in source.references:
            if ref_id in self._graph:
                node = self._graph[ref_id]
                scores[ref_id] = 1.0 + (node.citation_count / 100)
        
        # Direct citations (medium score)
        for citer_id in source.cited_by:
            if citer_id in self._graph:
                node = self._graph[citer_id]
                scores[citer_id] = 0.8 + (node.citation_count / 100)
        
        # 2-hop connections (lower score)
        for ref_id in source.references:
            if ref_id in self._graph:
                ref_node = self._graph[ref_id]
                for ref2_id in ref_node.references:
                    if ref2_id not in scores and ref2_id in self._graph:
                        node = self._graph[ref2_id]
                        scores[ref2_id] = 0.5 + (node.citation_count / 100)
        
        # Sort and return
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        return [self._graph[pid] for pid in sorted_ids[:top_k] if pid in self._graph]
    
    def get_citation_path(
        self,
        source_id: str,
        target_id: str,
    ) -> Optional[CitationPath]:
        """Find citation path between two papers.
        
        Args:
            source_id: Source paper.
            target_id: Target paper.
            
        Returns:
            CitationPath or None.
        """
        if source_id not in self._graph:
            self.build_graph([source_id])
        
        # BFS for shortest path
        visited: Set[str] = {source_id}
        queue = [(source_id, [source_id])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if current_id == target_id:
                return CitationPath(
                    source_id=source_id,
                    target_id=target_id,
                    path=path,
                    hop_count=len(path) - 1,
                    score=1.0 / len(path),
                )
            
            node = self._graph.get(current_id)
            if node and len(path) < self.max_hops + 1:
                for neighbor_id in node.references + node.cited_by:
                    if neighbor_id not in visited and neighbor_id in self._graph:
                        visited.add(neighbor_id)
                        queue.append((neighbor_id, path + [neighbor_id]))
        
        return None
