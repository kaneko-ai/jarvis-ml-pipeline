"""
JARVIS Claim Extractor

3. LLM Claim抽出: Gemini/GPTで主張・根拠を自動抽出
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ExtractedClaim:
    """抽出された主張."""

    claim_id: str
    claim_text: str
    claim_type: str  # finding, method, hypothesis, conclusion
    confidence: float
    source_text: str
    source_location: dict[str, Any]  # section, paragraph, sentence
    evidence_refs: list[str]


class ClaimExtractor:
    """LLM Claim抽出器.

    Gemini/GPT/ローカルLLMを使用して主張を抽出
    """

    CLAIM_TYPES = ["finding", "method", "hypothesis", "conclusion"]

    EXTRACTION_PROMPT = """
以下のテキストから、科学的主張（Claims）を抽出してください。

各主張について以下を特定してください：
1. 主張の内容（claim_text）
2. 主張の種類（finding/method/hypothesis/conclusion）
3. 確信度（0.0-1.0）
4. 根拠となる文（evidence）

テキスト:
{text}

JSON形式で出力してください：
[
  {{"claim_text": "...", "claim_type": "finding", "confidence": 0.8, "evidence": "..."}}
]
"""

    def __init__(self, llm_client=None):
        """初期化."""
        self.llm_client = llm_client

    def extract_claims(
        self,
        text: str,
        source_id: str = "",
        section: str = "",
    ) -> list[ExtractedClaim]:
        """テキストから主張を抽出.

        Args:
            text: 入力テキスト
            source_id: ソースID
            section: セクション名

        Returns:
            抽出された主張リスト
        """
        if self.llm_client:
            return self._extract_with_llm(text, source_id, section)
        else:
            return self._extract_rule_based(text, source_id, section)

    def _extract_with_llm(
        self,
        text: str,
        source_id: str,
        section: str,
    ) -> list[ExtractedClaim]:
        """LLMで抽出."""
        prompt = self.EXTRACTION_PROMPT.format(text=text[:2000])

        try:
            response = self.llm_client.generate(prompt)
            claims_data = self._parse_llm_response(response)

            claims = []
            for i, data in enumerate(claims_data):
                claims.append(
                    ExtractedClaim(
                        claim_id=f"{source_id}_c{i:03d}",
                        claim_text=data.get("claim_text", ""),
                        claim_type=data.get("claim_type", "finding"),
                        confidence=data.get("confidence", 0.5),
                        source_text=data.get("evidence", ""),
                        source_location={"section": section},
                        evidence_refs=[],
                    )
                )

            return claims

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return self._extract_rule_based(text, source_id, section)

    def _parse_llm_response(self, response: str) -> list[dict]:
        """LLMレスポンスをパース."""
        import json

        # JSON部分を抽出
        match = re.search(r"\[.*\]", response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to decode JSON from LLM response: {e}")

        return []

    def _extract_rule_based(
        self,
        text: str,
        source_id: str,
        section: str,
    ) -> list[ExtractedClaim]:
        """ルールベースで抽出."""
        claims = []

        # 文に分割
        sentences = re.split(r"(?<=[.!?])\s+", text)

        # 主張パターン
        claim_patterns = [
            (r"(?i)(we found|we observed|we demonstrated|our results show)", "finding"),
            (r"(?i)(we hypothesized|we propose|we suggest)", "hypothesis"),
            (r"(?i)(we conclude|in conclusion|these findings suggest)", "conclusion"),
            (r"(?i)(we used|we performed|we analyzed)", "method"),
        ]

        claim_count = 0
        for sentence in sentences:
            for pattern, claim_type in claim_patterns:
                if re.search(pattern, sentence):
                    claims.append(
                        ExtractedClaim(
                            claim_id=f"{source_id}_c{claim_count:03d}",
                            claim_text=sentence.strip(),
                            claim_type=claim_type,
                            confidence=0.6,
                            source_text=sentence.strip(),
                            source_location={"section": section},
                            evidence_refs=[],
                        )
                    )
                    claim_count += 1
                    break

        logger.info(f"Extracted {len(claims)} claims (rule-based)")
        return claims