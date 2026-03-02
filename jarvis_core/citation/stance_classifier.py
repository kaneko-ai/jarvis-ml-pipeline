"""Citation Stance Classifier (B-1).

Classifies the relationship between two papers as:
  - support: Paper B supports/confirms Paper A's findings
  - contrast: Paper B contradicts/challenges Paper A's findings
  - neutral: No clear support or contradiction
  - mention: Simple citation without clear stance

Uses Gemini API for semantic classification, with a keyword-based fallback.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CitationStance(str, Enum):
    """Stance categories.

    MENTION and CONTRAST are required by citation/graph.py.
    """
    SUPPORT = "support"
    CONTRAST = "contrast"
    CONTRADICT = "contradict"
    NEUTRAL = "neutral"
    MENTION = "mention"


@dataclass
class StanceResult:
    """Result of stance classification for a paper pair."""
    paper_a_title: str
    paper_b_title: str
    stance: CitationStance
    confidence: float
    reason: str


class StanceClassifier:
    """Classifies citation stance between paper pairs.

    Uses LLM (Gemini) when available, falls back to keyword heuristics.
    """

    def __init__(self, use_llm: bool = True, provider: str = "gemini"):
        self.use_llm = use_llm
        self.provider = provider
        self._llm = None

    def _get_llm(self):
        """Lazy-init LLM client."""
        if self._llm is None and self.use_llm:
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except ImportError:
                pass
            try:
                from jarvis_core.llm import LLMClient
                self._llm = LLMClient(provider=self.provider)
            except Exception as e:
                logger.warning(f"LLM init failed: {e}. Using keyword fallback.")
                self.use_llm = False
        return self._llm

    def classify(self, paper_a: dict, paper_b: dict) -> StanceResult:
        """Classify stance between two papers.

        Args:
            paper_a: First paper dict (needs 'title' and 'abstract')
            paper_b: Second paper dict (needs 'title' and 'abstract')

        Returns:
            StanceResult with stance, confidence, and reason.
        """
        title_a = paper_a.get("title", "")
        title_b = paper_b.get("title", "")
        abstract_a = paper_a.get("abstract", "")
        abstract_b = paper_b.get("abstract", "")

        if self.use_llm:
            llm = self._get_llm()
            if llm:
                return self._classify_llm(llm, title_a, abstract_a, title_b, abstract_b)

        return self._classify_keywords(title_a, abstract_a, title_b, abstract_b)

    def _classify_llm(self, llm, title_a, abstract_a, title_b, abstract_b) -> StanceResult:
        """Classify using LLM."""
        from jarvis_core.llm import Message

        system_prompt = (
            "You are a scientific literature analysis expert.\n"
            "Given two paper abstracts, classify their relationship as:\n"
            "- support: Paper B supports or confirms Paper A's findings\n"
            "- contrast: Paper B contradicts or challenges Paper A's findings\n"
            "- neutral: No clear relationship between findings\n\n"
            "Output ONLY a JSON object:\n"
            '{"stance": "support|contrast|neutral", "confidence": 0.0-1.0, "reason": "brief explanation"}'
        )

        user_prompt = (
            f"Paper A: {title_a}\n{abstract_a[:500]}\n\n"
            f"Paper B: {title_b}\n{abstract_b[:500]}"
        )

        try:
            raw = llm.chat([
                Message(role="system", content=system_prompt),
                Message(role="user", content=user_prompt),
            ])
            raw_clean = raw.strip()
            if raw_clean.startswith("```"):
                raw_clean = re.sub(r"^```(?:json)?\s*", "", raw_clean)
                raw_clean = re.sub(r"\s*```$", "", raw_clean)

            parsed = json.loads(raw_clean)
            stance_str = parsed.get("stance", "neutral").lower()

            stance_map = {
                "support": CitationStance.SUPPORT,
                "contrast": CitationStance.CONTRAST,
                "contradict": CitationStance.CONTRAST,
                "neutral": CitationStance.NEUTRAL,
            }
            stance = stance_map.get(stance_str, CitationStance.NEUTRAL)

            return StanceResult(
                paper_a_title=title_a,
                paper_b_title=title_b,
                stance=stance,
                confidence=float(parsed.get("confidence", 0.5)),
                reason=parsed.get("reason", "LLM classification"),
            )
        except Exception as e:
            logger.warning(f"LLM stance classification failed: {e}")
            return self._classify_keywords(title_a, abstract_a, title_b, abstract_b)

    def _classify_keywords(self, title_a, abstract_a, title_b, abstract_b) -> StanceResult:
        """Fallback keyword-based classification."""
        text_a = (title_a + " " + abstract_a).lower()
        text_b = (title_b + " " + abstract_b).lower()

        # Check if they discuss similar topics (word overlap)
        words_a = set(text_a.split())
        words_b = set(text_b.split())
        overlap = len(words_a & words_b)
        union = len(words_a | words_b)
        similarity = overlap / max(union, 1)

        if similarity < 0.1:
            return StanceResult(
                paper_a_title=title_a, paper_b_title=title_b,
                stance=CitationStance.NEUTRAL, confidence=0.3,
                reason="Low topic overlap",
            )

        contradict_words = [
            "however", "contrary", "contradict", "disagree", "inconsistent",
            "failed to", "no effect", "no significant", "ineffective",
            "challenge", "refute", "oppose", "conflicting",
        ]
        support_words = [
            "consistent with", "in agreement", "confirms", "supports",
            "corroborates", "in line with", "similar to", "aligns with",
            "validates", "reinforces",
        ]

        contra_score = sum(1 for w in contradict_words if w in text_b)
        support_score = sum(1 for w in support_words if w in text_b)

        if contra_score > support_score and contra_score > 0:
            return StanceResult(
                paper_a_title=title_a, paper_b_title=title_b,
                stance=CitationStance.CONTRAST,
                confidence=min(0.6, 0.3 + contra_score * 0.1),
                reason=f"Keyword match: {contra_score} contradiction indicators",
            )
        elif support_score > contra_score and support_score > 0:
            return StanceResult(
                paper_a_title=title_a, paper_b_title=title_b,
                stance=CitationStance.SUPPORT,
                confidence=min(0.6, 0.3 + support_score * 0.1),
                reason=f"Keyword match: {support_score} support indicators",
            )

        return StanceResult(
            paper_a_title=title_a, paper_b_title=title_b,
            stance=CitationStance.NEUTRAL, confidence=0.3,
            reason="No clear stance indicators found",
        )


def classify_citation_stance(paper_a: dict, paper_b: dict, use_llm: bool = True) -> StanceResult:
    """Convenience function to classify stance between two papers."""
    classifier = StanceClassifier(use_llm=use_llm)
    return classifier.classify(paper_a, paper_b)
