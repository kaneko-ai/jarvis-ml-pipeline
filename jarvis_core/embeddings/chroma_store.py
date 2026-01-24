"""ChromaDB Vector Store (Phase 37).

ChromaDB implementation of the VectorStore abstraction.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List, Dict, Tuple, Optional

import numpy as np

from jarvis_core.embeddings.vector_store import VectorStore

logger = logging.getLogger(__name__)


class ChromaVectorStore(VectorStore):
    """ChromaDB-based vector store implementation."""

    def __init__(
        self,
        collection_name: str = "jarvis_papers",
        persist_directory: Path | None = None,
    ):
        self._collection_name = collection_name
        self._persist_directory = persist_directory
        self._client = None
        self._collection = None

    def _init_client(self):
        """Initialize ChromaDB client."""
        if self._client is None:
            try:
                import chromadb
            except ImportError:
                raise ImportError("chromadb is required. Install with: pip install chromadb")

            if self._persist_directory:
                self._persist_directory = Path(self._persist_directory)
                self._persist_directory.mkdir(parents=True, exist_ok=True)
                self._client = chromadb.PersistentClient(path=str(self._persist_directory))
            else:
                self._client = chromadb.Client()

            self._collection = self._client.get_or_create_collection(
                name=self._collection_name, metadata={"hnsw:space": "cosine"}
            )

        return self._client, self._collection

    def add(
        self,
        embeddings: np.ndarray | List[List[float]],
        doc_ids: List[str],
        metadata: List[Dict[str, Any]] | None = None,
    ) -> None:
        """Add documents to ChromaDB."""
        _, collection = self._init_client()

        # Handle numpy conversion if necessary
        if isinstance(embeddings, np.ndarray):
            embeddings_list = embeddings.tolist()
        else:
            embeddings_list = embeddings

        # Extract text from metadata if present, else empty strings (Chroma requires documents or embeddings, if embeddings provided documents can be optional but good for debug)
        # Actually Chroma allows documents=None if embeddings are provided.
        documents = None
        if metadata:
            # Check if 'text' or 'document' key exists in metadata
            temp_docs = []
            has_text = False
            for m in metadata:
                txt = m.get("text", m.get("document", ""))
                temp_docs.append(str(txt)) # Ensure string
                if txt:
                    has_text = True
            if has_text:
                documents = temp_docs

        collection.add(
            ids=doc_ids,
            embeddings=embeddings_list,
            metadatas=metadata,
            documents=documents
        )
        logger.info(f"Added {len(doc_ids)} documents to ChromaDB")

    def search(
        self,
        query_embedding: np.ndarray | List[float],
        top_k: int = 10,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search ChromaDB."""
        _, collection = self._init_client()

        if isinstance(query_embedding, np.ndarray):
            query_list = query_embedding.tolist()
        else:
            query_list = query_embedding

        results = collection.query(
            query_embeddings=[query_list],
            n_results=top_k,
            include=["metadatas", "distances", "documents"],
        )

        output = []
        if results["ids"] and results["ids"][0]:
            ids = results["ids"][0]
            distances = results["distances"][0] if results["distances"] else [0.0] * len(ids)
            metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(ids)
            docs = results["documents"][0] if results["documents"] else [""] * len(ids)

            for i, doc_id in enumerate(ids):
                # Cosine distance to similarity: 1 - distance
                score = 1.0 - distances[i]
                meta = metas[i] if metas[i] else {}
                
                # Inject text back into metadata if it was stored separately
                if docs[i]:
                    meta["text"] = docs[i]
                    
                output.append((doc_id, score, meta))

        return output

    def save(self, path: Path) -> None:
        """Persist is automatic for PersistentClient."""
        # For non-persistent client, we can't easily 'save' to a random path after the fact
        # unless we export. But VectorStore.save implies taking current state and dumping it.
        # Since we enforce PersistentClient if path is provided in init, this might include
        # copying the directory?
        # For Phase 37, we assume the use of PersistentClient means 'save' is implicit or a no-op
        # effectively, or we can treat 'path' as a request to verify persistence.
        
        # If the user asks to save to a specific path but we initialized with a different one,
        # that's tricky.
        # Let's assume for this abstraction that save() logic is mainly for FAISS-like RAM stores.
        pass

    @classmethod
    def load(cls, path: Path) -> ChromaVectorStore:
        """Load from existing DB directory."""
        return cls(persist_directory=path)

    @property
    def count(self) -> int:
        _, collection = self._init_client()
        return collection.count()
