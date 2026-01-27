"""Paper Selector (P-03).

論文選抜ロジック。免疫/がん/抗体創薬向けの論文フィルタリング。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SelectionCriteria:
    """選抜基準."""

    min_year: int = 2015
    max_year: int = 2030
    require_abstract: bool = True
    min_abstract_length: int = 100
    domain_keywords: List[str] = field(default_factory=list)
    exclude_types: List[str] = field(default_factory=list)  # review, commentary等
    prefer_oa: bool = True

    @classmethod
    def for_immuno_onco(cls) -> "SelectionCriteria":
        """免疫腫瘍学向けデフォルト."""
        return cls(
            min_year=2015,
            domain_keywords=[
                "immunotherapy",
                "checkpoint",
                "pd-1",
                "pd-l1",
                "ctla-4",
                "car-t",
                "t cell",
                "nk cell",
                "tumor microenvironment",
                "adenosine",
                "cd73",
                "cd39",
                "a2a",
            ],
            exclude_types=["review", "meta-analysis", "commentary", "letter", "editorial"],
        )

    @classmethod
    def for_antibody_discovery(cls) -> "SelectionCriteria":
        """抗体創薬向けデフォルト."""
        return cls(
            min_year=2018,
            domain_keywords=[
                "antibody",
                "monoclonal",
                "bispecific",
                "adc",
                "adcc",
                "fc receptor",
                "binding affinity",
                "epitope",
                "humanization",
                "phage display",
                "hybridoma",
                "single domain",
            ],
            exclude_types=["review", "meta-analysis"],
        )


@dataclass
class SelectionResult:
    """選抜結果."""

    paper_id: str
    include: bool
    relevance_score: float
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "paper_id": self.paper_id,
            "include": self.include,
            "relevance_score": self.relevance_score,
            "reasons": self.reasons,
        }


@dataclass
class SelectionSummary:
    """選抜サマリ."""

    results: List[SelectionResult] = field(default_factory=list)
    included: int = 0
    excluded: int = 0

    def to_dict(self) -> dict:
        return {
            "results": [r.to_dict() for r in self.results],
            "included": self.included,
            "excluded": self.excluded,
        }


class PaperSelector:
    """論文選抜器.

    基準に基づいて論文を選抜。
    """

    def __init__(self, criteria: Optional[SelectionCriteria] = None):
        self.criteria = criteria or SelectionCriteria.for_immuno_onco()

    def select(self, papers: List[Dict[str, Any]]) -> SelectionSummary:
        """論文を選抜.

        Args:
            papers: 論文リスト

        Returns:
            SelectionSummary
        """
        summary = SelectionSummary()

        for paper in papers:
            result = self._evaluate_paper(paper)
            summary.results.append(result)

            if result.include:
                summary.included += 1
            else:
                summary.excluded += 1

        # 関連度スコアでソート
        summary.results.sort(key=lambda r: r.relevance_score, reverse=True)

        return summary

    def select_top_k(
        self,
        papers: List[Dict[str, Any]],
        k: int = 10,
    ) -> List[Dict[str, Any]]:
        """上位k件を選抜.

        Returns:
            選抜された論文リスト
        """
        summary = self.select(papers)

        # include=Trueの上位k件
        selected_ids = [r.paper_id for r in summary.results if r.include][:k]

        return [p for p in papers if p.get("paper_id") in selected_ids]

    def _evaluate_paper(self, paper: Dict[str, Any]) -> SelectionResult:
        """単一論文を評価."""
        paper_id = paper.get("paper_id", "")
        reasons = []
        score = 0.0
        include = True

        # 年フィルタ
        year = paper.get("year", 0)
        if year < self.criteria.min_year:
            reasons.append(f"年が古い: {year} < {self.criteria.min_year}")
            include = False
        elif year > self.criteria.max_year:
            reasons.append(f"年が新しすぎる: {year} > {self.criteria.max_year}")
            include = False
        else:
            # 新しいほど高スコア
            score += min(1.0, (year - self.criteria.min_year) / 10) * 0.2

        # アブストラクト必須
        abstract = paper.get("abstract", "")
        if self.criteria.require_abstract:
            if len(abstract) < self.criteria.min_abstract_length:
                reasons.append(f"アブストラクトが短い: {len(abstract)} chars")
                if include:
                    score -= 0.3

        # ドメインキーワードマッチ
        title = paper.get("title", "").lower()
        abstract_lower = abstract.lower()
        text = title + " " + abstract_lower

        keyword_matches = 0
        for kw in self.criteria.domain_keywords:
            if kw.lower() in text:
                keyword_matches += 1

        if self.criteria.domain_keywords:
            keyword_ratio = keyword_matches / len(self.criteria.domain_keywords)
            score += keyword_ratio * 0.5

            if keyword_matches == 0:
                reasons.append("ドメインキーワードなし")
                include = False
            else:
                reasons.append(f"キーワードマッチ: {keyword_matches}件")

        # 除外タイプ
        title_lower = title.lower()
        for exclude_type in self.criteria.exclude_types:
            if exclude_type.lower() in title_lower:
                reasons.append(f"除外タイプ: {exclude_type}")
                include = False
                break

        # OA優先
        if self.criteria.prefer_oa:
            is_oa = paper.get("is_oa", paper.get("open_access", False))
            if is_oa:
                score += 0.1
                reasons.append("OA論文")

        # スコアを0-10に正規化
        final_score = max(0, min(10, score * 10))

        if include:
            reasons.insert(0, "選抜")
        else:
            reasons.insert(0, "除外")

        return SelectionResult(
            paper_id=paper_id,
            include=include,
            relevance_score=final_score,
            reasons=reasons,
        )


def select_papers(
    papers: List[Dict[str, Any]],
    criteria: Optional[SelectionCriteria] = None,
) -> SelectionSummary:
    """便利関数: 論文を選抜."""
    selector = PaperSelector(criteria)
    return selector.select(papers)


def select_top_papers(
    papers: List[Dict[str, Any]],
    k: int = 10,
    domain: str = "immuno_onco",
) -> List[Dict[str, Any]]:
    """便利関数: 上位k件を選抜."""
    if domain == "immuno_onco":
        criteria = SelectionCriteria.for_immuno_onco()
    elif domain == "antibody":
        criteria = SelectionCriteria.for_antibody_discovery()
    else:
        criteria = SelectionCriteria()

    selector = PaperSelector(criteria)
    return selector.select_top_k(papers, k)
