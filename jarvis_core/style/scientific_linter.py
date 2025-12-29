"""Scientific writing lint checks for lab submissions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List
import re


@dataclass
class LintIssue:
    issue_type: str
    severity: str
    message: str
    location: str
    excerpt: str


AMBIGUOUS_PHRASES = [
    "示唆される",
    "と思われる",
    "と考えられる",
    "可能性がある",
]

SUBJECTLESS_PHRASES = [
    "示された",
    "確認された",
    "観察された",
]

CAUSAL_TOKENS = [
    ("相関", "因果"),
    ("関連", "原因"),
]

STAT_HINTS = ["有意", "p値", "p<", "p="]

REFERENCE_HINTS = ["報告", "先行研究", "先行報告"]


def _split_sentences(text: str) -> List[str]:
    sentences = re.split(r"(?<=[。．.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def lint_text(text: str, source_prefix: str) -> List[LintIssue]:
    issues: List[LintIssue] = []
    sentences = _split_sentences(text)

    for idx, sentence in enumerate(sentences, start=1):
        location = f"{source_prefix}:sentence:{idx}"

        for phrase in AMBIGUOUS_PHRASES:
            if phrase in sentence:
                issues.append(
                    LintIssue(
                        issue_type="ambiguous_expression",
                        severity="WARN",
                        message=f"曖昧表現の使用: {phrase}",
                        location=location,
                        excerpt=sentence,
                    )
                )

        for phrase in SUBJECTLESS_PHRASES:
            if phrase in sentence and not re.search(r"(我々|本研究|著者)", sentence):
                issues.append(
                    LintIssue(
                        issue_type="subject_missing",
                        severity="WARN",
                        message=f"主語が不明な受動表現: {phrase}",
                        location=location,
                        excerpt=sentence,
                    )
                )

        for left, right in CAUSAL_TOKENS:
            if left in sentence and right in sentence:
                issues.append(
                    LintIssue(
                        issue_type="causal_leap",
                        severity="ERROR",
                        message="相関から因果への飛躍表現を検出",
                        location=location,
                        excerpt=sentence,
                    )
                )

        if any(token in sentence for token in STAT_HINTS):
            if not re.search(r"n\s*=\s*\d+", sentence):
                issues.append(
                    LintIssue(
                        issue_type="quant_missing",
                        severity="ERROR",
                        message="統計表現にn数が欠落",
                        location=location,
                        excerpt=sentence,
                    )
                )
            if not re.search(r"p\s*[<=>]\s*\d", sentence):
                issues.append(
                    LintIssue(
                        issue_type="stat_format",
                        severity="WARN",
                        message="p値表記が不十分",
                        location=location,
                        excerpt=sentence,
                    )
                )

        if any(token in sentence for token in REFERENCE_HINTS):
            if not re.search(r"\[(\d+)\]", sentence) and not re.search(r"\(([^)]+),\s*\d{4}\)", sentence):
                issues.append(
                    LintIssue(
                        issue_type="missing_reference",
                        severity="WARN",
                        message="主張に引用が付与されていない可能性",
                        location=location,
                        excerpt=sentence,
                    )
                )

    return issues
