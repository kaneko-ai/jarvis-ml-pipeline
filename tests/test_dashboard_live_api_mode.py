from pathlib import Path


def test_live_api_search_functions_exist():
    js_path = Path(__file__).parent.parent / "docs" / "jarvis-app.js"
    text = js_path.read_text(encoding="utf-8")

    assert "async fetchPubMed(" in text
    assert "async fetchArXiv(" in text
    assert "async fetchCrossref(" in text
    assert "async fetchOpenAlex(" in text
    assert "Promise.allSettled(" in text
    assert "mockResults(" not in text
    assert "j_ncbi_key" in text


def test_index_contains_ncbi_inputs():
    html_path = Path(__file__).parent.parent / "docs" / "index.html"
    html = html_path.read_text(encoding="utf-8")

    assert 'id="ncbi-api-key"' in html
    assert 'id="ncbi-key-save"' in html
