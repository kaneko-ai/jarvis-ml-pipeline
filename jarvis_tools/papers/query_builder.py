"""Search Composer (P-02).

PubMed検索クエリを最適化して生成。
- MeSH用語の追加
- 同義語の展開
- フィルタの適用
- 理由付きの検索式
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ドメイン別の同義語辞書（免疫・がん・抗体創薬向け）
DOMAIN_SYNONYMS: Dict[str, Dict[str, List[str]]] = {
    "immuno_onco_preclinical": {
        "cd73": ["nt5e", "ecto-5'-nucleotidase", "5'-nucleotidase"],
        "cd39": ["entpd1", "ectonucleoside triphosphate diphosphohydrolase-1"],
        "adenosine": ["ado", "adenosine signaling"],
        "a2a": ["a2ar", "adora2a", "adenosine a2a receptor"],
        "pd-1": ["pdcd1", "cd279", "programmed cell death 1"],
        "pd-l1": ["cd274", "b7-h1", "programmed death-ligand 1"],
        "ctla-4": ["cd152", "cytotoxic t-lymphocyte antigen-4"],
        "tumor microenvironment": ["tme", "tumor immune microenvironment"],
        "t cell": ["t lymphocyte", "t-cell", "t-lymphocyte"],
        "nk cell": ["natural killer cell", "nk-cell"],
        "macrophage": ["tam", "tumor-associated macrophage"],
        "immunotherapy": ["immuno-oncology", "cancer immunotherapy"],
        "checkpoint": ["immune checkpoint", "checkpoint inhibitor", "ici"],
        "antibody": ["mab", "monoclonal antibody"],
        "adcc": ["antibody-dependent cellular cytotoxicity"],
        "adc": ["antibody-drug conjugate"],
    }
}

# MeSH用語マッピング（簡易版）
MESH_TERMS: Dict[str, str] = {
    "cd73": "5'-Nucleotidase[MeSH]",
    "adenosine": "Adenosine[MeSH]",
    "immunotherapy": "Immunotherapy[MeSH]",
    "cancer": "Neoplasms[MeSH]",
    "t cell": "T-Lymphocytes[MeSH]",
    "antibody": "Antibodies, Monoclonal[MeSH]",
    "tumor": "Neoplasms[MeSH]",
    "checkpoint": "Immune Checkpoint Proteins[MeSH]",
}


@dataclass
class SearchQuery:
    """構造化された検索クエリ."""
    pubmed_query: str
    mesh_terms: List[str] = field(default_factory=list)
    synonyms_used: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    original_query: str = ""

    def to_dict(self) -> dict:
        return {
            "pubmed_query": self.pubmed_query,
            "mesh_terms": self.mesh_terms,
            "synonyms_used": self.synonyms_used,
            "filters": self.filters,
            "reasoning": self.reasoning,
            "original_query": self.original_query,
        }


class SearchComposer:
    """検索クエリ生成器.
    
    ユーザークエリをPubMed最適化クエリに変換。
    """

    def __init__(
        self,
        domain: str = "immuno_onco_preclinical",
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        oa_only: bool = False,
    ):
        self.domain = domain
        self.year_from = year_from
        self.year_to = year_to
        self.oa_only = oa_only
        self.synonyms = DOMAIN_SYNONYMS.get(domain, {})

    def compose(self, query: str) -> SearchQuery:
        """クエリを最適化.
        
        Args:
            query: ユーザーの自然言語クエリ
            
        Returns:
            SearchQuery: 最適化された検索クエリ
        """
        # 1. クエリからキーワードを抽出
        keywords = self._extract_keywords(query)

        # 2. MeSH用語を追加
        mesh_terms = self._add_mesh_terms(keywords)

        # 3. 同義語を展開
        expanded = self._expand_synonyms(keywords)

        # 4. PubMedクエリを構築
        pubmed_query, synonyms_used = self._build_pubmed_query(keywords, expanded, mesh_terms)

        # 5. フィルタを適用
        filters = self._apply_filters()
        if filters:
            pubmed_query = f"({pubmed_query}) AND {self._filters_to_query(filters)}"

        # 6. 理由を生成
        reasoning = self._generate_reasoning(keywords, mesh_terms, synonyms_used, filters)

        return SearchQuery(
            pubmed_query=pubmed_query,
            mesh_terms=mesh_terms,
            synonyms_used=synonyms_used,
            filters=filters,
            reasoning=reasoning,
            original_query=query,
        )

    def _extract_keywords(self, query: str) -> List[str]:
        """クエリからキーワードを抽出."""
        # 小文字化
        query_lower = query.lower()

        # 簡易的なキーワード抽出
        words = re.findall(r'\b[a-z][a-z0-9-]+\b', query_lower)

        # ストップワード除去
        stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'this', 'that', 'these', 'those', 'which', 'what', 'when',
            'where', 'why', 'how', 'and', 'or', 'but', 'if', 'for',
            'with', 'by', 'from', 'to', 'of', 'in', 'on', 'at', 'as',
        }

        keywords = [w for w in words if w not in stopwords and len(w) > 2]

        # 複合語も検出（例: "tumor microenvironment"）
        for compound in ["tumor microenvironment", "t cell", "nk cell", "pd-1", "pd-l1"]:
            if compound in query_lower:
                keywords.append(compound)

        return list(set(keywords))

    def _add_mesh_terms(self, keywords: List[str]) -> List[str]:
        """MeSH用語を追加."""
        mesh_terms = []
        for kw in keywords:
            if kw in MESH_TERMS:
                mesh_terms.append(MESH_TERMS[kw])
        return mesh_terms

    def _expand_synonyms(self, keywords: List[str]) -> Dict[str, List[str]]:
        """同義語を展開."""
        expanded = {}
        for kw in keywords:
            if kw in self.synonyms:
                expanded[kw] = self.synonyms[kw]
        return expanded

    def _build_pubmed_query(
        self,
        keywords: List[str],
        expanded: Dict[str, List[str]],
        mesh_terms: List[str],
    ) -> tuple[str, List[str]]:
        """PubMedクエリを構築."""
        parts = []
        synonyms_used = []

        for kw in keywords:
            if kw in expanded:
                # 同義語付きで OR 結合
                all_terms = [kw] + expanded[kw]
                synonyms_used.extend(expanded[kw])
                term_part = " OR ".join(f'"{t}"' for t in all_terms)
                parts.append(f"({term_part})")
            else:
                parts.append(f'"{kw}"')

        # MeSH用語を追加
        for mesh in mesh_terms:
            parts.append(mesh)

        # AND で結合
        query = " AND ".join(parts)

        return query, synonyms_used

    def _apply_filters(self) -> Dict[str, Any]:
        """フィルタを適用."""
        filters = {}

        if self.year_from or self.year_to:
            filters["year"] = {
                "from": self.year_from,
                "to": self.year_to,
            }

        if self.oa_only:
            filters["oa_only"] = True

        return filters

    def _filters_to_query(self, filters: Dict[str, Any]) -> str:
        """フィルタをPubMedクエリに変換."""
        parts = []

        if "year" in filters:
            year_from = filters["year"].get("from", 1900)
            year_to = filters["year"].get("to", 2099)
            parts.append(f"({year_from}:{year_to}[pdat])")

        if filters.get("oa_only"):
            parts.append("(free full text[filter])")

        return " AND ".join(parts)

    def _generate_reasoning(
        self,
        keywords: List[str],
        mesh_terms: List[str],
        synonyms_used: List[str],
        filters: Dict[str, Any],
    ) -> str:
        """検索戦略の理由を生成."""
        lines = []

        lines.append(f"抽出キーワード: {', '.join(keywords)}")

        if mesh_terms:
            lines.append(f"MeSH用語追加: {', '.join(mesh_terms)}")

        if synonyms_used:
            lines.append(f"同義語展開: {', '.join(synonyms_used[:5])}...")

        if filters:
            filter_desc = []
            if "year" in filters:
                y = filters["year"]
                filter_desc.append(f"年: {y.get('from', '?')}-{y.get('to', '?')}")
            if filters.get("oa_only"):
                filter_desc.append("OAのみ")
            lines.append(f"フィルタ: {', '.join(filter_desc)}")

        return "\n".join(lines)


def compose_search(
    query: str,
    domain: str = "immuno_onco_preclinical",
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    oa_only: bool = False,
) -> SearchQuery:
    """便利関数: 検索クエリを生成."""
    composer = SearchComposer(
        domain=domain,
        year_from=year_from,
        year_to=year_to,
        oa_only=oa_only,
    )
    return composer.compose(query)
