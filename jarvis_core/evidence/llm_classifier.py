"""LLM-Based Evidence Classifier.

Uses LLM prompting to classify evidence levels.
Per JARVIS_COMPLETION_PLAN_v3 Task 2.1 LLM Classifier
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from jarvis_core.evidence.schema import (
    EvidenceGrade,
    EvidenceLevel,
    PICOExtraction,
    StudyType,
)

logger = logging.getLogger(__name__)


# Prompt template for evidence classification
CLASSIFICATION_PROMPT = """あなたは医学文献の研究デザインを分類する専門家です。

以下の論文を分析し、研究タイプと証拠レベルを判定してください。

# タイトル
{title}

# 抄録
{abstract}

# 指示
1. 研究タイプを特定してください（RCT、コホート研究、症例対照研究など）
2. Oxford CEBMの証拠レベル（1a, 1b, 2a, 2b, 3a, 3b, 4, 5）を判定してください
3. 判断の信頼度（0-100%）を示してください

# 出力形式（JSON）
{{
  "study_type": "研究タイプ",
  "evidence_level": "1a/1b/2a/2b/3a/3b/4/5",
  "confidence": 0-100,
  "reasoning": "判断理由"
}}

JSONのみを出力してください。"""


PICO_EXTRACTION_PROMPT = """以下の論文抄録からPICO要素を抽出してください。

# 抄録
{abstract}

# 指示
以下のPICO要素を抽出してください：
- P (Population): 対象集団・患者群
- I (Intervention): 介入・治療
- C (Comparator): 比較対照
- O (Outcome): 主要アウトカム

# 出力形式（JSON）
{{
  "population": "対象集団の説明",
  "intervention": "介入の説明",
  "comparator": "比較対照の説明",
  "outcome": "主要アウトカムの説明"
}}

JSONのみを出力してください。"""


@dataclass
class LLMConfig:
    """Configuration for LLM classifier."""

    model: str = "llama3.2"
    temperature: float = 0.1
    max_tokens: int = 500


class LLMBasedClassifier:
    """LLM-based evidence classifier.

    Uses local LLM to classify evidence levels based on paper content.
    Falls back to rule-based classification if LLM is unavailable.

    Example:
        >>> classifier = LLMBasedClassifier()
        >>> grade = classifier.classify(
        ...     title="A randomized controlled trial...",
        ...     abstract="Methods: We conducted a double-blind RCT..."
        ... )
        >>> print(grade.level)
        EvidenceLevel.LEVEL_1B
    """

    def __init__(self, config: LLMConfig | None = None):
        """Initialize the classifier.

        Args:
            config: LLM configuration
        """
        self._config = config or LLMConfig()
        self._llm = None
        self._initialized = False

    def _initialize(self) -> bool:
        """Initialize LLM connection."""
        if self._initialized:
            return self._llm is not None

        try:
            from jarvis_core.llm.ollama_adapter import OllamaBackend

            self._llm = OllamaBackend(model=self._config.model)
            self._initialized = True
            logger.info(f"LLM classifier initialized with model: {self._config.model}")
            return True

        except ImportError:
            logger.warning("Ollama backend not available for LLM classification")
            self._initialized = True
            return False
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self._initialized = True
            return False

    def classify(
        self,
        title: str = "",
        abstract: str = "",
        full_text: str = "",
    ) -> EvidenceGrade:
        """Classify evidence level using LLM.

        Args:
            title: Paper title
            abstract: Paper abstract
            full_text: Full paper text (optional, not used for cost reasons)

        Returns:
            EvidenceGrade with classification result
        """
        if not self._initialize():
            # Fallback to unknown if LLM not available
            return EvidenceGrade(
                level=EvidenceLevel.UNKNOWN,
                study_type=StudyType.UNKNOWN,
                confidence=0.0,
                classifier_source="llm_unavailable",
            )

        if not title and not abstract:
            return EvidenceGrade.unknown()

        # Build prompt
        prompt = CLASSIFICATION_PROMPT.format(
            title=title or "（タイトルなし）",
            abstract=abstract or "（抄録なし）",
        )

        try:
            # Call LLM
            response = self._llm.generate(
                prompt,
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
            )

            # Parse response
            return self._parse_response(response)

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return EvidenceGrade(
                level=EvidenceLevel.UNKNOWN,
                study_type=StudyType.UNKNOWN,
                confidence=0.0,
                classifier_source="llm_error",
            )

    def _parse_response(self, response: str) -> EvidenceGrade:
        """Parse LLM response into EvidenceGrade."""
        try:
            # Try to extract JSON from response
            json_match = self._extract_json(response)
            if not json_match:
                logger.warning("No JSON found in LLM response")
                return EvidenceGrade.unknown()

            data = json.loads(json_match)

            # Parse evidence level
            level_str = str(data.get("evidence_level", "unknown")).lower()
            level = self._parse_evidence_level(level_str)

            # Parse study type
            study_type_str = str(data.get("study_type", "unknown")).lower()
            study_type = self._parse_study_type(study_type_str)

            # Parse confidence
            confidence = float(data.get("confidence", 0)) / 100.0
            confidence = max(0.0, min(1.0, confidence))

            return EvidenceGrade(
                level=level,
                study_type=study_type,
                confidence=confidence,
                classifier_source="llm",
                quality_notes=[data.get("reasoning", "")] if data.get("reasoning") else [],
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return EvidenceGrade.unknown()
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return EvidenceGrade.unknown()

    def _extract_json(self, text: str) -> str | None:
        """Extract JSON object from text."""
        import re

        # Try to find JSON object
        patterns = [
            re.compile(r"\{[^{}]*\}", re.DOTALL),
            re.compile(r"```json\s*(\{[^{}]*\})\s*```", re.DOTALL),
        ]

        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return match.group(1) if match.lastindex else match.group(0)

        return None

    def _parse_evidence_level(self, level_str: str) -> EvidenceLevel:
        """Parse evidence level string."""
        level_map = {
            "1a": EvidenceLevel.LEVEL_1A,
            "1b": EvidenceLevel.LEVEL_1B,
            "1c": EvidenceLevel.LEVEL_1C,
            "2a": EvidenceLevel.LEVEL_2A,
            "2b": EvidenceLevel.LEVEL_2B,
            "2c": EvidenceLevel.LEVEL_2C,
            "3a": EvidenceLevel.LEVEL_3A,
            "3b": EvidenceLevel.LEVEL_3B,
            "4": EvidenceLevel.LEVEL_4,
            "5": EvidenceLevel.LEVEL_5,
        }
        return level_map.get(level_str.strip(), EvidenceLevel.UNKNOWN)

    def _parse_study_type(self, type_str: str) -> StudyType:
        """Parse study type string."""
        type_str = type_str.lower()

        # Map common names to StudyType
        if "systematic" in type_str and "review" in type_str:
            return StudyType.SYSTEMATIC_REVIEW
        if "meta" in type_str:
            return StudyType.META_ANALYSIS
        if "rct" in type_str or "randomized" in type_str or "randomised" in type_str:
            return StudyType.RCT
        if "cohort" in type_str:
            if "prospective" in type_str:
                return StudyType.COHORT_PROSPECTIVE
            return StudyType.COHORT_RETROSPECTIVE
        if "case-control" in type_str or "case control" in type_str:
            return StudyType.CASE_CONTROL
        if "cross-sectional" in type_str or "cross sectional" in type_str:
            return StudyType.CROSS_SECTIONAL
        if "case series" in type_str:
            return StudyType.CASE_SERIES
        if "case report" in type_str:
            return StudyType.CASE_REPORT
        if "guideline" in type_str:
            return StudyType.GUIDELINE
        if "review" in type_str:
            return StudyType.NARRATIVE_REVIEW

        return StudyType.UNKNOWN

    def extract_pico(self, abstract: str) -> PICOExtraction:
        """Extract PICO components using LLM.

        Args:
            abstract: Paper abstract

        Returns:
            PICOExtraction with extracted components
        """
        if not self._initialize() or not abstract:
            return PICOExtraction()

        prompt = PICO_EXTRACTION_PROMPT.format(abstract=abstract)

        try:
            response = self._llm.generate(
                prompt,
                temperature=0.1,
                max_tokens=400,
            )

            json_match = self._extract_json(response)
            if not json_match:
                return PICOExtraction()

            data = json.loads(json_match)

            return PICOExtraction(
                population=data.get("population"),
                intervention=data.get("intervention"),
                comparator=data.get("comparator"),
                outcome=data.get("outcome"),
            )

        except Exception as e:
            logger.error(f"PICO extraction failed: {e}")
            return PICOExtraction()
