"""ITER-07: 文章品質保証 (Text Quality Assurance).

生成テキストの品質チェック。
- 文法チェック
- 一貫性チェック
- 冗長性検出
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TextQualityResult:
    """テキスト品質結果."""
    passed: bool = True
    score: float = 0.0
    issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "score": self.score,
            "issues": self.issues,
            "suggestions": self.suggestions,
        }


class TextQualityAssurer:
    """テキスト品質保証器.
    
    生成テキストの品質をチェック。
    """
    
    def __init__(self, min_score: float = 0.7):
        self.min_score = min_score
    
    def check(self, text: str) -> TextQualityResult:
        """テキスト品質をチェック."""
        result = TextQualityResult()
        
        checks = [
            self._check_length(text),
            self._check_repetition(text),
            self._check_incomplete_sentences(text),
            self._check_citation_format(text),
            self._check_coherence(text),
        ]
        
        total_score = 0.0
        for check in checks:
            total_score += check["score"]
            if check.get("issue"):
                result.issues.append(check["issue"])
            if check.get("suggestion"):
                result.suggestions.append(check["suggestion"])
        
        result.score = total_score / len(checks)
        result.passed = result.score >= self.min_score
        
        return result
    
    def _check_length(self, text: str) -> Dict[str, Any]:
        """長さチェック."""
        word_count = len(text.split())
        
        if word_count < 50:
            return {
                "score": 0.3,
                "issue": {"type": "too_short", "word_count": word_count},
                "suggestion": "テキストが短すぎます。詳細を追加してください。",
            }
        elif word_count > 5000:
            return {
                "score": 0.6,
                "issue": {"type": "too_long", "word_count": word_count},
                "suggestion": "テキストが長すぎます。簡潔にまとめてください。",
            }
        else:
            return {"score": 1.0}
    
    def _check_repetition(self, text: str) -> Dict[str, Any]:
        """繰り返しチェック."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip().lower() for s in sentences if s.strip()]
        
        if len(sentences) < 2:
            return {"score": 1.0}
        
        unique = set(sentences)
        ratio = len(unique) / len(sentences)
        
        if ratio < 0.8:
            return {
                "score": ratio,
                "issue": {"type": "repetition", "unique_ratio": ratio},
                "suggestion": "同じ文が繰り返されています。",
            }
        
        return {"score": 1.0}
    
    def _check_incomplete_sentences(self, text: str) -> Dict[str, Any]:
        """不完全な文チェック."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        incomplete = 0
        
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            
            # 開始が小文字
            if sent[0].islower() and not sent.startswith(('e.g.', 'i.e.', 'etc.')):
                incomplete += 1
            
            # 終わりが句読点でない
            if not sent[-1] in '.!?':
                incomplete += 1
        
        if len(sentences) == 0:
            return {"score": 1.0}
        
        ratio = 1 - (incomplete / (len(sentences) * 2))
        
        if ratio < 0.8:
            return {
                "score": max(0, ratio),
                "issue": {"type": "incomplete_sentences", "count": incomplete},
                "suggestion": "不完全な文があります。文法を確認してください。",
            }
        
        return {"score": 1.0}
    
    def _check_citation_format(self, text: str) -> Dict[str, Any]:
        """引用形式チェック."""
        # 引用がある場合、形式が統一されているか
        citations = re.findall(r'\[([^\]]+)\]', text)
        
        if not citations:
            return {"score": 1.0}  # 引用なしはOK
        
        # 引用形式の種類をカウント
        numeric = sum(1 for c in citations if c.isdigit())
        alpha = sum(1 for c in citations if re.match(r'^[A-Za-z]+\d{4}', c))
        
        total = len(citations)
        max_type = max(numeric, alpha)
        
        if max_type / total < 0.8:
            return {
                "score": 0.7,
                "issue": {"type": "inconsistent_citations"},
                "suggestion": "引用形式が統一されていません。",
            }
        
        return {"score": 1.0}
    
    def _check_coherence(self, text: str) -> Dict[str, Any]:
        """一貫性チェック."""
        paragraphs = text.split('\n\n')
        
        if len(paragraphs) < 2:
            return {"score": 1.0}
        
        # 接続詞の存在をチェック
        connectors = [
            'however', 'therefore', 'moreover', 'furthermore',
            'in addition', 'additionally', 'consequently', 'thus',
            'on the other hand', 'in contrast', 'similarly',
        ]
        
        has_connector = sum(
            1 for p in paragraphs[1:]
            if any(c in p.lower() for c in connectors)
        )
        
        ratio = has_connector / (len(paragraphs) - 1) if len(paragraphs) > 1 else 1
        
        if ratio < 0.3:
            return {
                "score": 0.7,
                "suggestion": "段落間の接続詞を追加すると読みやすくなります。",
            }
        
        return {"score": 1.0}


def check_text_quality(text: str, min_score: float = 0.7) -> TextQualityResult:
    """便利関数: テキスト品質をチェック."""
    assurer = TextQualityAssurer(min_score)
    return assurer.check(text)
