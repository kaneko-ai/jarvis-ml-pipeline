"""Unified Chunker and Sectionizer (Phase 23).

Standardizes chunk_id generation and section detection to ensure reproducibility.
"""

import hashlib
import re
from typing import List
from jarvis_core.ingestion.pipeline import TextChunk


class StandardChunker:
    """Standardized text chunker with deterministic IDs and deduplication."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, doc_id: str, section_name: str = "Full Text") -> List[TextChunk]:
        """Chunk text into segments with deterministic IDs."""
        # 1. Deduplicate consecutive paragraphs
        paragraphs = self._cleanup_paragraphs(text)
        
        chunks = []
        current_chunk_paragraphs = []
        current_len = 0
        idx = 0

        for para in paragraphs:
            if current_len + len(para) > self.chunk_size and current_chunk_paragraphs:
                # Flush
                chunk_text = "\n\n".join(current_chunk_paragraphs)
                chunks.append(self._create_chunk(chunk_text, doc_id, section_name, idx))
                idx += 1
                
                # Simple overlap: keep last paragraph if enabled
                if self.overlap > 0:
                    current_chunk_paragraphs = [current_chunk_paragraphs[-1]]
                    current_len = len(current_chunk_paragraphs[0])
                else:
                    current_chunk_paragraphs = []
                    current_len = 0
            
            current_chunk_paragraphs.append(para)
            current_len += len(para)
        
        # Last chunk
        if current_chunk_paragraphs:
            chunk_text = "\n\n".join(current_chunk_paragraphs)
            chunks.append(self._create_chunk(chunk_text, doc_id, section_name, idx))

        return chunks

    def _create_chunk(self, text: str, doc_id: str, section: str, index: int) -> TextChunk:
        # Deterministic ID: doc_id + sanitized section + index
        sanitized_section = re.sub(r'\W+', '_', section).lower()
        chunk_id = f"{doc_id}_{sanitized_section}_{index}"
        
        return TextChunk(
            chunk_id=chunk_id,
            text=text,
            section=section,
            paragraph_index=index # Simplified for v2
        )

    def _cleanup_paragraphs(self, text: str) -> List[str]:
        # Split and deduplicate
        paras = re.split(r'\n\s*\n', text)
        cleaned = []
        seen = set()
        for p in paras:
            p = p.strip()
            if not p: continue
            
            # Simple content based dedupe to prevent duplicate extractions
            p_hash = hashlib.md5(p.encode(), usedforsecurity=False).hexdigest()
            if p_hash not in seen:
                cleaned.append(p)
                seen.add(p_hash)
        return cleaned


class Sectionizer:
    """Heuristic based section detector for scientific papers."""
    
    PATTERNS = [
        (r"(?i)^(Abstract|ABSTRACT)", "Abstract"),
        (r"(?i)^(Introduction|INTRODUCTION|Background)", "Introduction"),
        (r"(?i)^(Methods?|METHODS?|Materials? and Methods?)", "Methods"),
        (r"(?i)^(Results?|RESULTS?)", "Results"),
        (r"(?i)^(Discussion|DISCUSSION)", "Discussion"),
        (r"(?i)^(Conclusion|CONCLUSION|Conclusions?)", "Conclusion"),
        (r"(?i)^(References?|REFERENCES?|Bibliography)", "References"),
    ]

    def split_by_sections(self, text: str) -> List[dict]:
        """Split a long text into named sections."""
        lines = text.split("\n")
        sections = []
        current_section = "Main"
        current_buffer = []

        for line in lines:
            line_strip = line.strip()
            found_new = False
            for pattern, name in self.PATTERNS:
                if re.match(pattern, line_strip):
                    # Flush old
                    if current_buffer:
                        sections.append({"name": current_section, "text": "\n".join(current_buffer)})
                    
                    current_section = name
                    current_buffer = [line]
                    found_new = True
                    break
            
            if not found_new:
                current_buffer.append(line)

        if current_buffer:
            sections.append({"name": current_section, "text": "\n".join(current_buffer)})
        
        return sections
