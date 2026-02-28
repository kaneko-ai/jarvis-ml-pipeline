"""jarvis zotero-sync - Sync papers to Zotero library (T3-3).

Based on: https://github.com/kaneko-ai/zotero-doi-importer
Uses pyzotero to register papers by DOI via create_items().
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path


def _get_zotero_client():
    """Create a pyzotero client from .env settings."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    api_key = os.getenv("ZOTERO_API_KEY")
    user_id = os.getenv("ZOTERO_USER_ID")

    if not api_key or not user_id:
        print("  Error: ZOTERO_API_KEY and ZOTERO_USER_ID must be set in .env")
        return None

    try:
        from pyzotero import zotero
    except ImportError:
        print("  Error: pyzotero is not installed. Run: pip install pyzotero")
        return None

    return zotero.Zotero(user_id, "user", api_key)


def _get_crossref_metadata(doi: str) -> dict | None:
    """Fetch paper metadata from Crossref by DOI."""
    import requests
    try:
        url = f"https://api.crossref.org/works/{doi}"
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        return resp.json().get("message", {})
    except Exception:
        return None


def _get_doi_from_crossref(title: str) -> str | None:
    """Look up DOI from Crossref by paper title."""
    import requests
    try:
        url = f"https://api.crossref.org/works?query.bibliographic={title}&rows=1"
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        items = resp.json().get("message", {}).get("items", [])
        if not items:
            return None
        return items[0].get("DOI")
    except Exception:
        return None


def _build_zotero_item(zot, doi: str, meta: dict | None = None) -> dict:
    """Build a Zotero journal article item from DOI and Crossref metadata."""
    template = zot.item_template("journalArticle")

    template["DOI"] = doi
    template["url"] = f"https://doi.org/{doi}"

    if meta:
        # Title
        titles = meta.get("title", [])
        if titles:
            template["title"] = titles[0]

        # Authors
        authors = meta.get("author", [])
        creators = []
        for a in authors[:20]:
            creators.append({
                "creatorType": "author",
                "firstName": a.get("given", ""),
                "lastName": a.get("family", ""),
            })
        if creators:
            template["creators"] = creators

        # Journal
        container = meta.get("container-title", [])
        if container:
            template["publicationTitle"] = container[0]

        # Year / Date
        issued = meta.get("issued", {})
        date_parts = issued.get("date-parts", [[]])
        if date_parts and date_parts[0]:
            parts = date_parts[0]
            if len(parts) >= 1:
                template["date"] = str(parts[0])
            if len(parts) >= 2:
                template["date"] = f"{parts[0]}-{parts[1]:02d}"
            if len(parts) >= 3:
                template["date"] = f"{parts[0]}-{parts[1]:02d}-{parts[2]:02d}"

        # Volume, Issue, Pages
        template["volume"] = meta.get("volume", "")
        template["issue"] = meta.get("issue", "")
        template["pages"] = meta.get("page", "")

        # Abstract
        abstract = meta.get("abstract", "")
        if abstract:
            template["abstractNote"] = abstract

        # ISSN
        issn = meta.get("ISSN", [])
        if issn:
            template["ISSN"] = issn[0]

    return template


def run_zotero_sync(args) -> int:
    """Sync papers from a JSON file to Zotero."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"  Error: File not found: {input_path}")
        return 1

    with open(input_path, encoding="utf-8") as f:
        papers = json.load(f)

    if not papers:
        print("  Error: No papers in file.")
        return 1

    print(f"  Zotero Sync: {input_path.name} ({len(papers)} papers)")
    print()

    zot = _get_zotero_client()
    if zot is None:
        return 1

    try:
        zot.key_info()
        print("  Zotero connection: OK")
    except Exception as e:
        print(f"  Error: Cannot connect to Zotero API: {e}")
        return 1

    print()

    registered = 0
    skipped = 0
    failed = 0

    for i, paper in enumerate(papers, 1):
        title = paper.get("title", "Unknown")
        doi = paper.get("doi") or paper.get("DOI")

        print(f"  [{i}/{len(papers)}] {title[:60]}...")

        # If no DOI, try Crossref lookup by title
        if not doi:
            print(f"    DOI not found, searching Crossref...")
            doi = _get_doi_from_crossref(title)
            if doi:
                print(f"    Found DOI: {doi}")
            else:
                print(f"    Skip: No DOI available")
                skipped += 1
                continue

        # Get metadata from Crossref
        print(f"    Fetching metadata for DOI: {doi}")
        meta = _get_crossref_metadata(doi)

        # Build Zotero item and register
        try:
            item = _build_zotero_item(zot, doi, meta)
            resp = zot.create_items([item])

            # Check response
            if isinstance(resp, dict):
                success_keys = resp.get("successful", resp.get("success", {}))
                failed_keys = resp.get("failed", {})
                unchanged = resp.get("unchanged", {})

                if success_keys:
                    print(f"    Registered: {doi}")
                    registered += 1
                elif unchanged:
                    print(f"    Already exists: {doi}")
                    skipped += 1
                elif failed_keys:
                    reason = str(failed_keys)
                    print(f"    Failed: {reason[:80]}")
                    failed += 1
                else:
                    print(f"    Registered (response: {str(resp)[:60]})")
                    registered += 1
            else:
                print(f"    Registered: {doi}")
                registered += 1

        except Exception as e:
            print(f"    Failed: {e}")
            failed += 1

        time.sleep(1)

    print()
    print(f"  Results: {registered} registered, {skipped} skipped, {failed} failed")
    print(f"  Total: {len(papers)} papers")

    return 0
