"""Adaptive Chunking v2.

Per RP-300, implements structure-aware dynamic chunking.
"""
from __future__ import annotations

import re
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class ContentType(Enum):
    """Content types for adaptive chunking."""
    
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    METHODS = "methods"
    RESULTS = "results"
    DISCUSSION = "discussion"
    REFERENCES = "references"
    FIGURE_CAPTION = "figure_caption"
    TABLE_CAPTION = "table_caption"
    SUPPLEMENTARY = "supplementary"
    UNKNOWN = "unknown"


# Optimal chunk sizes per content type
CHUNK_SIZE_MAP = {
    ContentType.ABSTRACT: 500,
    ContentType.INTRODUCTION: 400,
    ContentType.METHODS: 300,
    ContentType.RESULTS: 350,
    ContentType.DISCUSSION: 400,
    ContentType.FIGURE_CAPTION: 200,
    ContentType.TABLE_CAPTION: 200,
    ContentType.REFERENCES: 150,
    ContentType.SUPPLEMENTARY: 300,
    ContentType.UNKNOWN: 350,
}


@dataclass
class AdaptiveChunk:
    """A chunk with adaptive properties."""
    
    chunk_id: str
    text: str
    content_type: ContentType
    section_title: Optional[str]
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    related_chunks: List[str] = field(default_factory=list)


class AdaptiveChunker:
    """Structure-aware dynamic chunker.
    
    Per RP-300:
    - Respects section boundaries
    - Independent figure/table caption chunks
    - Maintains reference relations via chunk IDs
    - Optimizes chunk_size per content_type
    """
    
    def __init__(
        self,
        default_size: int = 350,
        overlap: int = 50,
        respect_boundaries: bool = True,
    ):
        self.default_size = default_size
        self.overlap = overlap
        self.respect_boundaries = respect_boundaries
    
    def chunk(
        self,
        text: str,
        sections: Optional[List[Dict[str, Any]]] = None,
    ) -> List[AdaptiveChunk]:
        """Chunk text adaptively.
        
        Args:
            text: Full document text.
            sections: Optional section annotations.
            
        Returns:
            List of AdaptiveChunk objects.
        """
        chunks = []
        
        if sections:
            # Section-aware chunking
            chunks = self._chunk_by_sections(text, sections)
        else:
            # Auto-detect sections
            detected = self._detect_sections(text)
            if detected:
                chunks = self._chunk_by_sections(text, detected)
            else:
                chunks = self._chunk_flat(text)
        
        # Extract figure/table captions as independent chunks
        caption_chunks = self._extract_captions(text)
        chunks.extend(caption_chunks)
        
        # Link related chunks
        self._link_related_chunks(chunks)
        
        return chunks
    
    def _detect_sections(self, text: str) -> List[Dict[str, Any]]:
        """Auto-detect sections from text."""
        patterns = [
            (r"(?i)\babstract\b", ContentType.ABSTRACT),
            (r"(?i)\bintroduction\b", ContentType.INTRODUCTION),
            (r"(?i)\b(methods?|materials?)\b", ContentType.METHODS),
            (r"(?i)\bresults?\b", ContentType.RESULTS),
            (r"(?i)\bdiscussion\b", ContentType.DISCUSSION),
            (r"(?i)\breferences?\b", ContentType.REFERENCES),
        ]
        
        sections = []
        for pattern, content_type in patterns:
            for match in re.finditer(pattern, text):
                sections.append({
                    "start": match.start(),
                    "title": match.group(),
                    "type": content_type,
                })
        
        # Sort by position
        sections.sort(key=lambda x: x["start"])
        
        # Add end positions
        for i, section in enumerate(sections):
            if i + 1 < len(sections):
                section["end"] = sections[i + 1]["start"]
            else:
                section["end"] = len(text)
        
        return sections
    
    def _chunk_by_sections(
        self,
        text: str,
        sections: List[Dict[str, Any]],
    ) -> List[AdaptiveChunk]:
        """Chunk respecting section boundaries."""
        chunks = []
        
        for section in sections:
            content_type = section.get("type", ContentType.UNKNOWN)
            if isinstance(content_type, str):
                content_type = ContentType(content_type) if content_type in [e.value for e in ContentType] else ContentType.UNKNOWN
            
            chunk_size = CHUNK_SIZE_MAP.get(content_type, self.default_size)
            section_text = text[section["start"]:section["end"]]
            section_title = section.get("title", "")
            
            # Split section into chunks
            section_chunks = self._split_text(
                section_text,
                chunk_size,
                section["start"],
                content_type,
                section_title,
            )
            chunks.extend(section_chunks)
        
        return chunks
    
    def _chunk_flat(self, text: str) -> List[AdaptiveChunk]:
        """Chunk without section awareness."""
        return self._split_text(
            text,
            self.default_size,
            0,
            ContentType.UNKNOWN,
            None,
        )
    
    def _split_text(
        self,
        text: str,
        chunk_size: int,
        base_offset: int,
        content_type: ContentType,
        section_title: Optional[str],
    ) -> List[AdaptiveChunk]:
        """Split text into chunks."""
        chunks = []
        
        # Split by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = []
        current_len = 0
        chunk_start = base_offset
        
        for sentence in sentences:
            sentence_len = len(sentence)
            
            if current_len + sentence_len > chunk_size and current_chunk:
                # Finalize current chunk
                chunk_text = " ".join(current_chunk)
                chunk_id = self._generate_chunk_id(chunk_text, chunk_start)
                
                chunks.append(AdaptiveChunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    content_type=content_type,
                    section_title=section_title,
                    start_char=chunk_start,
                    end_char=chunk_start + len(chunk_text),
                ))
                
                # Start new chunk with overlap
                if self.overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-1] if len(current_chunk[-1]) <= self.overlap else ""
                    current_chunk = [overlap_text] if overlap_text else []
                    current_len = len(overlap_text)
                else:
                    current_chunk = []
                    current_len = 0
                
                chunk_start += len(chunk_text) + 1
            
            current_chunk.append(sentence)
            current_len += sentence_len + 1
        
        # Final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk_id = self._generate_chunk_id(chunk_text, chunk_start)
            
            chunks.append(AdaptiveChunk(
                chunk_id=chunk_id,
                text=chunk_text,
                content_type=content_type,
                section_title=section_title,
                start_char=chunk_start,
                end_char=chunk_start + len(chunk_text),
            ))
        
        return chunks
    
    def _extract_captions(self, text: str) -> List[AdaptiveChunk]:
        """Extract figure and table captions as independent chunks."""
        chunks = []
        
        # Figure captions
        fig_pattern = r"(?i)(Figure\s+\d+[.:]\s*[^\n]+)"
        for match in re.finditer(fig_pattern, text):
            chunk_id = self._generate_chunk_id(match.group(1), match.start())
            chunks.append(AdaptiveChunk(
                chunk_id=chunk_id,
                text=match.group(1),
                content_type=ContentType.FIGURE_CAPTION,
                section_title="Figures",
                start_char=match.start(),
                end_char=match.end(),
            ))
        
        # Table captions
        table_pattern = r"(?i)(Table\s+\d+[.:]\s*[^\n]+)"
        for match in re.finditer(table_pattern, text):
            chunk_id = self._generate_chunk_id(match.group(1), match.start())
            chunks.append(AdaptiveChunk(
                chunk_id=chunk_id,
                text=match.group(1),
                content_type=ContentType.TABLE_CAPTION,
                section_title="Tables",
                start_char=match.start(),
                end_char=match.end(),
            ))
        
        return chunks
    
    def _link_related_chunks(self, chunks: List[AdaptiveChunk]) -> None:
        """Link related chunks (e.g., figure references)."""
        # Build index of figure/table chunks
        caption_ids = {}
        for chunk in chunks:
            if chunk.content_type in [ContentType.FIGURE_CAPTION, ContentType.TABLE_CAPTION]:
                # Extract figure/table number
                match = re.search(r"(?i)(Figure|Table)\s+(\d+)", chunk.text)
                if match:
                    key = f"{match.group(1).lower()}_{match.group(2)}"
                    caption_ids[key] = chunk.chunk_id
        
        # Link chunks that reference figures/tables
        for chunk in chunks:
            for key, caption_id in caption_ids.items():
                # Build pattern without f-string backslash issue
                pattern_key = key.replace('_', r'\s+')
                ref_pattern = f"(?i){pattern_key}"
                if re.search(ref_pattern, chunk.text) and chunk.chunk_id != caption_id:
                    if caption_id not in chunk.related_chunks:
                        chunk.related_chunks.append(caption_id)
    
    def _generate_chunk_id(self, text: str, offset: int) -> str:
        """Generate stable chunk ID."""
        content = f"{text[:50]}:{offset}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
