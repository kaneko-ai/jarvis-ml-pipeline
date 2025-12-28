"""ITER2-01: 文ID/オフセット精密化 (Sentence ID Precision).

文レベルでの正確な位置特定。
- 文ID生成
- オフセット管理
- 位置情報の精密化
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class SentenceLocator:
    """文のロケータ."""
    sentence_id: str
    paper_id: str
    section: str
    paragraph_index: int
    sentence_index: int
    char_start: int
    char_end: int
    text: str
    
    def to_dict(self) -> dict:
        return {
            "sentence_id": self.sentence_id,
            "paper_id": self.paper_id,
            "section": self.section,
            "paragraph_index": self.paragraph_index,
            "sentence_index": self.sentence_index,
            "char_start": self.char_start,
            "char_end": self.char_end,
        }
    
    def to_canonical(self) -> str:
        """正規形式に変換."""
        return f"{self.paper_id}|{self.section}|P{self.paragraph_index}|S{self.sentence_index}"


class SentenceIndexer:
    """文インデクサ.
    
    文レベルでの位置情報を管理。
    """
    
    def __init__(self):
        self._index: Dict[str, SentenceLocator] = {}
    
    def index_text(
        self,
        text: str,
        paper_id: str,
        section: str = "Unknown",
    ) -> List[SentenceLocator]:
        """テキストから文をインデックス."""
        locators = []
        
        paragraphs = re.split(r'\n\s*\n', text)
        char_pos = 0
        
        for para_idx, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                char_pos += len(para) + 2
                continue
            
            sentences = self._split_sentences(para)
            sent_start = 0
            
            for sent_idx, sent in enumerate(sentences):
                if not sent.strip():
                    continue
                
                # 文IDを生成
                sent_id = self._generate_sentence_id(paper_id, section, para_idx, sent_idx)
                
                locator = SentenceLocator(
                    sentence_id=sent_id,
                    paper_id=paper_id,
                    section=section,
                    paragraph_index=para_idx,
                    sentence_index=sent_idx,
                    char_start=char_pos + sent_start,
                    char_end=char_pos + sent_start + len(sent),
                    text=sent.strip(),
                )
                
                locators.append(locator)
                self._index[sent_id] = locator
                
                sent_start += len(sent) + 1
            
            char_pos += len(para) + 2
        
        return locators
    
    def _split_sentences(self, text: str) -> List[str]:
        """文に分割."""
        # 略語を保護
        text = re.sub(r'(Dr|Mr|Mrs|Ms|Prof|etc|e\.g|i\.e)\. ', r'\1<DOT> ', text)
        
        # 文分割
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # 略語を復元
        sentences = [s.replace('<DOT>', '.') for s in sentences]
        
        return sentences
    
    def _generate_sentence_id(
        self,
        paper_id: str,
        section: str,
        para_idx: int,
        sent_idx: int,
    ) -> str:
        """文IDを生成."""
        source = f"{paper_id}:{section}:{para_idx}:{sent_idx}"
        hash_val = hashlib.sha256(source.encode()).hexdigest()[:8]
        return f"sent_{hash_val}"
    
    def get_sentence(self, sentence_id: str) -> SentenceLocator | None:
        """文を取得."""
        return self._index.get(sentence_id)
    
    def find_by_text(self, text: str, fuzzy: bool = False) -> List[SentenceLocator]:
        """テキストで文を検索."""
        results = []
        text_lower = text.lower().strip()
        
        for locator in self._index.values():
            if fuzzy:
                if text_lower in locator.text.lower():
                    results.append(locator)
            else:
                if locator.text.lower().strip() == text_lower:
                    results.append(locator)
        
        return results


def index_sentences(
    text: str,
    paper_id: str,
    section: str = "Unknown",
) -> List[SentenceLocator]:
    """便利関数: 文をインデックス."""
    indexer = SentenceIndexer()
    return indexer.index_text(text, paper_id, section)
