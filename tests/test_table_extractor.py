import pytest


@pytest.mark.core
def test_table_extractor_html():
    BeautifulSoup = pytest.importorskip("bs4").BeautifulSoup
    from jarvis_core.ingestion.table_extractor import extract_tables

    html = """
    <table>
      <caption>Table 1</caption>
      <tr><th>A</th><th>B</th></tr>
      <tr><td>1</td><td>2</td></tr>
    </table>
    """
    tables = extract_tables(html)

    assert tables
    assert tables[0].headers == ["A", "B"]
    assert tables[0].rows == [["1", "2"]]
    assert tables[0].caption == "Table 1"
