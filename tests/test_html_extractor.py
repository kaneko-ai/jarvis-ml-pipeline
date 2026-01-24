"""Tests for html_extractor module."""

from jarvis_core.html_extractor import (
    extract_title,
    extract_main_text,
    _extract_text_regex,
    _normalize_text,
    REMOVE_TAGS,
)


class TestRemoveTags:
    def test_includes_common_tags(self):
        assert "script" in REMOVE_TAGS
        assert "style" in REMOVE_TAGS
        assert "nav" in REMOVE_TAGS
        assert "footer" in REMOVE_TAGS


class TestExtractTitle:
    def test_simple_title(self):
        html = "<html><head><title>Test Page</title></head><body></body></html>"

        result = extract_title(html)

        assert result == "Test Page"

    def test_no_title(self):
        html = "<html><head></head><body>Content</body></html>"

        result = extract_title(html)

        assert result is None

    def test_title_with_whitespace(self):
        html = "<html><head><title>  Spaced Title  </title></head></html>"

        result = extract_title(html)

        assert result == "Spaced Title"


class TestExtractMainText:
    def test_simple_body(self):
        html = "<html><body><p>Hello World</p></body></html>"

        result = extract_main_text(html)

        assert "Hello World" in result

    def test_removes_script(self):
        html = "<html><body><script>alert('x')</script><p>Content</p></body></html>"

        result = extract_main_text(html)

        assert "alert" not in result
        assert "Content" in result

    def test_removes_style(self):
        html = "<html><body><style>.red { color: red; }</style><p>Text</p></body></html>"

        result = extract_main_text(html)

        assert "color" not in result
        assert "Text" in result

    def test_prefers_article(self):
        html = """
        <html><body>
        <nav>Navigation</nav>
        <article>Main Article Content</article>
        <footer>Footer</footer>
        </body></html>
        """

        result = extract_main_text(html)

        assert "Main Article Content" in result

    def test_prefers_main(self):
        html = """
        <html><body>
        <header>Header</header>
        <main>Main Content Here</main>
        <aside>Sidebar</aside>
        </body></html>
        """

        result = extract_main_text(html)

        assert "Main Content Here" in result


class TestExtractTextRegex:
    def test_removes_tags(self):
        html = "<p>Hello</p><div>World</div>"

        result = _extract_text_regex(html)

        assert "<p>" not in result
        assert "Hello" in result
        assert "World" in result

    def test_removes_script_content(self):
        html = "<script>var x = 1;</script><p>Text</p>"

        result = _extract_text_regex(html)

        assert "var x" not in result
        assert "Text" in result

    def test_decodes_entities(self):
        html = "<p>A &amp; B &lt; C</p>"

        result = _extract_text_regex(html)

        assert "&" in result
        assert "<" in result


class TestNormalizeText:
    def test_collapses_spaces(self):
        text = "Hello    World"

        result = _normalize_text(text)

        assert "    " not in result
        assert "Hello World" in result

    def test_collapses_newlines(self):
        text = "Line 1\n\n\n\n\nLine 2"

        result = _normalize_text(text)

        # Multiple newlines become double newline
        assert "\n\n\n" not in result

    def test_strips_lines(self):
        text = "  Line 1  \n  Line 2  "

        result = _normalize_text(text)

        assert result == "Line 1\nLine 2"
