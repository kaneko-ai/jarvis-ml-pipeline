"""ID normalization utilities for paper graph commands."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NormalizedPaperId:
    raw: str
    kind: str
    value: str

    @property
    def canonical(self) -> str:
        return f"{self.kind}:{self.value}"

    @property
    def s2_lookup_id(self) -> str:
        if self.kind == "doi":
            return f"DOI:{self.value}"
        if self.kind == "arxiv":
            return f"ARXIV:{self.value}"
        if self.kind == "pmid":
            return f"PMID:{self.value}"
        return self.value


def normalize_paper_id(value: str) -> NormalizedPaperId:
    text = (value or "").strip()
    if not text:
        raise ValueError("paper id is required")
    if ":" in text:
        prefix, body = text.split(":", 1)
        kind = prefix.strip().lower()
        body = body.strip()
    else:
        kind = "s2"
        body = text
    if kind not in {"doi", "pmid", "arxiv", "s2"}:
        raise ValueError(f"unsupported paper id prefix: {kind}")
    if not body:
        raise ValueError("paper id body is empty")
    return NormalizedPaperId(raw=text, kind=kind, value=body)


def paper_key_from_dict(paper: dict) -> str:
    external_ids = paper.get("externalIds") or {}
    if isinstance(external_ids, dict):
        doi = external_ids.get("DOI")
        if doi:
            return f"doi:{str(doi).lower()}"
        arxiv = external_ids.get("ArXiv")
        if arxiv:
            return f"arxiv:{str(arxiv).lower()}"
        pmid = external_ids.get("PubMed")
        if pmid:
            return f"pmid:{str(pmid)}"
    paper_id = paper.get("paperId")
    if paper_id:
        return f"s2:{paper_id}"
    title = str(paper.get("title", "")).strip().lower()
    year = str(paper.get("year", ""))
    return f"title:{title}|year:{year}"
