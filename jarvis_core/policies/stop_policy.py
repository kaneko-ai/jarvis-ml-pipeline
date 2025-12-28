"""Stop Policy (R-02).

無理なら「不明」で停止し、次に必要な情報を提示する。

原則:
1. 根拠なしで断言しない
2. リトライ上限で停止
3. 停止時は「何が不明か」「次に何が必要か」を明示
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StopDecision:
    """停止判定結果."""
    should_stop: bool = False
    reason: str = ""
    unknown_aspects: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    partial_answer: str = ""
    confidence: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "should_stop": self.should_stop,
            "reason": self.reason,
            "unknown_aspects": self.unknown_aspects,
            "next_steps": self.next_steps,
            "partial_answer": self.partial_answer,
            "confidence": self.confidence,
        }
    
    def format_response(self) -> str:
        """ユーザー向けレスポンスをフォーマット."""
        lines = []
        
        if self.partial_answer:
            lines.append("## 部分的な回答")
            lines.append(self.partial_answer)
            lines.append("")
        
        if self.unknown_aspects:
            lines.append("## 不明な点")
            for aspect in self.unknown_aspects:
                lines.append(f"- {aspect}")
            lines.append("")
        
        if self.next_steps:
            lines.append("## 次に必要な情報/ステップ")
            for step in self.next_steps:
                lines.append(f"- {step}")
            lines.append("")
        
        lines.append(f"*信頼度: {self.confidence:.0%}*")
        lines.append(f"*停止理由: {self.reason}*")
        
        return "\n".join(lines)


class StopPolicy:
    """停止ポリシー.
    
    以下の条件で停止を判定:
    1. 根拠なしで断言しようとしている
    2. リトライ上限に達した
    3. 致命的なエラーが発生した
    4. 品質ゲートを満たせない
    """
    
    # 停止条件の閾値
    DEFAULT_THRESHOLDS = {
        "min_evidence_count": 1,
        "min_confidence": 0.3,
        "max_retries": 3,
        "max_assertion_without_evidence": 0,
    }
    
    def __init__(
        self,
        thresholds: Optional[Dict[str, Any]] = None,
        refuse_if_no_evidence: bool = True,
    ):
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}
        self.refuse_if_no_evidence = refuse_if_no_evidence
    
    def evaluate(
        self,
        evidence_count: int,
        assertions_without_evidence: int,
        retry_count: int,
        confidence: float,
        has_fatal_error: bool = False,
        error_message: str = "",
        partial_answer: str = "",
    ) -> StopDecision:
        """停止すべきか評価.
        
        Args:
            evidence_count: 抽出された根拠の数
            assertions_without_evidence: 根拠なし断言の数
            retry_count: 現在のリトライ回数
            confidence: 全体の信頼度
            has_fatal_error: 致命的エラーがあるか
            error_message: エラーメッセージ
            partial_answer: 部分的な回答
            
        Returns:
            StopDecision
        """
        decision = StopDecision(
            partial_answer=partial_answer,
            confidence=confidence,
        )
        
        # 条件1: 致命的エラー
        if has_fatal_error:
            decision.should_stop = True
            decision.reason = "致命的なエラーが発生しました"
            decision.unknown_aspects.append(f"エラー: {error_message}")
            decision.next_steps.append("システム管理者に連絡してください")
            return decision
        
        # 条件2: 根拠不足
        if self.refuse_if_no_evidence and evidence_count < self.thresholds["min_evidence_count"]:
            decision.should_stop = True
            decision.reason = "十分な根拠が見つかりませんでした"
            decision.unknown_aspects.append("この質問に対する信頼できる根拠が不足しています")
            decision.next_steps.extend([
                "検索クエリを変更して再試行してください",
                "より具体的な質問に分解してください",
                "追加の論文/資料を投入してください",
            ])
            return decision
        
        # 条件3: 根拠なし断言
        if assertions_without_evidence > self.thresholds["max_assertion_without_evidence"]:
            decision.should_stop = True
            decision.reason = "根拠なしの断言を避けるため停止しました"
            decision.unknown_aspects.append(f"{assertions_without_evidence}件の主張に根拠がありません")
            decision.next_steps.extend([
                "根拠付きの主張のみで回答を再構成してください",
                "不確実な点は「〜の可能性がある」等の表現を使用してください",
            ])
            return decision
        
        # 条件4: リトライ上限
        if retry_count >= self.thresholds["max_retries"]:
            decision.should_stop = True
            decision.reason = f"リトライ上限（{self.thresholds['max_retries']}回）に達しました"
            decision.unknown_aspects.append("複数回の試行でも十分な品質に達しませんでした")
            decision.next_steps.extend([
                "質問の範囲を狭めてください",
                "異なるアプローチで再試行してください",
            ])
            return decision
        
        # 条件5: 信頼度不足
        if confidence < self.thresholds["min_confidence"]:
            decision.should_stop = True
            decision.reason = f"信頼度が閾値（{self.thresholds['min_confidence']:.0%}）を下回りました"
            decision.unknown_aspects.append("回答の信頼性が十分ではありません")
            decision.next_steps.extend([
                "追加の根拠を探してください",
                "専門家に確認してください",
            ])
            return decision
        
        # 停止不要
        decision.should_stop = False
        return decision
    
    def format_refuse_response(
        self,
        decision: StopDecision,
        original_query: str,
    ) -> str:
        """拒否レスポンスをフォーマット."""
        lines = [
            "# ⚠️ 回答を保留します",
            "",
            f"**クエリ:** {original_query}",
            "",
            "---",
            "",
        ]
        
        lines.append(decision.format_response())
        
        return "\n".join(lines)
