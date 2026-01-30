from jarvis_core.retrieval.expansion import QueryExpander


def test_keyword_expansion():
    expander = QueryExpander()

    # Test known heuristic
    query = "AI in cancer treatment"
    expanded = expander.expand(query, method="keyword")

    assert "neoplasm" in expanded or "tumor" in expanded or "artificial intelligence" in expanded
    assert query in expanded


def test_hyde_expansion():
    expander = QueryExpander()
    query = "immunotherapy side effects"

    expanded = expander.expand(query, method="hyde")

    # Needs to return original + hypo document
    assert len(expanded) == 2
    assert query in expanded
    assert "Hypothetical abstract" in expanded[1]


def test_unknown_method():
    expander = QueryExpander()
    query = "test"
    expanded = expander.expand(query, method="magic")
    assert len(expanded) == 1
    assert expanded[0] == query