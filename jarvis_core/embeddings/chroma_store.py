"""ChromaDB Vector Store.

ChromaDB-based vector store for RAG applications.
Per JARVIS_COMPLETION_INSTRUCTION Task 1.2.4
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """ChromaDB-based vector store for RAG."""
    
    def __init__(
        self,
        collection_name: str = "jarvis_papers",
        persist_directory: Optional[Path] = None,
    ):
        """Initialize ChromaDB vector store.
        
        Args:
            collection_name: Name of the collection
            persist_directory: Optional directory for persistence
        """
        self._collection_name = collection_name
        self._persist_directory = persist_directory
        self._client = None
        self._collection = None
    
    def _init_client(self):
        """Initialize ChromaDB client."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
            except ImportError:
                raise ImportError(
                    "chromadb is required. Install with: pip install chromadb"
                )
            
            if self._persist_directory:
                self._persist_directory = Path(self._persist_directory)
                self._persist_directory.mkdir(parents=True, exist_ok=True)
                self._client = chromadb.PersistentClient(
                    path=str(self._persist_directory)
                )
            else:
                self._client = chromadb.Client()
            
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        
        return self._client, self._collection
    
    def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Add documents to the collection.
        
        Args:
            texts: Document texts
            embeddings: Pre-computed embeddings
            ids: Document IDs
            metadata: Optional metadata per document
        """
        _, collection = self._init_client()
        
        collection.add(
            documents=texts,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadata,
        )
        
        logger.info(f"Added {len(ids)} documents to ChromaDB")
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, str, Dict[str, Any]]]:
        """Search for similar documents.
        
        Args:
            query_embedding: Query embedding
            top_k: Number of results
            where: Optional metadata filter
            
        Returns:
            List of (doc_id, score, text, metadata) tuples
        """
        _, collection = self._init_client()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        
        output = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if results["distances"] else 0.0
                # Convert distance to similarity (1 - distance for cosine)
                score = 1.0 - distance
                text = results["documents"][0][i] if results["documents"] else ""
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                output.append((doc_id, score, text, meta))
        
        return output
    
    def delete(self, ids: List[str]) -> None:
        """Delete documents by ID.
        
        Args:
            ids: Document IDs to delete
        """
        _, collection = self._init_client()
        collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} documents from ChromaDB")
    
    @property
    def count(self) -> int:
        """Return number of documents in collection."""
        _, collection = self._init_client()
        return collection.count()
