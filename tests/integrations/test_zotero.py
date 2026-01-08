"""Tests for Zotero Integration."""

from jarvis_core.integrations.zotero import ZoteroClient, ZoteroConfig


def test_zotero_config():
    config = ZoteroConfig(
        api_key="test_key",
        user_id="12345",
        library_type="user",
    )

    assert config.api_key == "test_key"
    assert config.user_id == "12345"
    assert config.library_type == "user"


def test_zotero_library_url_user():
    config = ZoteroConfig(api_key="key", user_id="123", library_type="user")
    client = ZoteroClient(config)

    assert "/users/123" in client._get_library_url()


def test_zotero_library_url_group():
    config = ZoteroConfig(api_key="key", user_id="456", library_type="group")
    client = ZoteroClient(config)

    assert "/groups/456" in client._get_library_url()


def test_item_to_paper_conversion():
    config = ZoteroConfig(api_key="key", user_id="123")
    client = ZoteroClient(config)

    zotero_item = {
        "key": "ABC123",
        "data": {
            "title": "Test Paper",
            "creators": [
                {"lastName": "Smith"},
                {"lastName": "Jones"},
            ],
            "abstractNote": "Test abstract",
            "DOI": "10.1234/test",
            "date": "2023-01-15",
            "publicationTitle": "Test Journal",
        }
    }

    paper = client.item_to_paper(zotero_item)

    assert paper["id"] == "ABC123"
    assert paper["title"] == "Test Paper"
    assert "Smith" in paper["authors"]
    assert paper["doi"] == "10.1234/test"
    assert paper["year"] == "2023"


def test_paper_to_item_conversion():
    config = ZoteroConfig(api_key="key", user_id="123")
    client = ZoteroClient(config)

    paper = {
        "title": "My Paper",
        "authors": ["John Doe", "Jane Smith"],
        "abstract": "Paper abstract",
        "doi": "10.5555/test",
        "year": 2024,
        "journal": "Science Journal",
    }

    item = client.paper_to_item(paper)

    assert item["itemType"] == "journalArticle"
    assert item["title"] == "My Paper"
    assert len(item["creators"]) == 2
    assert item["DOI"] == "10.5555/test"
