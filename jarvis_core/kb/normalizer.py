"""Normalize terms using synonym dictionary."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable

DEFAULT_SYNONYMS = {
    "cd73": ["nt5e", "ecto-5'-nucleotidase", "ecto5n"],
    "adenosine": ["purinergic signaling", "adenosine pathway"],
    "tme": ["tumor microenvironment", "tumour microenvironment"],
}

GREEK_MAP = {
    "α": "alpha",
    "β": "beta",
    "γ": "gamma",
    "δ": "delta",
    "ε": "epsilon",
    "κ": "kappa",
}


class TermNormalizer:
    """Normalize terms using a synonym dictionary."""

    def __init__(self, synonym_path: Path):
        self.synonym_path = synonym_path
        self.synonyms = self._load_synonyms(synonym_path)

    def _load_synonyms(self, path: Path) -> Dict[str, list[str]]:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            with open(path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_SYNONYMS, f, ensure_ascii=False, indent=2)
            return {key.lower(): [item.lower() for item in values] for key, values in DEFAULT_SYNONYMS.items()}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {}
        normalized: Dict[str, list[str]] = {}
        for key, values in data.items():
            normalized[key.lower()] = [str(item).lower() for item in values]
        return normalized

    def normalize_text(self, text: str) -> str:
        cleaned = text.lower()
        for greek, latin in GREEK_MAP.items():
            cleaned = cleaned.replace(greek, latin)
        cleaned = re.sub(r"[-_/]", " ", cleaned)
        cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def normalize_term(self, term: str) -> str:
        cleaned = self.normalize_text(term)
        if cleaned in self.synonyms:
            return cleaned
        for canonical, synonyms in self.synonyms.items():
            if cleaned == canonical:
                return canonical
            if cleaned in synonyms:
                return canonical
        return cleaned

    def expand_terms(self, terms: Iterable[str]) -> list[str]:
        expanded = []
        for term in terms:
            normalized = self.normalize_term(term)
            if normalized:
                expanded.append(normalized)
        return sorted(set(expanded))
