"""jarvis zotero-sync - Sync papers to Zotero library (T3-3).

Based on: https://github.com/kaneko-ai/zotero-doi-importer
Uses pyzotero to register papers by DOI.
"""

from __future__ import annotations

import json
import os
import sys
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
        print("  Example .env:")
        print("    ZOTERO_API_KEY=your_key_here")
        print("    ZOTERO_USER_ID=your_id_here")
        return None

    try:
        from pyzotero import zotero
    except ImportError:
        print("  Error: pyzotero is not installed.")
        print("  Run: pip install pyzotero")
        return None

    return zotero.Zotero(user_id, "user", api_key)


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

    # Connect to Zotero
    zot = _get_zotero_client()
    if zot is None:
        return 1

    # Test connection
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

        # If no DOI, try Crossref lookup
        if not doi:
            print(f"    DOI not found, searching Crossref...")
            doi = _get_doi_from_crossref(title)
            if doi:
                print(f"    Found DOI: {doi}")
            else:
                print(f"    Skip: No DOI available")
                skipped += 1
                continue

        # Register in Zotero
        try:
            zot.create_items_from_dois([doi])
            print(f"    Registered: {doi}")
            registered += 1
        except Exception as e:
            error_msg = str(e)
            if "400" in error_msg or "already" in error_msg.lower():
                print(f"    Already exists or invalid DOI: {doi}")
                skipped += 1
            else:
                print(f"    Failed: {e}")
                failed += 1

        # Rate limit: 1 request per second
        time.sleep(1)

    print()
    print(f"  Results: {registered} registered, {skipped} skipped, {failed} failed")
    print(f"  Total: {len(papers)} papers")

    return 0
