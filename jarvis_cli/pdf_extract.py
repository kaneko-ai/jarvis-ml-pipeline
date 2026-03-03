"""CLI handler for pdf-extract command."""
from __future__ import annotations

import time
from pathlib import Path


def run_pdf_extract(args) -> int:
    """Convert PDF to Markdown via MinerU API or PyMuPDF fallback."""
    pdf_path = args.input
    mode = args.mode
    output_format = args.format

    if not Path(pdf_path).exists():
        print(f"  Error: File not found: {pdf_path}")
        return 1

    print(f"  PDF: {pdf_path}")
    print(f"  Mode: {mode} | Format: {output_format}")
    print(f"  Converting...")

    try:
        from jarvis_core.pdf.mineru_client import MinerUClient

        client = MinerUClient()
        start = time.time()
        result = client.convert_pdf(pdf_path, mode=mode, output_format=output_format)
        elapsed = time.time() - start

        text = result.get("text", "")
        engine = result.get("engine", "unknown")
        metadata = result.get("metadata", {})

        if not text or len(text.strip()) < 10:
            print(f"  Error: No content extracted from PDF.")
            return 1

        # Save output
        if args.output:
            out_path = args.output
        else:
            ext_map = {"markdown": ".md", "html": ".html", "json": ".json", "chunks": ".json"}
            ext = ext_map.get(output_format, ".md")
            out_path = str(Path(pdf_path).with_suffix(ext))

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"  Engine: {engine}")
        print(f"  Conversion completed in {elapsed:.1f}s")
        print(f"  Output: {out_path}")
        print(f"  Markdown length: {len(text):,} chars")

        # Show metadata if available
        if isinstance(metadata, dict) and metadata:
            title = metadata.get("title", "")
            pages = metadata.get("pages", "")
            if title:
                print(f"  Title: {title}")
            if pages:
                print(f"  Pages: {pages}")

        # Preview
        preview = text[:500].replace("\n", " ")
        print(f"\n  Preview (first 500 chars):")
        print(f"  {preview}")

        return 0

    except Exception as e:
        print(f"  Error during conversion: {e}")
        return 1
