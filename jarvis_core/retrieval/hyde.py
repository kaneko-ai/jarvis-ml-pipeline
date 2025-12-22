"""HyDE - Hypothetical Document Embeddings.

Per RP-302, generates hypothetical answers for query expansion.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Callable


@dataclass
class HyDEResult:
    """Result of HyDE query expansion."""
    
    original_query: str
    hypothetical_docs: List[str]
    combined_embedding: Optional[List[float]]


class HyDE:
    """Hypothetical Document Embeddings for query expansion.
    
    Per RP-302:
    - Generates hypothetical answer documents from query
    - Uses hypothetical doc embeddings for retrieval
    - Ensembles with original query
    """
    
    def __init__(
        self,
        generator: Optional[Callable[[str], str]] = None,
        embedder: Optional[Callable[[List[str]], List[List[float]]]] = None,
        num_hypotheticals: int = 3,
        ensemble_weight: float = 0.7,
    ):
        self.generator = generator
        self.embedder = embedder
        self.num_hypotheticals = num_hypotheticals
        self.ensemble_weight = ensemble_weight
    
    def generate_hypothetical(self, query: str) -> str:
        """Generate a hypothetical answer document.
        
        Args:
            query: The search query.
            
        Returns:
            Hypothetical document text.
        """
        if self.generator:
            return self.generator(query)
        
        # Default: simple template expansion
        return self._template_hypothetical(query)
    
    def _template_hypothetical(self, query: str) -> str:
        """Generate hypothetical using template."""
        templates = [
            f"Research shows that {query}. Studies have demonstrated...",
            f"According to recent findings, {query} is characterized by...",
            f"The mechanism of {query} involves key factors including...",
        ]
        
        import hashlib
        idx = int(hashlib.md5(query.encode()).hexdigest(), 16) % len(templates)
        return templates[idx]
    
    def expand_query(self, query: str) -> HyDEResult:
        """Expand query using HyDE.
        
        Args:
            query: Original search query.
            
        Returns:
            HyDEResult with hypothetical documents.
        """
        hypotheticals = []
        
        for i in range(self.num_hypotheticals):
            # Generate with slight variation
            variant_query = f"{query} (aspect {i + 1})"
            hyp = self.generate_hypothetical(variant_query)
            hypotheticals.append(hyp)
        
        # Generate combined embedding
        combined = None
        if self.embedder:
            # Embed original query
            query_emb = self.embedder([query])[0]
            
            # Embed hypotheticals
            hyp_embs = self.embedder(hypotheticals)
            
            # Weighted average
            combined = self._ensemble_embeddings(query_emb, hyp_embs)
        
        return HyDEResult(
            original_query=query,
            hypothetical_docs=hypotheticals,
            combined_embedding=combined,
        )
    
    def _ensemble_embeddings(
        self,
        query_emb: List[float],
        hyp_embs: List[List[float]],
    ) -> List[float]:
        """Ensemble query and hypothetical embeddings.
        
        Args:
            query_emb: Original query embedding.
            hyp_embs: Hypothetical document embeddings.
            
        Returns:
            Combined embedding vector.
        """
        if not hyp_embs:
            return query_emb
        
        dim = len(query_emb)
        
        # Average hypothetical embeddings
        avg_hyp = [0.0] * dim
        for emb in hyp_embs:
            for i in range(dim):
                avg_hyp[i] += emb[i] / len(hyp_embs)
        
        # Weighted combination
        combined = []
        for i in range(dim):
            val = (
                self.ensemble_weight * avg_hyp[i] +
                (1 - self.ensemble_weight) * query_emb[i]
            )
            combined.append(val)
        
        # Normalize
        norm = sum(x * x for x in combined) ** 0.5
        if norm > 0:
            combined = [x / norm for x in combined]
        
        return combined


def create_hyde_retriever(
    base_retriever,
    generator,
    embedder,
) -> Callable:
    """Create a HyDE-enhanced retriever.
    
    Args:
        base_retriever: Base retrieval function.
        generator: LLM generator function.
        embedder: Embedding function.
        
    Returns:
        Enhanced retriever function.
    """
    hyde = HyDE(generator=generator, embedder=embedder)
    
    def retrieve(query: str, top_k: int = 10):
        result = hyde.expand_query(query)
        
        # Search with combined embedding
        if result.combined_embedding:
            return base_retriever.search_by_vector(
                result.combined_embedding,
                top_k=top_k,
            )
        
        # Fallback to text search
        return base_retriever.search(query, top_k=top_k)
    
    return retrieve
