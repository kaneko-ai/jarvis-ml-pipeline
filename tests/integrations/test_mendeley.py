"""Tests for Mendeley Integration."""

from jarvis_core.integrations.mendeley import MendeleyClient, MendeleyConfig


def test_mendeley_config():
    config = MendeleyConfig(access_token="test_token")
    assert config.access_token == "test_token"


def test_document_to_paper_conversion():
    config = MendeleyConfig(access_token="token")
    client = MendeleyClient(config)

    mendeley_doc = {
        "id": "doc123",
        "title": "Test Document",
        "authors": [
            {"first_name": "John", "last_name": "Smith"},
            {"first_name": "Jane", "last_name": "Doe"},
        ],
        "abstract": "Test abstract",
        "identifiers": {"doi": "10.1234/test"},
        "year": 2023,
        "source": "Test Journal",
    }

    paper = client.document_to_paper(mendeley_doc)

    assert paper["id"] == "doc123"
    assert paper["title"] == "Test Document"
    assert len(paper["authors"]) == 2
    assert paper["doi"] == "10.1234/test"
    assert paper["year"] == 2023


def test_paper_to_document_conversion():
    config = MendeleyConfig(access_token="token")
    client = MendeleyClient(config)

    paper = {
        "title": "My Paper",
        "authors": ["John Smith", "Jane Doe"],
        "abstract": "Paper abstract",
        "doi": "10.5555/test",
        "year": 2024,
        "journal": "Science Journal",
    }

    doc = client.paper_to_document(paper)

    assert doc["type"] == "journal"
    assert doc["title"] == "My Paper"
    assert len(doc["authors"]) == 2
    assert doc["identifiers"]["doi"] == "10.5555/test"
