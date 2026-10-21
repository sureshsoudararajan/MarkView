# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Suresh Soundararajan

"""Tests for MarkView utility functions."""

import sys
import os
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from markview.utils import (
    is_markdown_file,
    read_markdown_file,
    get_document_title,
    get_document_dir,
    validate_local_path,
    validate_external_url,
    is_dangerous_url,
    is_local_markdown_link,
    get_file_filter_patterns,
)


class TestMarkdownFileDetection(unittest.TestCase):
    """Test Markdown file extension detection."""

    def test_md_extension(self):
        self.assertTrue(is_markdown_file("file.md"))

    def test_markdown_extension(self):
        self.assertTrue(is_markdown_file("file.markdown"))

    def test_mdown_extension(self):
        self.assertTrue(is_markdown_file("file.mdown"))

    def test_mkd_extension(self):
        self.assertTrue(is_markdown_file("file.mkd"))

    def test_mdx_extension(self):
        self.assertTrue(is_markdown_file("file.mdx"))

    def test_uppercase_extension(self):
        self.assertTrue(is_markdown_file("file.MD"))

    def test_non_markdown_extension(self):
        self.assertFalse(is_markdown_file("file.txt"))
        self.assertFalse(is_markdown_file("file.py"))
        self.assertFalse(is_markdown_file("file.html"))

    def test_no_extension(self):
        self.assertFalse(is_markdown_file("README"))

    def test_path_with_spaces(self):
        self.assertTrue(is_markdown_file("/path/to/my file.md"))

    def test_unicode_filename(self):
        self.assertTrue(is_markdown_file("/path/to/文档.md"))


class TestFileReading(unittest.TestCase):
    """Test Markdown file reading."""

    def test_read_utf8_file(self):
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False, encoding='utf-8'
        ) as f:
            f.write("# Hello World\n\nTest content")
            f.flush()
            content = read_markdown_file(f.name)
            self.assertIn("Hello World", content)
        os.unlink(f.name)

    def test_read_nonexistent_file(self):
        result = read_markdown_file("/nonexistent/path/file.md")
        self.assertIsNone(result)

    def test_read_unicode_content(self):
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False, encoding='utf-8'
        ) as f:
            f.write("# 你好世界\n\nTest: 日本語 🚀")
            f.flush()
            content = read_markdown_file(f.name)
            self.assertIn("你好世界", content)
            self.assertIn("🚀", content)
        os.unlink(f.name)


class TestDocumentInfo(unittest.TestCase):
    """Test document title and directory extraction."""

    def test_get_title(self):
        self.assertEqual(get_document_title("/path/to/README.md"), "README")

    def test_get_title_with_spaces(self):
        self.assertEqual(
            get_document_title("/path/to/My Document.md"), "My Document"
        )

    def test_get_dir(self):
        doc_dir = get_document_dir("/path/to/file.md")
        self.assertTrue(doc_dir.endswith("/path/to") or "path" in doc_dir)


class TestPathValidation(unittest.TestCase):
    """Test path validation and traversal prevention."""

    def test_valid_relative_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "image.png"
            test_file.touch()
            result = validate_local_path(tmpdir, "image.png")
            self.assertIsNotNone(result)

    def test_path_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validate_local_path(tmpdir, "../../etc/passwd")
            self.assertIsNone(result)

    def test_absolute_path_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validate_local_path(tmpdir, "/etc/passwd")
            self.assertIsNone(result)

    def test_dot_dot_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validate_local_path(tmpdir, "../../../etc/shadow")
            self.assertIsNone(result)


class TestURLValidation(unittest.TestCase):
    """Test URL validation."""

    def test_valid_http(self):
        self.assertTrue(validate_external_url("https://example.com"))

    def test_valid_mailto(self):
        self.assertTrue(validate_external_url("mailto:user@example.com"))

    def test_dangerous_javascript(self):
        self.assertTrue(is_dangerous_url("javascript:alert(1)"))

    def test_dangerous_vbscript(self):
        self.assertTrue(is_dangerous_url("vbscript:msgbox(1)"))

    def test_safe_https(self):
        self.assertFalse(is_dangerous_url("https://example.com"))

    def test_local_markdown_link(self):
        self.assertTrue(is_local_markdown_link("./other.md"))

    def test_local_markdown_link_relative(self):
        self.assertTrue(is_local_markdown_link("docs/file.markdown"))

    def test_not_markdown_link(self):
        self.assertFalse(is_local_markdown_link("https://example.com/page"))


class TestFileFilters(unittest.TestCase):
    """Test file filter pattern generation."""

    def test_patterns_generated(self):
        patterns = get_file_filter_patterns()
        self.assertTrue(len(patterns) > 0)
        self.assertIn("*.md", patterns)


if __name__ == '__main__':
    unittest.main()
