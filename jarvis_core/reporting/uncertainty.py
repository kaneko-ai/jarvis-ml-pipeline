"""Uncertainty Determination Logic (Phase 2-ΩΩ).

Implements mechanical rules for determining uncertainty labels
based on evidence strength and contradictions.
"""

from typing import Literal

UncertaintyLabel = Literal["確定", "高信頼", "要注意", "推測"]
SupportLevel = Literal["Strong", "Medium", "Weak", "None"]


def determine_uncertainty(
    support_level: SupportLevel, has_contradiction: bool = False
) -> UncertaintyLabel:
    """Determine uncertainty label based on support and contradictions.

    Rules (strict, no exceptions):
    - Strong + no contradiction → 確定
    - Strong + contradiction → 高信頼 (降格)
    - Medium + no contradiction → 高信頼
    - Medium + contradiction → 要注意 (降格)
    - Weak → 要注意
    - None → 推測

    Args:
        support_level: Evidence support level
        has_contradiction: Whether contradicting evidence exists

    Returns:
        Uncertainty label
    """
    if support_level == "Strong":
        return "高信頼" if has_contradiction else "確定"
    elif support_level == "Medium":
        return "要注意" if has_contradiction else "高信頼"
    elif support_level == "Weak":
        return "要注意"
    else:  # None
        return "推測"


def get_allowed_language(uncertainty: UncertaintyLabel) -> dict[str, list[str]]:
    """Get allowed/forbidden language patterns for each uncertainty level.

    Returns:
        Dict with 'allowed' and 'forbidden' language patterns
    """
    rules = {
        "確定": {
            "allowed": ["である", "示す", "確認された"],
            "forbidden": ["可能性", "推測", "おそらく"],
        },
        "高信頼": {
            "allowed": ["可能性が高い", "示唆される", "考えられる"],
            "forbidden": ["である（断定）", "証明された"],
        },
        "要注意": {
            "allowed": ["可能性", "示唆", "限定的に"],
            "forbidden": ["確実", "明らか", "証明"],
        },
        "推測": {
            "allowed": ["推測", "不明", "データ不足"],
            "forbidden": ["である（断定）", "確実", "明らか", "証明"],
        },
    }

    return rules.get(uncertainty, rules["推測"])


def format_conclusion_text(base_text: str, uncertainty: UncertaintyLabel) -> str:
    """Format conclusion text with appropriate hedging based on uncertainty.

    Args:
        base_text: Original conclusion text
        uncertainty: Uncertainty label

    Returns:
        Formatted text with appropriate hedging
    """
    if uncertainty == "確定":
        # No hedging needed
        return base_text
    elif uncertainty == "高信頼":
        # Add moderate hedging
        if not any(word in base_text for word in ["可能性", "示唆", "考えられる"]):
            return f"{base_text}と考えられる"
        return base_text
    elif uncertainty == "要注意":
        # Add strong hedging
        if not any(word in base_text for word in ["可能性", "限定的"]):
            return f"{base_text}可能性がある（限定的な根拠）"
        return base_text
    else:  # 推測
        # Replace with uncertainty template
        return f"根拠不足のため、{base_text}かどうかは不明"