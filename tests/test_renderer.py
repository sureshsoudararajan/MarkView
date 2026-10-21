# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Suresh Soundararajan

"""Tests for the MarkView Markdown rendering engine."""

import sys
import os
import unittest

# Add source to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from markview.renderer import MarkdownRenderer, GitHubAlertPreprocessor


class TestMarkdownRendering(unittest.TestCase):
    """Test Markdown rendering output."""

    def setUp(self):
        self.renderer = MarkdownRenderer()

    def _render_body(self, markdown_source, dark=False):
        """Render Markdown and return just the body HTML (not full page)."""
        html = self.renderer.render(markdown_source, dark_theme=dark)
        return html

    # --- Headings ---

    def test_heading_h1(self):
        html = self._render_body("# Heading 1")
        self.assertIn("<h1", html)
        self.assertIn("Heading 1", html)

    def test_heading_h2(self):
        html = self._render_body("## Heading 2")
        self.assertIn("<h2", html)

    def test_heading_h3(self):
        html = self._render_body("### Heading 3")
        self.assertIn("<h3", html)

    def test_heading_h4(self):
        html = self._render_body("#### Heading 4")
        self.assertIn("<h4", html)

    def test_heading_h5(self):
        html = self._render_body("##### Heading 5")
        self.assertIn("<h5", html)

    def test_heading_h6(self):
        html = self._render_body("###### Heading 6")
        self.assertIn("<h6", html)

    def test_heading_ids_generated(self):
        html = self._render_body("# My Test Heading")
        self.assertIn('id="', html)

    # --- Inline Formatting ---

    def test_bold(self):
        html = self._render_body("This is **bold** text")
        self.assertIn("<strong>bold</strong>", html)

    def test_italic(self):
        html = self._render_body("This is *italic* text")
        self.assertIn("<em>italic</em>", html)

    def test_bold_italic(self):
        html = self._render_body("This is ***bold italic*** text")
        self.assertIn("<strong>", html)
        self.assertIn("<em>", html)

    def test_strikethrough(self):
        html = self._render_body("This is ~~deleted~~ text")
        self.assertIn("<del>deleted</del>", html)

    def test_inline_code(self):
        html = self._render_body("Use `print()` function")
        self.assertIn("<code>print()</code>", html)

    # --- Code Blocks ---

    def test_fenced_code_block(self):
        md = '```python\nprint("hello")\n```'
        html = self._render_body(md)
        self.assertIn("print", html)
        self.assertIn("highlight", html.lower())

    def test_code_block_unknown_language(self):
        """Unknown languages should render without error."""
        md = '```unknownlang\nsome code here\n```'
        html = self._render_body(md)
        self.assertIn("some code here", html)

    def test_code_block_no_language(self):
        md = '```\nplain code\n```'
        html = self._render_body(md)
        self.assertIn("plain code", html)

    # --- Tables ---

    def test_simple_table(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        html = self._render_body(md)
        self.assertIn("<table", html)
        self.assertIn("<th", html)
        self.assertIn("<td", html)

    def test_table_alignment(self):
        md = "| Left | Center | Right |\n|:-----|:------:|------:|\n| L | C | R |"
        html = self._render_body(md)
        self.assertIn("<table", html)

    # --- Lists ---

    def test_unordered_list(self):
        md = "- Item 1\n- Item 2\n- Item 3"
        html = self._render_body(md)
        self.assertIn("<ul>", html)
        self.assertIn("<li>", html)

    def test_ordered_list(self):
        md = "1. First\n2. Second\n3. Third"
        html = self._render_body(md)
        self.assertIn("<ol>", html)

    def test_nested_list(self):
        md = "- Item 1\n  - Nested 1\n  - Nested 2\n- Item 2"
        html = self._render_body(md)
        self.assertIn("<ul>", html)

    def test_task_list(self):
        md = "- [x] Done\n- [ ] Not done"
        html = self._render_body(md)
        self.assertIn("checkbox", html.lower())

    # --- Blockquotes ---

    def test_blockquote(self):
        md = "> This is a quote"
        html = self._render_body(md)
        self.assertIn("<blockquote>", html)

    def test_nested_blockquote(self):
        md = "> Level 1\n>> Level 2\n>>> Level 3"
        html = self._render_body(md)
        self.assertIn("<blockquote>", html)

    # --- Links ---

    def test_link(self):
        md = "[Click here](https://example.com)"
        html = self._render_body(md)
        self.assertIn('href="https://example.com"', html)
        self.assertIn("Click here", html)

    def test_link_with_title(self):
        md = '[Link](https://example.com "Title")'
        html = self._render_body(md)
        self.assertIn("example.com", html)

    # --- Images ---

    def test_image(self):
        md = "![Alt text](image.png)"
        html = self._render_body(md)
        self.assertIn("<img", html)
        self.assertIn('alt="Alt text"', html)

    # --- Horizontal Rule ---

    def test_horizontal_rule(self):
        md = "---"
        html = self._render_body(md)
        self.assertIn("<hr", html)

    # --- GitHub Alerts ---

    def test_alert_note(self):
        md = "> [!NOTE]\n> This is a note"
        html = self._render_body(md)
        self.assertIn("admonition", html)
        self.assertIn("note", html.lower())

    def test_alert_warning(self):
        md = "> [!WARNING]\n> This is a warning"
        html = self._render_body(md)
        self.assertIn("admonition", html)
        self.assertIn("warning", html.lower())

    def test_alert_tip(self):
        md = "> [!TIP]\n> This is a tip"
        html = self._render_body(md)
        self.assertIn("admonition", html)
        self.assertIn("tip", html.lower())

    def test_alert_important(self):
        md = "> [!IMPORTANT]\n> This is important"
        html = self._render_body(md)
        self.assertIn("admonition", html)
        self.assertIn("important", html.lower())

    def test_alert_caution(self):
        md = "> [!CAUTION]\n> This is a caution"
        html = self._render_body(md)
        self.assertIn("admonition", html)
        self.assertIn("caution", html.lower())

    # --- Footnotes ---

    def test_footnotes(self):
        md = "Text with a footnote[^1].\n\n[^1]: Footnote content."
        html = self._render_body(md)
        self.assertIn("footnote", html.lower())

    # --- Math ---

    def test_math_inline(self):
        md = "Inline math: $E = mc^2$"
        html = self._render_body(md)
        # arithmatex wraps in a span/div with arithmatex class
        self.assertIn("arithmatex", html)

    def test_math_display(self):
        md = "$$\n\\int_0^\\infty e^{-x} dx = 1\n$$"
        html = self._render_body(md)
        self.assertIn("arithmatex", html)

    # --- Mermaid ---

    def test_mermaid_block(self):
        md = '```mermaid\ngraph TD\n    A --> B\n```'
        html = self._render_body(md)
        self.assertIn('class="mermaid"', html)
        self.assertIn("graph TD", html)

    # --- Miscellaneous ---

    def test_empty_document(self):
        html = self._render_body("")
        self.assertIn("<!DOCTYPE html>", html)

    def test_unicode_content(self):
        md = "# 你好世界\n\nこんにちは 🚀 مرحبا"
        html = self._render_body(md)
        self.assertIn("你好世界", html)
        self.assertIn("🚀", html)

    def test_escaped_characters(self):
        md = "\\*not italic\\*"
        html = self._render_body(md)
        self.assertNotIn("<em>", html)

    def test_dark_theme(self):
        html = self._render_body("# Hello", dark=True)
        self.assertIn('class="dark"', html)

    def test_light_theme(self):
        html = self._render_body("# Hello", dark=False)
        self.assertIn('class="light"', html)


class TestGitHubAlertPreprocessor(unittest.TestCase):
    """Test the GitHub alert syntax preprocessor."""

    def setUp(self):
        self.preprocessor = GitHubAlertPreprocessor(None)

    def test_converts_note_alert(self):
        lines = ["> [!NOTE]", "> This is a note"]
        result = self.preprocessor.run(lines)
        self.assertEqual(result[0], '!!! note "Note"')
        self.assertEqual(result[1], '    This is a note')

    def test_converts_warning_alert(self):
        lines = ["> [!WARNING]", "> Be careful"]
        result = self.preprocessor.run(lines)
        self.assertEqual(result[0], '!!! warning "Warning"')

    def test_preserves_non_alert_blockquotes(self):
        lines = ["> Regular quote"]
        result = self.preprocessor.run(lines)
        self.assertEqual(result[0], "> Regular quote")

    def test_multiline_alert(self):
        lines = ["> [!TIP]", "> Line 1", "> Line 2", "", "Normal text"]
        result = self.preprocessor.run(lines)
        self.assertIn('!!! tip "Tip"', result)
        self.assertIn('    Line 1', result)
        self.assertIn('    Line 2', result)


if __name__ == '__main__':
    unittest.main()
