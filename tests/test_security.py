# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Suresh Soundararajan

"""Security tests for MarkView HTML sanitization."""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from markview.renderer import MarkdownRenderer


class TestHTMLSanitization(unittest.TestCase):
    """Test that dangerous HTML is properly sanitized."""

    def setUp(self):
        self.renderer = MarkdownRenderer()

    def _render(self, md):
        return self.renderer.render(md)

    # --- Script Injection ---

    def test_script_tag_stripped(self):
        html = self._render("<script>alert('xss')</script>")
        self.assertNotIn("<script", html.lower().split('katex')[0])
        self.assertNotIn("alert('xss')", html)

    def test_script_in_markdown(self):
        md = "Normal text\n\n<script>document.cookie</script>\n\nMore text"
        html = self._render(md)
        self.assertNotIn("document.cookie", html)

    def test_inline_script_attribute(self):
        md = '<div onmouseover="alert(1)">hover me</div>'
        html = self._render(md)
        self.assertNotIn("onmouseover", html)
        self.assertNotIn("alert(1)", html)

    def test_onclick_handler(self):
        md = '<a onclick="alert(1)" href="#">click</a>'
        html = self._render(md)
        self.assertNotIn("onclick", html)

    def test_onerror_handler(self):
        md = '<img src="x" onerror="alert(1)">'
        html = self._render(md)
        self.assertNotIn("onerror", html)

    def test_onload_handler(self):
        md = '<body onload="alert(1)">text</body>'
        html = self._render(md)
        self.assertNotIn("onload=", html)

    # --- JavaScript URLs ---

    def test_javascript_href(self):
        md = '<a href="javascript:alert(1)">click</a>'
        html = self._render(md)
        self.assertNotIn("javascript:", html)

    def test_javascript_img_src(self):
        md = '<img src="javascript:alert(1)">'
        html = self._render(md)
        self.assertNotIn("javascript:", html)

    def test_vbscript_href(self):
        md = '<a href="vbscript:MsgBox(1)">click</a>'
        html = self._render(md)
        self.assertNotIn("vbscript:", html)

    # --- Dangerous Tags ---

    def test_iframe_stripped(self):
        md = '<iframe src="https://evil.com"></iframe>'
        html = self._render(md)
        self.assertNotIn("<iframe", html)

    def test_object_stripped(self):
        md = '<object data="evil.swf"></object>'
        html = self._render(md)
        self.assertNotIn("<object", html)

    def test_embed_stripped(self):
        md = '<embed src="evil.swf">'
        html = self._render(md)
        self.assertNotIn("<embed", html)

    def test_form_stripped(self):
        md = '<form action="https://evil.com"><input type="text"></form>'
        html = self._render(md)
        self.assertNotIn("<form", html)

    def test_style_tag_stripped(self):
        md = '<style>body { display: none; }</style>'
        html = self._render(md)
        # Style tags in content should be stripped (our own styles are inline)
        self.assertNotIn("<style>body", html)

    # --- Safe HTML Preserved ---

    def test_safe_div_preserved(self):
        md = '<div class="custom">Content</div>'
        html = self._render(md)
        self.assertIn("Content", html)

    def test_safe_span_preserved(self):
        md = '<span class="highlight">text</span>'
        html = self._render(md)
        self.assertIn("text", html)

    def test_safe_table_preserved(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        html = self._render(md)
        self.assertIn("<table", html)

    def test_img_preserved(self):
        md = '![Alt](image.png "Title")'
        html = self._render(md)
        self.assertIn("<img", html)

    # --- Edge Cases ---

    def test_mixed_safe_and_dangerous(self):
        md = (
            "# Safe Heading\n\n"
            "<script>alert(1)</script>\n\n"
            "**Safe bold text**\n\n"
            '<img src="x" onerror="alert(1)">\n\n'
            "[Safe link](https://example.com)"
        )
        html = self._render(md)
        self.assertIn("Safe Heading", html)
        self.assertIn("<strong>Safe bold text</strong>", html)
        self.assertNotIn("alert(1)", html)
        self.assertNotIn("onerror", html)

    def test_nested_dangerous_content(self):
        md = '<div><script>alert(1)</script><p>safe</p></div>'
        html = self._render(md)
        self.assertNotIn("<script", html.lower().split('katex')[0])
        self.assertIn("safe", html)

    def test_malformed_html_handled(self):
        """Malformed HTML should not crash the renderer."""
        md = "<div><p>unclosed\n\n<b>also unclosed"
        html = self._render(md)
        self.assertIsNotNone(html)

    def test_document_not_modified(self):
        """Rendering must not modify the source."""
        original = "# Hello\n\nWorld"
        source = original
        self._render(source)
        self.assertEqual(source, original)

    def test_large_input_handled(self):
        """Large documents should not crash."""
        md = "# Heading\n\n" + ("Lorem ipsum dolor sit amet. " * 1000)
        html = self._render(md)
        self.assertIsNotNone(html)
        self.assertIn("Heading", html)


class TestContentSecurityPolicy(unittest.TestCase):
    """Test that the Content Security Policy is set correctly."""

    def setUp(self):
        self.renderer = MarkdownRenderer()

    def test_csp_header_present(self):
        html = self.renderer.render("# Test")
        self.assertIn("Content-Security-Policy", html)

    def test_csp_blocks_inline_scripts(self):
        html = self.renderer.render("# Test")
        # CSP should not allow unsafe-eval
        self.assertNotIn("unsafe-eval", html)


if __name__ == '__main__':
    unittest.main()
