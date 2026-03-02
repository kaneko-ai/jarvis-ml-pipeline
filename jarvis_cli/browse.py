"""jarvis browse - Lightweight browser agent for paper metadata extraction (C-2).

Fetches a URL and extracts paper metadata (title, abstract, authors, DOI).
Uses requests + Scrapling parser (784x faster than BeautifulSoup).

Supported sites:
  - PubMed (pubmed.ncbi.nlm.nih.gov)
  - arXiv (arxiv.org)
  - DOI redirect (doi.org)
  - Generic HTML pages (best-effort extraction via meta tags)

Security: Only allows URLs matching the security allow-list.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests
from scrapling.parser import Selector

ALLOWED_DOMAINS = [
    "pubmed.ncbi.nlm.nih.gov",
    "ncbi.nlm.nih.gov",
    "arxiv.org",
    "doi.org",
    "europepmc.org",
    "semanticscholar.org",
    "scholar.google.com",
    "crossref.org",
    "api.crossref.org",
    "api.openalex.org",
]

HEADERS = {
    "User-Agent": "JARVIS Research OS/1.0 (Academic research tool)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _is_allowed(url: str) -> bool:
    for domain in ALLOWED_DOMAINS:
        if domain in url:
            return True
    return False


def _fetch_page(url: str, timeout: int = 20) -> tuple[str, str]:
    resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()
    return resp.url, resp.text


def _first(page, selector):
    """Helper: return first element matching CSS selector, or None."""
    hits = page.css(selector)
    if hits and len(hits) > 0:
        return hits[0]
    return None


# ========== PubMed ==========

def _extract_pubmed(url: str, html: str) -> dict:
    page = Selector(html)
    meta = {"source": "pubmed", "url": url}

    pmid_match = re.search(r"/(\d{6,10})/?$", url)
    if pmid_match:
        meta["pmid"] = pmid_match.group(1)

    # Title
    title_el = _first(page, "h1.heading-title")
    if title_el:
        meta["title"] = title_el.text.strip()
    else:
        og = _first(page, 'meta[property="og:title"]')
        if og:
            meta["title"] = og.attrib.get("content", "").strip()

    # Abstract
    abs_el = _first(page, "#eng-abstract")
    if abs_el is None:
        abs_el = _first(page, "div.abstract-content")
    if abs_el:
        meta["abstract"] = abs_el.text.strip()
    else:
        og_desc = _first(page, 'meta[property="og:description"]')
        if og_desc:
            meta["abstract"] = og_desc.attrib.get("content", "").strip()

    # Authors
    author_els = page.css("span.authors-list-item a.full-name")
    if author_els and len(author_els) > 0:
        meta["authors"] = [a.text.strip() for a in author_els if a.text.strip()]
    else:
        author_els2 = page.css("a.full-name")
        if author_els2 and len(author_els2) > 0:
            meta["authors"] = [a.text.strip() for a in author_els2 if a.text.strip()]

    # Journal
    journal_el = _first(page, "button.journal-actions-trigger")
    if journal_el is None:
        journal_el = _first(page, "a[data-ga-action='click_article_journal_title']")
    if journal_el:
        meta["journal"] = journal_el.text.strip()

    # DOI
    doi_el = _first(page, "span.citation-doi")
    if doi_el:
        doi_text = doi_el.text.strip()
        doi_match = re.search(r"(10\.\d{4,}/\S+)", doi_text)
        if doi_match:
            meta["doi"] = doi_match.group(1).rstrip(".")

    # Year
    year_el = _first(page, "span.cit")
    if year_el:
        yr = re.search(r"(\d{4})", year_el.text)
        if yr:
            meta["year"] = int(yr.group(1))

    return meta


# ========== arXiv ==========

def _extract_arxiv(url: str, html: str) -> dict:
    page = Selector(html)
    meta = {"source": "arxiv", "url": url}

    # arXiv ID
    id_match = re.search(r"abs/([^\s?#]+)", url)
    if id_match:
        meta["arxiv_id"] = id_match.group(1)

    # Title - <h1 class="title mathjax"> contains <span class="descriptor">Title:</span> + text
    title_el = _first(page, "h1.title")
    if title_el:
        raw = title_el.text.strip()
        raw = re.sub(r"^Title\s*:\s*", "", raw, flags=re.IGNORECASE).strip()
        if raw:
            meta["title"] = raw
    if "title" not in meta:
        og = _first(page, 'meta[property="og:title"]')
        if og:
            meta["title"] = og.attrib.get("content", "").strip()
    if "title" not in meta:
        t = _first(page, "title")
        if t:
            meta["title"] = t.text.strip()

    # Abstract - <blockquote class="abstract mathjax">
    abs_el = _first(page, "blockquote.abstract")
    if abs_el:
        raw = abs_el.text.strip()
        raw = re.sub(r"^Abstract\s*:\s*", "", raw, flags=re.IGNORECASE).strip()
        if raw:
            meta["abstract"] = raw
    if "abstract" not in meta:
        og_desc = _first(page, 'meta[property="og:description"]')
        if og_desc:
            meta["abstract"] = og_desc.attrib.get("content", "").strip()
    if "abstract" not in meta:
        desc = _first(page, 'meta[name="description"]')
        if desc:
            meta["abstract"] = desc.attrib.get("content", "").strip()

    # Authors - <div class="authors"> with <a> tags
    authors_div = _first(page, "div.authors")
    if authors_div:
        a_tags = authors_div.css("a")
        if a_tags and len(a_tags) > 0:
            meta["authors"] = [a.text.strip() for a in a_tags if a.text.strip()]
    if "authors" not in meta:
        author_meta = page.css('meta[name="citation_author"]')
        if author_meta and len(author_meta) > 0:
            meta["authors"] = [m.attrib.get("content", "").strip() for m in author_meta]

    # DOI
    doi_el = _first(page, "td.tablecell.arxivdoi a")
    if doi_el:
        href = doi_el.attrib.get("href", "")
        doi_match = re.search(r"(10\.\d{4,}/\S+)", href)
        if doi_match:
            meta["doi"] = doi_match.group(1)
    if "doi" not in meta:
        doi_meta = _first(page, 'meta[name="citation_doi"]')
        if doi_meta:
            meta["doi"] = doi_meta.attrib.get("content", "").strip()

    # Year
    date_el = _first(page, 'meta[name="citation_date"]')
    if date_el:
        yr = re.search(r"(\d{4})", date_el.attrib.get("content", ""))
        if yr:
            meta["year"] = int(yr.group(1))
    if "year" not in meta:
        sub_div = _first(page, "div.submission-history")
        if sub_div:
            yr = re.search(r"(\d{4})", sub_div.text)
            if yr:
                meta["year"] = int(yr.group(1))
    if "year" not in meta:
        yr = re.search(r"(\d{4})", url)
        if yr:
            meta["year"] = int(yr.group(1))

    # Categories
    subj_el = _first(page, "span.primary-subject")
    if subj_el:
        meta["categories"] = subj_el.text.strip()

    return meta


# ========== Generic ==========

def _extract_generic(url: str, html: str) -> dict:
    page = Selector(html)
    meta = {"source": "generic", "url": url}

    for sel in ['meta[property="og:title"]', 'meta[name="citation_title"]', "title"]:
        el = _first(page, sel)
        if el:
            if sel == "title":
                meta["title"] = el.text.strip()
            else:
                val = el.attrib.get("content", "").strip()
                if val:
                    meta["title"] = val
            if "title" in meta:
                break

    for sel in ['meta[name="description"]', 'meta[property="og:description"]',
                'meta[name="citation_abstract"]']:
        el = _first(page, sel)
        if el:
            val = el.attrib.get("content", "").strip()
            if val:
                meta["abstract"] = val
                break

    author_tags = page.css('meta[name="citation_author"]')
    if author_tags and len(author_tags) > 0:
        meta["authors"] = [t.attrib.get("content", "").strip() for t in author_tags]

    doi_tag = _first(page, 'meta[name="citation_doi"]')
    if doi_tag:
        meta["doi"] = doi_tag.attrib.get("content", "").strip()

    date_tag = _first(page, 'meta[name="citation_date"]')
    if date_tag is None:
        date_tag = _first(page, 'meta[name="citation_publication_date"]')
    if date_tag:
        yr = re.search(r"(\d{4})", date_tag.attrib.get("content", ""))
        if yr:
            meta["year"] = int(yr.group(1))

    return meta


# ========== Dispatcher ==========

def extract_metadata(url: str, timeout: int = 20) -> dict:
    if not _is_allowed(url):
        return {"error": f"Domain not in allow-list: {url}", "url": url}
    try:
        final_url, html = _fetch_page(url, timeout=timeout)
    except Exception as e:
        return {"error": str(e), "url": url}

    if "pubmed.ncbi.nlm.nih.gov" in final_url or "ncbi.nlm.nih.gov" in final_url:
        return _extract_pubmed(final_url, html)
    elif "arxiv.org" in final_url:
        return _extract_arxiv(final_url, html)
    else:
        return _extract_generic(final_url, html)


# ========== CLI handler ==========

def run_browse(args) -> int:
    urls = args.urls
    output_path = getattr(args, "output", None)
    json_mode = getattr(args, "json_output", False)

    results = []
    for i, url in enumerate(urls, 1):
        print(f"\n{'='*60}")
        print(f"  [{i}/{len(urls)}] Fetching: {url}")
        print(f"{'='*60}")

        start = time.time()
        meta = extract_metadata(url)
        elapsed = time.time() - start

        results.append(meta)

        if "error" in meta:
            print(f"  Error: {meta['error']}")
            continue

        if json_mode:
            print(json.dumps(meta, ensure_ascii=False, indent=2))
        else:
            print(f"  Source  : {meta.get('source', '?')}")
            if meta.get("pmid"):
                print(f"  PMID    : {meta['pmid']}")
            if meta.get("arxiv_id"):
                print(f"  arXiv ID: {meta['arxiv_id']}")
            print(f"  Title   : {meta.get('title', '(none)')}")
            authors = meta.get("authors", [])
            if authors:
                display = ", ".join(authors[:5])
                if len(authors) > 5:
                    display += f" ... (+{len(authors)-5})"
                print(f"  Authors : {display}")
            if meta.get("journal"):
                print(f"  Journal : {meta['journal']}")
            if meta.get("year"):
                print(f"  Year    : {meta['year']}")
            if meta.get("doi"):
                print(f"  DOI     : {meta['doi']}")
            if meta.get("categories"):
                print(f"  Category: {meta['categories']}")
            abstract = meta.get("abstract", "")
            if abstract:
                snippet = abstract[:200] + ("..." if len(abstract) > 200 else "")
                print(f"  Abstract: {snippet}")
            print(f"  (fetched in {elapsed:.2f}s)")

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nSaved {len(results)} results to {out}")

    print(f"\nDone: {len(results)} URL(s) processed.")
    return 0
