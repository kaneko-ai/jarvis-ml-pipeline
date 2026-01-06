"""Sample Plugins for JARVIS.

Example plugins demonstrating the plugin system.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .plugin_system import (
    Plugin, SourcePlugin, AnalyzerPlugin, ExporterPlugin,
    PluginType, register_plugin
)


@register_plugin
class BibtexExporterPlugin(ExporterPlugin):
    """Export results to BibTeX format."""
    
    NAME = "bibtex_exporter"
    VERSION = "1.0.0"
    PLUGIN_TYPE = PluginType.EXPORTER
    DESCRIPTION = "Export papers to BibTeX format"
    AUTHOR = "JARVIS Team"
    
    def initialize(self) -> bool:
        return True
    
    def export(
        self,
        data: List[Dict],
        output_path: Optional[Path] = None,
        **kwargs
    ) -> str:
        """Export papers to BibTeX."""
        entries = []
        
        for i, paper in enumerate(data):
            entry = self._paper_to_bibtex(paper, i)
            entries.append(entry)
        
        bibtex = "\n\n".join(entries)
        
        if output_path:
            output_path.write_text(bibtex, encoding="utf-8")
            return str(output_path)
        
        return bibtex
    
    def _paper_to_bibtex(self, paper: Dict, index: int) -> str:
        """Convert paper dict to BibTeX entry."""
        entry_type = paper.get("type", "article")
        key = paper.get("key", f"paper{index}")
        
        # Build fields
        fields = []
        
        if paper.get("title"):
            fields.append(f'  title = {{{paper["title"]}}}')
        
        if paper.get("authors"):
            authors = paper["authors"]
            if isinstance(authors, list):
                authors = " and ".join(authors)
            fields.append(f'  author = {{{authors}}}')
        
        if paper.get("year"):
            fields.append(f'  year = {{{paper["year"]}}}')
        
        if paper.get("journal") or paper.get("venue"):
            journal = paper.get("journal") or paper.get("venue")
            fields.append(f'  journal = {{{journal}}}')
        
        if paper.get("doi"):
            fields.append(f'  doi = {{{paper["doi"]}}}')
        
        if paper.get("abstract"):
            abstract = paper["abstract"][:500].replace("{", "").replace("}", "")
            fields.append(f'  abstract = {{{abstract}}}')
        
        fields_str = ",\n".join(fields)
        return f"@{entry_type}{{{key},\n{fields_str}\n}}"


@register_plugin 
class JSONExporterPlugin(ExporterPlugin):
    """Export results to JSON format."""
    
    NAME = "json_exporter"
    VERSION = "1.0.0"
    PLUGIN_TYPE = PluginType.EXPORTER
    DESCRIPTION = "Export data to JSON format"
    AUTHOR = "JARVIS Team"
    
    def initialize(self) -> bool:
        return True
    
    def export(
        self,
        data: Any,
        output_path: Optional[Path] = None,
        **kwargs
    ) -> str:
        """Export data to JSON."""
        indent = kwargs.get("indent", 2)
        
        json_str = json.dumps(data, indent=indent, ensure_ascii=False, default=str)
        
        if output_path:
            output_path.write_text(json_str, encoding="utf-8")
            return str(output_path)
        
        return json_str


@register_plugin
class WordCountAnalyzer(AnalyzerPlugin):
    """Analyze word count and text statistics."""
    
    NAME = "word_count"
    VERSION = "1.0.0"
    PLUGIN_TYPE = PluginType.ANALYZER
    DESCRIPTION = "Analyze word count and text statistics"
    AUTHOR = "JARVIS Team"
    
    def initialize(self) -> bool:
        return True
    
    def analyze(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Analyze text data."""
        if isinstance(data, str):
            texts = [data]
        elif isinstance(data, list):
            texts = [str(item) for item in data]
        else:
            texts = [str(data)]
        
        total_chars = sum(len(t) for t in texts)
        total_words = sum(len(t.split()) for t in texts)
        total_sentences = sum(t.count(".") + t.count("!") + t.count("?") for t in texts)
        
        return {
            "total_items": len(texts),
            "total_characters": total_chars,
            "total_words": total_words,
            "total_sentences": total_sentences,
            "avg_words_per_item": total_words / len(texts) if texts else 0,
            "avg_chars_per_word": total_chars / total_words if total_words else 0,
        }


@register_plugin
class KeywordExtractor(AnalyzerPlugin):
    """Extract keywords from text."""
    
    NAME = "keyword_extractor"
    VERSION = "1.0.0"
    PLUGIN_TYPE = PluginType.ANALYZER
    DESCRIPTION = "Extract keywords from text using TF-IDF-like scoring"
    AUTHOR = "JARVIS Team"
    
    # Common stopwords to filter out
    STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
        "be", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "this", "that", "these",
        "those", "it", "its", "they", "their", "we", "our", "you", "your",
    }
    
    def initialize(self) -> bool:
        return True
    
    def analyze(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Extract keywords from text."""
        if isinstance(data, str):
            text = data
        elif isinstance(data, list):
            text = " ".join(str(item) for item in data)
        else:
            text = str(data)
        
        # Simple word frequency
        words = text.lower().split()
        word_counts: Dict[str, int] = {}
        
        for word in words:
            # Clean word
            word = "".join(c for c in word if c.isalnum())
            if len(word) < 3 or word in self.STOPWORDS:
                continue
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(
            word_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        top_n = kwargs.get("top_n", 10)
        
        return {
            "keywords": [
                {"word": word, "count": count}
                for word, count in sorted_words[:top_n]
            ],
            "total_unique_words": len(word_counts),
            "total_words_analyzed": len(words),
        }
