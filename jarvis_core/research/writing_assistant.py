"""Paper Writing Assistant.

Per RP-444, assists with paper writing.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PaperSection(Enum):
    """Paper sections."""

    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    METHODS = "methods"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"
    REFERENCES = "references"


@dataclass
class WritingSuggestion:
    """A writing suggestion."""

    section: PaperSection
    current_text: str
    suggested_text: str
    reason: str
    confidence: float


@dataclass
class CitationSuggestion:
    """A citation suggestion."""

    position: int
    paper_id: str
    title: str
    relevance_score: float
    citation_text: str


class PaperWritingAssistant:
    """Assists with paper writing.
    
    Per RP-444:
    - Structure suggestions
    - Citation insertion
    - Style adjustment
    """

    def __init__(
        self,
        llm_generator=None,
        citation_db=None,
        style_guide: str = "scientific",
    ):
        self.llm = llm_generator
        self.citation_db = citation_db
        self.style_guide = style_guide

    def suggest_structure(
        self,
        topic: str,
        paper_type: str = "research",
    ) -> dict[PaperSection, str]:
        """Suggest paper structure.
        
        Args:
            topic: Paper topic.
            paper_type: Type of paper.
            
        Returns:
            Section outlines.
        """
        outlines = {
            PaperSection.ABSTRACT: f"Summarize research on {topic}",
            PaperSection.INTRODUCTION: f"Background on {topic}, research gap, objectives",
            PaperSection.METHODS: "Data sources, analysis methods, validation",
            PaperSection.RESULTS: "Key findings, statistical analysis",
            PaperSection.DISCUSSION: "Interpretation, limitations, implications",
            PaperSection.CONCLUSION: "Summary and future directions",
        }

        return outlines

    def suggest_citations(
        self,
        text: str,
        available_papers: list[dict] | None = None,
    ) -> list[CitationSuggestion]:
        """Suggest citations for text.
        
        Args:
            text: Text to add citations to.
            available_papers: Papers to cite from.
            
        Returns:
            Citation suggestions.
        """
        suggestions = []

        # Find claim-like sentences
        sentences = text.split(". ")

        for i, sentence in enumerate(sentences):
            if self._needs_citation(sentence):
                # Find relevant paper
                if available_papers:
                    paper = self._find_relevant_paper(sentence, available_papers)
                    if paper:
                        suggestions.append(CitationSuggestion(
                            position=sum(len(s) + 2 for s in sentences[:i]),
                            paper_id=paper.get("id", ""),
                            title=paper.get("title", ""),
                            relevance_score=0.8,
                            citation_text=self._format_citation(paper),
                        ))

        return suggestions

    def _needs_citation(self, sentence: str) -> bool:
        """Check if sentence needs citation."""
        claim_indicators = [
            "studies show",
            "research indicates",
            "has been demonstrated",
            "according to",
            "evidence suggests",
            "is known to",
            "has been reported",
        ]

        sentence_lower = sentence.lower()
        return any(ind in sentence_lower for ind in claim_indicators)

    def _find_relevant_paper(
        self,
        sentence: str,
        papers: list[dict],
    ) -> dict | None:
        """Find most relevant paper for sentence."""
        if not papers:
            return None

        # Simple keyword matching
        sentence_words = set(sentence.lower().split())

        best_paper = None
        best_score = 0

        for paper in papers:
            title_words = set(paper.get("title", "").lower().split())
            overlap = len(sentence_words & title_words)

            if overlap > best_score:
                best_score = overlap
                best_paper = paper

        return best_paper if best_score > 2 else None

    def _format_citation(self, paper: dict) -> str:
        """Format citation."""
        authors = paper.get("authors", ["Unknown"])
        year = paper.get("year", "")

        if len(authors) > 2:
            author_str = f"{authors[0]} et al."
        elif len(authors) == 2:
            author_str = f"{authors[0]} and {authors[1]}"
        else:
            author_str = authors[0]

        return f"({author_str}, {year})"

    def improve_section(
        self,
        section: PaperSection,
        text: str,
    ) -> WritingSuggestion:
        """Suggest improvements for a section.
        
        Args:
            section: Section type.
            text: Current text.
            
        Returns:
            Writing suggestion.
        """
        suggestions = {
            PaperSection.ABSTRACT: "Consider adding quantitative results",
            PaperSection.INTRODUCTION: "Strengthen the research gap statement",
            PaperSection.METHODS: "Add more detail on statistical methods",
            PaperSection.RESULTS: "Include effect sizes and confidence intervals",
            PaperSection.DISCUSSION: "Address potential limitations",
            PaperSection.CONCLUSION: "End with clear future directions",
        }

        return WritingSuggestion(
            section=section,
            current_text=text[:100] + "..." if len(text) > 100 else text,
            suggested_text="",  # Would be generated by LLM
            reason=suggestions.get(section, "General improvement"),
            confidence=0.7,
        )

    def check_style(
        self,
        text: str,
    ) -> list[dict[str, str]]:
        """Check writing style.
        
        Args:
            text: Text to check.
            
        Returns:
            Style issues.
        """
        issues = []

        # Check for passive voice overuse
        passive_patterns = ["was ", "were ", "is being", "has been"]
        passive_count = sum(text.lower().count(p) for p in passive_patterns)
        if passive_count > 5:
            issues.append({
                "type": "passive_voice",
                "message": "Consider reducing passive voice usage",
            })

        # Check for long sentences
        sentences = text.split(". ")
        long_sentences = [s for s in sentences if len(s.split()) > 40]
        if long_sentences:
            issues.append({
                "type": "long_sentence",
                "message": f"{len(long_sentences)} sentence(s) exceed 40 words",
            })

        # Check for first person
        if " I " in text or " we " in text.lower():
            issues.append({
                "type": "first_person",
                "message": "Consider third person for formal style",
            })

        return issues
