"""Sentence Splitter.

Per RP-112, splits text into sentences with stable IDs.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import List


@dataclass
class Sentence:
    """A sentence with stable ID."""

    sentence_id: str
    text: str
    start_char: int
    end_char: int
    index: int  # 0-based index in document

    @classmethod
    def create(cls, text: str, start: int, end: int, index: int) -> "Sentence":
        """Create sentence with deterministic ID."""
        # Hash based on content for stability
        content_hash = hashlib.sha256(text.encode()).hexdigest()[:12]
        sentence_id = f"s{index:04d}_{content_hash}"

        return cls(
            sentence_id=sentence_id,
            text=text,
            start_char=start,
            end_char=end,
            index=index,
        )


# Abbreviations that don't end sentences
ABBREVIATIONS = {
    "dr.",
    "mr.",
    "mrs.",
    "ms.",
    "prof.",
    "sr.",
    "jr.",
    "vs.",
    "etc.",
    "i.e.",
    "e.g.",
    "cf.",
    "al.",
    "et.",
    "fig.",
    "figs.",
    "ref.",
    "refs.",
    "vol.",
    "no.",
    "p.",
    "pp.",
    "ed.",
    "eds.",
    "trans.",
}


def is_sentence_boundary(text: str, pos: int) -> bool:
    """Check if position is a sentence boundary."""
    if pos >= len(text):
        return True

    # Must be after sentence-ending punctuation
    if pos == 0:
        return False

    prev_char = text[pos - 1]
    if prev_char not in ".!?":
        return False

    # Check for abbreviations
    # Look back for the word before the period
    word_start = pos - 1
    while word_start > 0 and text[word_start - 1].isalpha():
        word_start -= 1

    if word_start < pos - 1:
        word = text[word_start:pos].lower()
        if word in ABBREVIATIONS:
            return False

    # Check if followed by lowercase (continuation)
    next_pos = pos
    while next_pos < len(text) and text[next_pos].isspace():
        next_pos += 1

    if next_pos < len(text) and text[next_pos].islower():
        return False

    return True


def split_sentences(text: str) -> List[Sentence]:
    """Split text into sentences.

    Args:
        text: Input text.

    Returns:
        List of Sentence objects with stable IDs.
    """
    sentences = []
    current_start = 0
    index = 0

    # Find potential sentence boundaries
    i = 0
    while i < len(text):
        char = text[i]

        if char in ".!?":
            # Check if this is a real sentence boundary
            if is_sentence_boundary(text, i + 1):
                # Extract sentence
                sentence_text = text[current_start : i + 1].strip()

                if sentence_text:
                    sentences.append(
                        Sentence.create(
                            text=sentence_text,
                            start=current_start,
                            end=i + 1,
                            index=index,
                        )
                    )
                    index += 1

                # Move past whitespace
                i += 1
                while i < len(text) and text[i].isspace():
                    i += 1
                current_start = i
                continue

        i += 1

    # Handle remaining text
    remaining = text[current_start:].strip()
    if remaining:
        sentences.append(
            Sentence.create(
                text=remaining,
                start=current_start,
                end=len(text),
                index=index,
            )
        )

    return sentences


def split_japanese(text: str) -> List[Sentence]:
    """Split Japanese text into sentences (。区切り)."""
    sentences = []
    current_start = 0
    index = 0

    for i, char in enumerate(text):
        if char in "。！？":
            sentence_text = text[current_start : i + 1].strip()
            if sentence_text:
                sentences.append(
                    Sentence.create(
                        text=sentence_text,
                        start=current_start,
                        end=i + 1,
                        index=index,
                    )
                )
                index += 1
            current_start = i + 1

    # Remaining
    remaining = text[current_start:].strip()
    if remaining:
        sentences.append(
            Sentence.create(
                text=remaining,
                start=current_start,
                end=len(text),
                index=index,
            )
        )

    return sentences


def split_sentences_auto(text: str) -> List[Sentence]:
    """Auto-detect language and split sentences."""
    # Simple heuristic: check for Japanese characters
    has_japanese = any("\u3040" <= c <= "\u30ff" or "\u4e00" <= c <= "\u9fff" for c in text)

    if has_japanese:
        return split_japanese(text)
    return split_sentences(text)
