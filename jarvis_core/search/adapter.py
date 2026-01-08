"""ITER-01: 検索適応性強化 (Search Adaptability).

検索クエリの自動調整と拡張。
- 同義語展開
- エンティティ認識
- クエリ分解
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class AdaptedQuery:
    """適応されたクエリ."""
    original: str
    expanded: str
    entities: list[str] = field(default_factory=list)
    synonyms: dict[str, list[str]] = field(default_factory=dict)
    decomposed: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "original": self.original,
            "expanded": self.expanded,
            "entities": self.entities,
            "synonyms": self.synonyms,
            "decomposed": self.decomposed,
            "confidence": self.confidence,
        }


# 生物医学エンティティ辞書
BIOMEDICAL_ENTITIES = {
    "genes": [
        r"\b[A-Z][A-Z0-9]{1,5}\b",  # Gene symbols (CD73, PDL1, etc.)
    ],
    "diseases": [
        "cancer", "tumor", "carcinoma", "melanoma", "lymphoma",
        "leukemia", "adenocarcinoma", "sarcoma",
    ],
    "drugs": [
        "pembrolizumab", "nivolumab", "ipilimumab", "atezolizumab",
        "durvalumab", "avelumab",
    ],
    "pathways": [
        "adenosine pathway", "pd-1 pathway", "ctla-4 pathway",
        "jak-stat", "mapk", "pi3k-akt",
    ],
}


class QueryAdapter:
    """クエリ適応器.
    
    検索クエリを自動的に改善。
    """

    def __init__(self, domain: str = "immuno_onco"):
        self.domain = domain
        from jarvis_tools.papers.query_builder import DOMAIN_SYNONYMS
        self.synonyms = DOMAIN_SYNONYMS.get(f"{domain}_preclinical", {})

    def adapt(self, query: str) -> AdaptedQuery:
        """クエリを適応."""
        result = AdaptedQuery(original=query, expanded=query)

        # エンティティ抽出
        result.entities = self._extract_entities(query)

        # 同義語展開
        expanded_parts = []
        query_lower = query.lower()
        synonyms_used = {}

        for term, syns in self.synonyms.items():
            if term in query_lower:
                synonyms_used[term] = syns[:3]  # 上位3つ
                expanded_parts.append(f"({term} OR {' OR '.join(syns[:3])})")

        result.synonyms = synonyms_used

        # クエリ分解
        result.decomposed = self._decompose_query(query)

        # 拡張クエリ生成
        if expanded_parts:
            result.expanded = " AND ".join(expanded_parts)

        # 信頼度計算
        result.confidence = self._calculate_confidence(result)

        return result

    def _extract_entities(self, query: str) -> list[str]:
        """エンティティを抽出."""
        entities = []
        query_lower = query.lower()

        # 遺伝子シンボル
        gene_matches = re.findall(r"\b[A-Z][A-Z0-9]{1,5}\b", query)
        entities.extend(gene_matches)

        # 疾患名
        for disease in BIOMEDICAL_ENTITIES["diseases"]:
            if disease in query_lower:
                entities.append(disease)

        # 薬剤名
        for drug in BIOMEDICAL_ENTITIES["drugs"]:
            if drug in query_lower:
                entities.append(drug)

        return list(set(entities))

    def _decompose_query(self, query: str) -> list[str]:
        """クエリを部分クエリに分解."""
        # ANDで分割
        parts = re.split(r'\s+AND\s+', query, flags=re.IGNORECASE)
        if len(parts) > 1:
            return parts

        # カンマで分割
        parts = query.split(",")
        if len(parts) > 1:
            return [p.strip() for p in parts]

        # 長いクエリは意味単位で分解
        words = query.split()
        if len(words) > 5:
            mid = len(words) // 2
            return [" ".join(words[:mid]), " ".join(words[mid:])]

        return [query]

    def _calculate_confidence(self, result: AdaptedQuery) -> float:
        """信頼度を計算."""
        confidence = 0.5

        # エンティティ認識
        if result.entities:
            confidence += 0.2

        # 同義語マッチ
        if result.synonyms:
            confidence += 0.2

        # クエリ長さ
        if 3 <= len(result.original.split()) <= 10:
            confidence += 0.1

        return min(1.0, confidence)


def adapt_query(query: str, domain: str = "immuno_onco") -> AdaptedQuery:
    """便利関数: クエリを適応."""
    adapter = QueryAdapter(domain)
    return adapter.adapt(query)
