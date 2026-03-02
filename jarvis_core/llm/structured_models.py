"""Pydantic models for structured LLM outputs in JARVIS."""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class EvidenceLevelLLM(str, Enum):
    LEVEL_1A = "1a"
    LEVEL_1B = "1b"
    LEVEL_2A = "2a"
    LEVEL_2B = "2b"
    LEVEL_3 = "3"
    LEVEL_4 = "4"
    LEVEL_5 = "5"


class EvidenceGradeLLM(BaseModel):
    level: EvidenceLevelLLM
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    study_type: str


class PaperSummaryLLM(BaseModel):
    title_ja: str = Field(description="Title in Japanese")
    summary_ja: str = Field(description="Summary in Japanese, max 300 chars")
    key_findings: list[str] = Field(description="Key findings, 3-5 items")
    limitations: Optional[str] = Field(default=None, description="Limitations")
    relevance_score: float = Field(ge=0.0, le=1.0, description="Relevance to research theme")


class ContradictionResultLLM(BaseModel):
    is_contradictory: bool
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str
    contradiction_type: Optional[str] = None


class CitationStanceLLM(BaseModel):
    stance: str = Field(description="SUPPORT, CONTRAST, NEUTRAL, or MENTION")
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
