"""
JARVIS Mandatory Similar Search

Phase2: 類似判断検索の強制化
- 新Issue処理時、Goldset検索を必須ステップにせよ
- Top-3 類似判断を必ず提示せよ
- 類似点・差分の記述を強制せよ
- 類似判断を無視した判断を禁止せよ
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from .decision import DecisionMaker, JudgmentDecision
from .evaluator_v2 import IntelligentEvaluator
from .goldset_index import GoldsetEntry, GoldsetIndex

logger = logging.getLogger(__name__)


@dataclass
class SimilarJudgment:
    """類似判断."""
    entry: GoldsetEntry
    similarity: float
    common_points: str  # 今回との共通点
    different_points: str = ""  # 今回との差分


@dataclass
class MandatorySearchResult:
    """類似判断検索結果（必須出力）."""
    query_context: str
    similar_judgments: list[SimilarJudgment]
    search_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def format_output(self) -> str:
        """固定フォーマットで出力.
        
        Phase2の出力フォーマット（固定）:
        【類似判断①】
        - Context:
        - Decision:
        - Outcome:
        - 今回との共通点:
        """
        lines = ["## 類似判断検索結果\n"]

        for i, sj in enumerate(self.similar_judgments, 1):
            lines.append(f"### 【類似判断{i}】（類似度: {sj.similarity:.2f}）")
            lines.append(f"- **Context**: {sj.entry.context}")
            lines.append(f"- **Decision**: {sj.entry.decision}")
            lines.append(f"- **Reason**: {sj.entry.reason}")
            lines.append(f"- **Outcome**: {sj.entry.outcome}")
            lines.append(f"- **今回との共通点**: {sj.common_points}")
            if sj.different_points:
                lines.append(f"- **今回との差分**: {sj.different_points}")
            lines.append("")

        return "\n".join(lines)


@dataclass
class Phase2Decision:
    """Phase2判断結果.
    
    類似判断との比較を含む。
    """
    issue_context: str
    similar_search: MandatorySearchResult
    decision: JudgmentDecision
    same_as_similar: str  # 類似判断と同じ点
    different_from_similar: str  # あえて違う点

    def format_full_output(self) -> str:
        """完全な出力を生成."""
        lines = [
            f"# 判断レポート: {self.issue_context[:50]}...\n",
            self.similar_search.format_output(),
            "---\n",
            "## 【今回の判断】",
            f"- **Decision**: {self.decision.status.value}",
            f"- **Reason**: {self.decision.decision_reason}",
            "",
            "### 類似判断と同じ点",
            self.same_as_similar,
            "",
            "### あえて違う点",
            self.different_from_similar,
        ]

        if self.decision.reject_reason:
            lines.append("")
            lines.append("### Reject理由")
            lines.append(f"- {self.decision.reject_reason.value}: {self.decision.reject_detail}")

        return "\n".join(lines)


class MandatorySearchJudge:
    """強制類似検索付き判断器.
    
    Phase2の核心:
    - 類似判断検索を必須ステップにせよ
    - 類似判断を無視した判断を禁止せよ
    """

    def __init__(
        self,
        goldset_index: GoldsetIndex | None = None,
        evaluator: IntelligentEvaluator | None = None,
        decision_maker: DecisionMaker | None = None
    ):
        """
        初期化.
        
        Args:
            goldset_index: GoldsetIndex
            evaluator: 5軸評価器
            decision_maker: 判断決定器
        """
        self.goldset_index = goldset_index or GoldsetIndex()
        self.evaluator = evaluator or IntelligentEvaluator()
        self.decision_maker = decision_maker or DecisionMaker()

    def judge(
        self,
        issue_id: str,
        issue_context: str,
        description: str = ""
    ) -> Phase2Decision:
        """
        類似判断検索付きで判断.
        
        ルール（核心）:
        1. Issue概要をembedding化
        2. goldset_indexからTop-3類似判断を取得
        3. それを人間に見せる
        4. その上でaccept/rejectを決める
        
        Args:
            issue_id: Issue ID
            issue_context: Issue概要
            description: 詳細説明
        
        Returns:
            Phase2Decision
        """
        # Step 1: 必須の類似判断検索
        search_result = self._mandatory_search(issue_context)

        # Step 2: 5軸評価
        scores = self.evaluator.evaluate(issue_context, description)

        # Step 3: 判断決定
        decision = self.decision_maker.decide(issue_id, issue_context, scores)

        # Step 4: 類似判断との比較を強制
        same_as, different_from = self._analyze_comparison(
            decision, search_result.similar_judgments
        )

        return Phase2Decision(
            issue_context=issue_context,
            similar_search=search_result,
            decision=decision,
            same_as_similar=same_as,
            different_from_similar=different_from,
        )

    def _mandatory_search(self, query: str) -> MandatorySearchResult:
        """必須の類似判断検索."""
        # Top-3検索
        results = self.goldset_index.search(query, top_k=3)

        similar_judgments = []
        for entry, similarity in results:
            # 共通点を自動生成（プレースホルダー）
            common = self._find_common_points(query, entry)

            similar_judgments.append(SimilarJudgment(
                entry=entry,
                similarity=similarity,
                common_points=common,
            ))

        return MandatorySearchResult(
            query_context=query,
            similar_judgments=similar_judgments,
        )

    def _find_common_points(self, query: str, entry: GoldsetEntry) -> str:
        """共通点を特定."""
        query_lower = query.lower()
        context_lower = entry.context.lower()

        # キーワード抽出（簡易）
        keywords = ["判断", "設計", "導入", "論文", "評価", "自動", "手動"]
        common = []
        for kw in keywords:
            if kw in query_lower and kw in context_lower:
                common.append(kw)

        if common:
            return f"共通キーワード: {', '.join(common)}"

        return "文脈の類似性から抽出"

    def _analyze_comparison(
        self,
        decision: JudgmentDecision,
        similar_judgments: list[SimilarJudgment]
    ) -> tuple[str, str]:
        """類似判断との比較を分析.
        
        「同じ判断をするか／あえて外すか」を言語化。
        """
        if not similar_judgments:
            return "類似判断なし", "新規の判断パターン"

        # 最も類似する判断と比較
        top_similar = similar_judgments[0]

        same_decision = decision.status.value == top_similar.entry.decision

        if same_decision:
            same_as = f"類似判断({top_similar.entry.decision})と同じ判断。理由: 文脈が類似"
            different_from = "なし（同じ判断を採用）"
        else:
            same_as = f"評価軸の一部は類似（{top_similar.common_points}）"
            different_from = (
                f"類似判断は{top_similar.entry.decision}だが、"
                f"今回は{decision.status.value}。"
                f"理由: {decision.decision_reason}"
            )

        return same_as, different_from
