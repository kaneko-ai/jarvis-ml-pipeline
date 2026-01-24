import pytest
from jarvis_core.ranking.features import RankingFeatures

def test_feature_extraction_basics():
    extractor = RankingFeatures()
    
    query = "immunotherapy cancer"
    doc = {
        "title": "Advances in cancer immunotherapy",
        "text": "This study explores immunotherapy options.",
        "year": 2023,
        "bm25_score": 12.5
    }
    
    feats = extractor.extract(query, doc)
    
    # Check string match features
    # "immunotherapy cancer" are both in title (case insensitive)
    # Our simple extractor checks if the full query string is in title
    # "immunotherapy cancer" is NOT in "Advances in cancer immunotherapy" as a substring
    assert feats["title_match"] == 0.0 
    
    # Check loose match components if we had them, but here we test exact behavior
    
    assert feats["query_len"] == 2
    assert feats["year"] == 2023.0
    assert feats["bm25_score"] == 12.5
    assert feats["has_doi"] == 0.0

def test_feature_extraction_exact_match():
    extractor = RankingFeatures()
    query = "specific phrase"
    doc = {"title": "A specific phrase title", "text": "body content"}
    
    feats = extractor.extract(query, doc)
    assert feats["title_match"] == 1.0

def test_feature_extraction_vector():
    extractor = RankingFeatures()
    query = "test"
    doc = {"title": "test doc"}
    
    # Mock vectors [1, 0] and [0, 1] -> dot product 0
    import numpy as np
    q_vec = np.array([1.0, 0.0])
    d_vec = np.array([0.0, 1.0])
    
    feats = extractor.extract(query, doc, query_vec=q_vec, doc_vec=d_vec)
    assert feats["cosine_sim"] == 0.0
    
    # Same vector -> dot product 1 (if normalized)
    feats2 = extractor.extract(query, doc, query_vec=q_vec, doc_vec=q_vec)
    assert feats2["cosine_sim"] == 1.0
