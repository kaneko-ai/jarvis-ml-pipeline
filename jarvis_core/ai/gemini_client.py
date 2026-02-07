"""JARVIS Gemini API Integration for real AI features."""

import json
import os
import urllib.request
from dataclasses import dataclass


@dataclass
class GeminiConfig:
    """Gemini API configuration."""

    api_key: str
    model: str = "gemini-2.0-flash-exp"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"


class GeminiClient:
    """Google Gemini API client for AI features."""

    def __init__(self, config: GeminiConfig | None = None):
        if config:
            self.config = config
        else:
            api_key = os.environ.get("GEMINI_API_KEY", "")
            self.config = GeminiConfig(api_key=api_key)

    def _make_request(self, prompt: str, system_instruction: str = "") -> str | None:
        """Make API request to Gemini.

        Args:
            prompt: User prompt
            system_instruction: System instruction

        Returns:
            Generated text or None
        """
        if not self.config.api_key:
            return None

        url = f"{self.config.base_url}/models/{self.config.model}:generateContent?key={self.config.api_key}"

        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=data, headers={"Content-Type": "application/json"}, method="POST"
            )

            with urllib.request.urlopen(req, timeout=30) as response:  # nosec B310
                result = json.loads(response.read().decode())
                return (
                    result.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
        except Exception as e:
            print(f"Gemini API error: {e}")
            return None

    def summarize_paper(self, paper: dict) -> str:
        """Generate AI summary of a paper.

        Args:
            paper: Paper dictionary with title, abstract, etc.

        Returns:
            Summary text
        """
        prompt = f"""Summarize this research paper in 3-4 sentences:

Title: {paper.get('title', 'Unknown')}
Abstract: {paper.get('abstract', 'No abstract available')}

Provide:
1. Main objective
2. Key methodology
3. Main findings
4. Significance"""

        system = "You are a research paper summarization assistant. Be concise and accurate."

        result = self._make_request(prompt, system)
        return result or "Summary not available. API key may be missing."

    def find_related_topics(self, paper: dict) -> list[str]:
        """Find related research topics.

        Args:
            paper: Paper dictionary

        Returns:
            List of related topics
        """
        prompt = f"""Given this paper title: "{paper.get('title', '')}"

List 5 related research topics that researchers might also be interested in.
Return as a simple list, one topic per line."""

        result = self._make_request(prompt)
        if result:
            return [line.strip("- ").strip() for line in result.strip().split("\n") if line.strip()]
        return []

    def answer_question(self, paper: dict, question: str) -> str:
        """Answer a question about a paper.

        Args:
            paper: Paper dictionary
            question: User question

        Returns:
            Answer text
        """
        prompt = f"""Based on this paper information:

Title: {paper.get('title', '')}
Abstract: {paper.get('abstract', '')}
Authors: {paper.get('authors', '')}
Journal: {paper.get('journal', '')}
Year: {paper.get('year', '')}

Answer this question: {question}"""

        system = "You are a helpful research assistant. Answer based only on the provided paper information."

        result = self._make_request(prompt, system)
        return result or "Unable to answer. Please check your API configuration."

    def translate_abstract(self, abstract: str, target_lang: str = "Japanese") -> str:
        """Translate abstract to another language.

        Args:
            abstract: Abstract text
            target_lang: Target language

        Returns:
            Translated text
        """
        prompt = f"Translate this research abstract to {target_lang}:\n\n{abstract}"

        result = self._make_request(prompt)
        return result or abstract

    def extract_key_findings(self, paper: dict) -> list[str]:
        """Extract key findings from paper.

        Args:
            paper: Paper dictionary

        Returns:
            List of key findings
        """
        prompt = f"""Extract 3-5 key findings from this paper:

Title: {paper.get('title', '')}
Abstract: {paper.get('abstract', '')}

List each finding on a separate line, starting with a bullet point."""

        result = self._make_request(prompt)
        if result:
            return [
                line.strip("•- ").strip() for line in result.strip().split("\n") if line.strip()
            ]
        return []


class MockGeminiClient:
    """Mock Gemini client for testing without API key."""

    def summarize_paper(self, paper: dict) -> str:
        return f"[Mock Summary] This paper titled '{paper.get('title', 'Unknown')[:30]}...' presents significant findings in its field."

    def find_related_topics(self, paper: dict) -> list[str]:
        return [
            "Machine Learning",
            "Data Analysis",
            "Healthcare AI",
            "Clinical Research",
            "Predictive Modeling",
        ]

    def answer_question(self, paper: dict, question: str) -> str:
        return f"[Mock Answer] Based on the paper, the answer to '{question[:30]}...' involves key research findings."

    def translate_abstract(self, abstract: str, target_lang: str = "Japanese") -> str:
        return f"[Mock Translation to {target_lang}] {abstract[:100]}..."

    def extract_key_findings(self, paper: dict) -> list[str]:
        return [
            "Novel methodology improves accuracy",
            "Significant results compared to baseline",
            "Applicable to real-world scenarios",
        ]


def get_gemini_client(use_mock: bool = False) -> GeminiClient:
    """Get Gemini client instance.

    Args:
        use_mock: Use mock client if True or no API key

    Returns:
        GeminiClient or MockGeminiClient
    """
    if use_mock or not os.environ.get("GEMINI_API_KEY"):
        return MockGeminiClient()
    return GeminiClient()


if __name__ == "__main__":
    # Demo
    client = get_gemini_client(use_mock=True)

    paper = {
        "title": "Deep Learning for COVID-19 Treatment Prediction",
        "abstract": "This study presents a novel deep learning model for predicting treatment outcomes...",
        "authors": "Smith J, et al.",
        "journal": "Nature Medicine",
        "year": 2024,
    }

    print("=== Paper Summary ===")
    print(client.summarize_paper(paper))

    print("\n=== Related Topics ===")
    print(client.find_related_topics(paper))

    print("\n=== Q&A ===")
    print(client.answer_question(paper, "What is the main contribution?"))
