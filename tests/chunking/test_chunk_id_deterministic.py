import pytest
from jarvis_core.chunking.engine import StandardChunker, Sectionizer

def test_chunk_id_deterministic():
    chunker = StandardChunker(chunk_size=100, overlap=0)
    text = "Paragraph one is here.\n\nParagraph two is there.\n\nParagraph three is everywhere."
    
    chunks = chunker.chunk(text, "DOC001", "Introduction")
    
    assert len(chunks) > 0
    assert chunks[0].chunk_id == "DOC001_introduction_0"
    if len(chunks) > 1:
        assert chunks[1].chunk_id == "DOC001_introduction_1"

def test_chunker_deduplication():
    chunker = StandardChunker()
    text = "Duplicate paragraph.\n\nDuplicate paragraph.\n\nUnique paragraph."
    
    chunks = chunker.chunk(text, "DOC002")
    # Both duplicates should merge/dedupe if identical
    full_text = " ".join([c.text for c in chunks])
    assert text.count("Duplicate paragraph") == 2
    assert full_text.count("Duplicate paragraph") == 1

def test_sectionizer_basic():
    sectionizer = Sectionizer()
    text = "Abstract\nThis is abstraction.\nIntroduction\nThis is intro."
    sections = sectionizer.split_by_sections(text)
    
    assert len(sections) >= 2
    assert sections[0]["name"] == "Abstract"
    assert sections[1]["name"] == "Introduction"
