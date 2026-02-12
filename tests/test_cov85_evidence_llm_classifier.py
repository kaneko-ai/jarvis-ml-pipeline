"""Coverage tests for jarvis_core.evidence.llm_classifier."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from jarvis_core.evidence.llm_classifier import (
    LLMBasedClassifier,
    LLMConfig,
)
from jarvis_core.evidence.schema import EvidenceGrade, EvidenceLevel, StudyType


class TestLLMConfig:
    def test_defaults(self) -> None:
        config = LLMConfig()
        assert config.model == "llama3.2"
        assert config.temperature == 0.1
        assert config.max_tokens == 500

    def test_custom(self) -> None:
        config = LLMConfig(model="custom", temperature=0.5, max_tokens=1000)
        assert config.model == "custom"


def _make_classifier(llm_mock=None):
    """Create LLMBasedClassifier with _initialize bypassed."""
    with patch.object(LLMBasedClassifier, "_initialize", return_value=llm_mock is not None):
        cls = LLMBasedClassifier()
    cls._initialized = True
    cls._llm = llm_mock
    return cls


class TestLLMBasedClassifier:
    def test_init_default(self) -> None:
        cls = _make_classifier()
        assert cls._config is not None
        assert cls._config.model == "llama3.2"

    def test_init_custom_config(self) -> None:
        config = LLMConfig(model="test")
        with patch.object(LLMBasedClassifier, "_initialize", return_value=False):
            cls = LLMBasedClassifier(config=config)
        assert cls._config.model == "test"

    def test_classify_fallback(self) -> None:
        """When _initialize returns False, should return unknown."""
        cls = _make_classifier(llm_mock=None)
        # Force _initialize to return False
        with patch.object(cls, "_initialize", return_value=False):
            result = cls.classify(title="RCT study", abstract="randomized controlled trial")
        assert isinstance(result, EvidenceGrade)
        assert result.level == EvidenceLevel.UNKNOWN
        assert result.classifier_source == "llm_unavailable"

    def test_classify_with_llm(self) -> None:
        """When LLM is available, should use LLM."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps(
            {
                "evidence_level": "1a",
                "study_type": "rct",
                "confidence": 90,
                "reasoning": "Randomized trial design",
            }
        )
        cls = _make_classifier(llm_mock=mock_llm)
        with patch.object(cls, "_initialize", return_value=True):
            result = cls.classify(title="RCT", abstract="randomized controlled trial")
        assert isinstance(result, EvidenceGrade)
        assert result.level == EvidenceLevel.LEVEL_1A
        assert result.study_type == StudyType.RCT
        assert result.confidence == 0.9
        assert result.classifier_source == "llm"

    def test_classify_empty_input(self) -> None:
        """Empty title and abstract should return unknown level."""
        cls = _make_classifier(llm_mock=None)
        # _initialize returns False => fallback to unknown
        with patch.object(cls, "_initialize", return_value=False):
            result = cls.classify(title="", abstract="")
        assert isinstance(result, EvidenceGrade)
        assert result.level == EvidenceLevel.UNKNOWN
        assert result.classifier_source == "llm_unavailable"

    def test_classify_llm_error(self) -> None:
        """When LLM raises, should fall back."""
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = Exception("LLM error")
        cls = _make_classifier(llm_mock=mock_llm)
        with patch.object(cls, "_initialize", return_value=True):
            result = cls.classify(title="Test", abstract="test abstract")
        assert isinstance(result, EvidenceGrade)
        assert result.classifier_source == "llm_error"

    def test_parse_response_valid_json(self) -> None:
        cls = _make_classifier()
        response = json.dumps(
            {
                "evidence_level": "2b",
                "study_type": "cohort",
                "confidence": 80,
                "reasoning": "Cohort study design",
            }
        )
        result = cls._parse_response(response)
        assert isinstance(result, EvidenceGrade)
        assert result.level == EvidenceLevel.LEVEL_2B
        assert result.study_type == StudyType.COHORT_RETROSPECTIVE
        assert result.confidence == 0.8
        assert result.classifier_source == "llm"
        assert result.quality_notes == ["Cohort study design"]

    def test_parse_response_invalid_json(self) -> None:
        cls = _make_classifier()
        result = cls._parse_response("not json at all")
        assert isinstance(result, EvidenceGrade)
        assert result.level == EvidenceLevel.UNKNOWN

    def test_parse_response_code_block(self) -> None:
        cls = _make_classifier()
        response = 'Some text ```json\n{"evidence_level": "3b", "study_type": "case-control", "confidence": 55}\n```'
        result = cls._parse_response(response)
        assert isinstance(result, EvidenceGrade)
        assert result.level == EvidenceLevel.LEVEL_3B
        assert result.study_type == StudyType.CASE_CONTROL

    def test_extract_json_found(self) -> None:
        cls = _make_classifier()
        text = 'Here is the result: {"key": "value"} end.'
        result = cls._extract_json(text)
        assert result == '{"key": "value"}'

    def test_extract_json_not_found(self) -> None:
        cls = _make_classifier()
        result = cls._extract_json("no json here")
        assert result is None

    def test_parse_evidence_level(self) -> None:
        cls = _make_classifier()
        assert cls._parse_evidence_level("1a") == EvidenceLevel.LEVEL_1A
        assert cls._parse_evidence_level("2b") == EvidenceLevel.LEVEL_2B
        assert cls._parse_evidence_level("3a") == EvidenceLevel.LEVEL_3A
        assert cls._parse_evidence_level("4") == EvidenceLevel.LEVEL_4
        assert cls._parse_evidence_level("5") == EvidenceLevel.LEVEL_5
        assert cls._parse_evidence_level("unknown") == EvidenceLevel.UNKNOWN

    def test_parse_study_type(self) -> None:
        cls = _make_classifier()
        assert cls._parse_study_type("RCT") == StudyType.RCT
        # "cohort" maps to one of the cohort types
        cohort_result = cls._parse_study_type("cohort")
        assert "COHORT" in cohort_result.name or cohort_result == StudyType.UNKNOWN
        assert cls._parse_study_type("something_else") == StudyType.UNKNOWN

    def test_extract_pico_with_llm(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps(
            {
                "population": "Adults with diabetes",
                "intervention": "Drug X",
                "comparator": "Placebo",
                "outcome": "HbA1c reduction",
            }
        )
        cls = _make_classifier(llm_mock=mock_llm)
        with patch.object(cls, "_initialize", return_value=True):
            pico = cls.extract_pico("200 adults with diabetes received Drug X versus placebo")
        assert pico.population == "Adults with diabetes"
        assert pico.intervention == "Drug X"
        assert pico.comparator == "Placebo"
        assert pico.outcome == "HbA1c reduction"

    def test_extract_pico_fallback(self) -> None:
        cls = _make_classifier()
        with patch.object(cls, "_initialize", return_value=False):
            pico = cls.extract_pico("200 adults with diabetes")
        assert pico.population is None
        assert pico.intervention is None

    def test_extract_pico_error(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = Exception("LLM error")
        cls = _make_classifier(llm_mock=mock_llm)
        with patch.object(cls, "_initialize", return_value=True):
            pico = cls.extract_pico("test abstract")
        assert pico.population is None
        assert pico.intervention is None

    def test_extract_pico_empty(self) -> None:
        cls = _make_classifier()
        with patch.object(cls, "_initialize", return_value=True):
            pico = cls.extract_pico("")
        assert pico.population is None

    def test_parse_study_type_others(self) -> None:
        cls = _make_classifier()
        assert cls._parse_study_type("A Case Report of ...") == StudyType.CASE_REPORT
        assert cls._parse_study_type("Clinical practice guideline") == StudyType.GUIDELINE
        assert cls._parse_study_type("A Narrative review of") == StudyType.NARRATIVE_REVIEW

    def test_extract_json_block(self) -> None:
        cls = _make_classifier()
        text = '```json\n{"level": "1a"}\n```'
        assert cls._extract_json(text) == '{"level": "1a"}'

    def test_classify_runtime_error(self) -> None:
        cls = _make_classifier(llm_mock=None)
        # Forced None _llm with _initialize returning True should trigger RuntimeError
        with patch.object(cls, "_initialize", return_value=True):
            result = cls.classify(title="Test")
        assert result.classifier_source == "llm_error"

    def test_extract_pico_runtime_error(self) -> None:
        cls = _make_classifier(llm_mock=None)
        with patch.object(cls, "_initialize", return_value=True):
            result = cls.extract_pico("Test")
        assert result.population is None

    def test_initialize_import_error(self) -> None:
        config = LLMConfig()
        cls = LLMBasedClassifier(config=config)
        with patch("jarvis_core.llm.ollama_adapter.OllamaAdapter", side_effect=ImportError()):
            assert cls._initialize() is False

    def test_initialize_generic_exception(self) -> None:
        config = LLMConfig()
        cls = LLMBasedClassifier(config=config)
        with patch("jarvis_core.llm.ollama_adapter.OllamaAdapter", side_effect=Exception()):
            assert cls._initialize() is False
