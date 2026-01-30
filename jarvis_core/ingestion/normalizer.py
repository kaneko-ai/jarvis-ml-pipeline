"""ITER-02: コーパス正規化 (Corpus Normalization).

テキストの正規化と標準化。
- Unicode正規化
- 空白/改行正規化
- 参照番号除去
- セクションヘッダー統一
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass
class NormalizedText:
    """正規化されたテキスト."""

    original: str
    normalized: str
    changes: list[str]

    def to_dict(self) -> dict:
        return {
            "original_length": len(self.original),
            "normalized_length": len(self.normalized),
            "changes": self.changes,
        }


class TextNormalizer:
    """テキスト正規化器.

    コーパス全体で一貫した処理を保証。
    """

    # 標準セクション名マッピング
    SECTION_MAP = {
        r"\babstract\b": "Abstract",
        r"\bintroduction\b": "Introduction",
        r"\bbackground\b": "Introduction",
        r"\bmethods?\b": "Methods",
        r"\bmaterials?\s+and\s+methods?\b": "Methods",
        r"\bresults?\b": "Results",
        r"\bdiscussion\b": "Discussion",
        r"\bconclusions?\b": "Conclusion",
        r"\breferences?\b": "References",
        r"\backnowledg": "Acknowledgments",
        r"\bsupplementary\b": "Supplementary",
    }

    def __init__(self, preserve_case: bool = False):
        self.preserve_case = preserve_case

    def normalize(self, text: str) -> NormalizedText:
        """テキストを正規化."""
        changes = []
        result = text

        # Unicode正規化（NFKC）
        normalized = unicodedata.normalize("NFKC", result)
        if normalized != result:
            changes.append("unicode_normalized")
        result = normalized

        # 制御文字除去
        result = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", result)

        # 連続空白の正規化
        old_len = len(result)
        result = re.sub(r"[ \t]+", " ", result)
        if len(result) != old_len:
            changes.append("whitespace_normalized")

        # 連続改行の正規化（3つ以上→2つ）
        result = re.sub(r"\n{3,}", "\n\n", result)

        # 参照番号の処理（ [1], [1,2], [1-3] など）
        old_len = len(result)
        result = re.sub(r"\s*\[\d+(?:[,\s\-–]+\d+)*\]", "", result)
        if len(result) != old_len:
            changes.append("citations_cleaned")

        # 上付き数字の除去
        result = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+", "", result)

        # 特殊ダッシュの統一
        result = result.replace("–", "-").replace("—", "-").replace("−", "-")

        # 引用符の統一
        result = result.replace('"', '"').replace('"', '"')
        result = result.replace(""", "'").replace(""", "'")

        # 行末の空白除去
        result = "\n".join(line.rstrip() for line in result.split("\n"))

        return NormalizedText(
            original=text,
            normalized=result.strip(),
            changes=changes,
        )

    def normalize_section_name(self, name: str) -> str:
        """セクション名を標準化."""
        name_lower = name.lower().strip()

        for pattern, standard in self.SECTION_MAP.items():
            if re.search(pattern, name_lower):
                return standard

        # マッチしない場合はタイトルケースで返す
        return name.strip().title()

    def extract_clean_sentences(self, text: str) -> list[str]:
        """クリーンな文を抽出."""
        # 正規化
        normalized = self.normalize(text).normalized

        # 文分割
        sentences = re.split(r"(?<=[.!?])\s+", normalized)

        # クリーンな文のみ抽出
        clean = []
        for sent in sentences:
            sent = sent.strip()

            # 短すぎる文はスキップ
            if len(sent) < 20:
                continue

            # 数字・記号のみの文はスキップ
            if not re.search(r"[a-zA-Z]{3,}", sent):
                continue

            # 参照リストっぽい文はスキップ
            if re.match(r"^\d+\.\s*[A-Z][a-z]+", sent):
                continue

            clean.append(sent)

        return clean


def normalize_text(text: str) -> NormalizedText:
    """便利関数: テキストを正規化."""
    normalizer = TextNormalizer()
    return normalizer.normalize(text)


def normalize_corpus(texts: list[str]) -> list[NormalizedText]:
    """便利関数: コーパス全体を正規化."""
    normalizer = TextNormalizer()
    return [normalizer.normalize(t) for t in texts]