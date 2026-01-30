"""Multi-Language Paper Support.

Per RP-349, supports papers in multiple languages.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Language(Enum):
    """Supported languages."""

    ENGLISH = "en"
    JAPANESE = "ja"
    CHINESE = "zh"
    GERMAN = "de"
    FRENCH = "fr"
    SPANISH = "es"
    KOREAN = "ko"


@dataclass
class TranslatedContent:
    """Translated content."""

    original_text: str
    original_language: Language
    translated_text: str
    target_language: Language
    confidence: float


@dataclass
class MultilingualPaper:
    """A paper with multi-language support."""

    paper_id: str
    title: dict[Language, str]
    abstract: dict[Language, str]
    primary_language: Language
    available_languages: list[Language]


class MultiLanguageSupport:
    """Multi-language paper support.

    Per RP-349:
    - Japanese, Chinese, German paper support
    - Translation pipeline
    - Cross-language search
    """

    def __init__(
        self,
        translator=None,
        default_target: Language = Language.ENGLISH,
    ):
        self.translator = translator
        self.default_target = default_target

    def detect_language(self, text: str) -> Language:
        """Detect text language.

        Args:
            text: Input text.

        Returns:
            Detected language.
        """
        # Simple heuristics
        if self._contains_japanese(text):
            return Language.JAPANESE
        elif self._contains_chinese(text):
            return Language.CHINESE
        elif self._contains_korean(text):
            return Language.KOREAN
        elif self._contains_german(text):
            return Language.GERMAN
        else:
            return Language.ENGLISH

    def _contains_japanese(self, text: str) -> bool:
        """Check for Japanese characters."""
        for char in text:
            if "\u3040" <= char <= "\u309f":  # Hiragana
                return True
            if "\u30a0" <= char <= "\u30ff":  # Katakana
                return True
        return False

    def _contains_chinese(self, text: str) -> bool:
        """Check for Chinese characters (excluding Japanese)."""
        has_cjk = False
        for char in text:
            if "\u4e00" <= char <= "\u9fff":
                has_cjk = True

        return has_cjk and not self._contains_japanese(text)

    def _contains_korean(self, text: str) -> bool:
        """Check for Korean characters."""
        for char in text:
            if "\uac00" <= char <= "\ud7a3":
                return True
        return False

    def _contains_german(self, text: str) -> bool:
        """Check for German-specific characters."""
        german_chars = set("äöüßÄÖÜ")
        return any(c in german_chars for c in text)

    def translate(
        self,
        text: str,
        source: Language | None = None,
        target: Language | None = None,
    ) -> TranslatedContent:
        """Translate text.

        Args:
            text: Text to translate.
            source: Source language (auto-detect if None).
            target: Target language.

        Returns:
            TranslatedContent.
        """
        if source is None:
            source = self.detect_language(text)

        target = target or self.default_target

        if source == target:
            return TranslatedContent(
                original_text=text,
                original_language=source,
                translated_text=text,
                target_language=target,
                confidence=1.0,
            )

        # Use translator if available
        if self.translator:
            translated = self.translator(text, source.value, target.value)
            return TranslatedContent(
                original_text=text,
                original_language=source,
                translated_text=translated,
                target_language=target,
                confidence=0.9,
            )

        # Placeholder
        return TranslatedContent(
            original_text=text,
            original_language=source,
            translated_text=f"[Translation of: {text[:50]}...]",
            target_language=target,
            confidence=0.5,
        )

    def process_paper(
        self,
        paper_id: str,
        title: str,
        abstract: str,
    ) -> MultilingualPaper:
        """Process a paper for multi-language support.

        Args:
            paper_id: Paper ID.
            title: Paper title.
            abstract: Paper abstract.

        Returns:
            MultilingualPaper.
        """
        primary = self.detect_language(title + " " + abstract)

        titles = {primary: title}
        abstracts = {primary: abstract}

        # Translate to English if not already
        if primary != Language.ENGLISH:
            title_trans = self.translate(title, primary, Language.ENGLISH)
            abstract_trans = self.translate(abstract, primary, Language.ENGLISH)

            titles[Language.ENGLISH] = title_trans.translated_text
            abstracts[Language.ENGLISH] = abstract_trans.translated_text

        return MultilingualPaper(
            paper_id=paper_id,
            title=titles,
            abstract=abstracts,
            primary_language=primary,
            available_languages=list(titles.keys()),
        )

    def cross_language_search(
        self,
        query: str,
        papers: list[MultilingualPaper],
        target_language: Language | None = None,
    ) -> list[MultilingualPaper]:
        """Search across languages.

        Args:
            query: Search query.
            papers: Papers to search.
            target_language: Language to search in.

        Returns:
            Matching papers.
        """
        target = target_language or Language.ENGLISH
        query_lower = query.lower()

        results = []
        for paper in papers:
            # Check in target language
            title = paper.title.get(target, "").lower()
            abstract = paper.abstract.get(target, "").lower()

            if query_lower in title or query_lower in abstract:
                results.append(paper)

        return results