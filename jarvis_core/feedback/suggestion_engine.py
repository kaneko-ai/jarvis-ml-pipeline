"""Suggestion engine for feedback risk mitigation."""
from __future__ import annotations

from .schema import FeedbackEntry


class SuggestionEngine:
    """Generate before/after suggestions for high-risk segments."""

    def __init__(self, history: list[FeedbackEntry]):
        self.history = history

    def suggest(self, text: str, categories: list[str]) -> list[dict[str, str]]:
        suggestions: list[dict[str, str]] = []
        for category in categories:
            suggestions.extend(self._category_suggestions(text, category))
        return suggestions[:3]

    def _category_suggestions(self, text: str, category: str) -> list[dict[str, str]]:
        templates = {
            "evidence": [
                {
                    "after": f"{text} 具体的な根拠（例: 引用やデータ）を1点追記する。",
                    "why": "根拠を明示すると指摘されにくくなる",
                    "tradeoff": "情報量が増え、文章が長くなる",
                },
                {
                    "after": f"{text} （推測です）に加えて出典を示す。",
                    "why": "推測の明示と出典提示でリスクを下げる",
                    "tradeoff": "断定感が弱まる",
                },
            ],
            "terminology": [
                {
                    "after": f"{text} 用語を定義し、括弧で意味を補足する。",
                    "why": "用語揺れの指摘を避ける",
                    "tradeoff": "冗長になる",
                },
                {
                    "after": f"{text} 使用する専門用語を統一する。",
                    "why": "用語の一貫性を担保する",
                    "tradeoff": "推敲が必要",
                },
            ],
            "logic": [
                {
                    "after": f"{text} その結論に至る理由を1文追加する。",
                    "why": "論理の飛躍を防ぐ",
                    "tradeoff": "文章が長くなる",
                },
                {
                    "after": f"{text} 反例の可能性を一言添える（推測です）。",
                    "why": "論理の抜けを補強できる",
                    "tradeoff": "断定性が下がる",
                },
            ],
            "expression": [
                {
                    "after": f"{text} 曖昧語を具体的な数値や条件に置換する。",
                    "why": "表現の曖昧さを減らす",
                    "tradeoff": "追加調査が必要",
                },
                {
                    "after": f"{text} （推測です）を明示する。",
                    "why": "断定表現の指摘を回避",
                    "tradeoff": "説得力が下がる",
                },
            ],
            "figure": [
                {
                    "after": f"{text} 図表番号と根拠を補足する。",
                    "why": "図表の説明不足を減らす",
                    "tradeoff": "説明が増える",
                }
            ],
            "conclusion": [
                {
                    "after": f"{text} 結論の範囲と前提条件を明示する。",
                    "why": "結論の飛躍を抑える",
                    "tradeoff": "慎重な表現になる",
                }
            ],
            "format": [
                {
                    "after": f"{text} 規定フォーマットに合わせて体裁を整える。",
                    "why": "形式上の指摘を回避",
                    "tradeoff": "編集工数が増える",
                }
            ],
        }
        suggestions = []
        for template in templates.get(category, []):
            suggestions.append({
                "before": text,
                "after": template["after"],
                "why": template["why"],
                "tradeoff": template["tradeoff"],
            })
        return suggestions
