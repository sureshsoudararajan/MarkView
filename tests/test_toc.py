# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Suresh Soundararajan

"""Tests for the Table of Contents module."""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from markview.toc import TocEntry, TableOfContents


class TestTocEntry(unittest.TestCase):
    """Test TocEntry data model."""

    def test_create_entry(self):
        entry = TocEntry(title="Hello", anchor_id="hello", level=1)
        self.assertEqual(entry.title, "Hello")
        self.assertEqual(entry.anchor_id, "hello")
        self.assertEqual(entry.level, 1)

    def test_add_child(self):
        parent = TocEntry(title="Parent", anchor_id="parent", level=1)
        child = TocEntry(title="Child", anchor_id="child", level=2)
        parent.add_child(child)
        self.assertEqual(parent.children.get_n_items(), 1)


class TestTableOfContents(unittest.TestCase):
    """Test TOC extraction and building."""

    def setUp(self):
        self.toc = TableOfContents()

    def test_build_from_empty_tokens(self):
        self.toc.build_from_toc_tokens([])
        self.assertFalse(self.toc.has_entries)

    def test_build_from_simple_tokens(self):
        tokens = [
            {'level': 1, 'id': 'heading-1', 'name': 'Heading 1', 'children': []},
            {'level': 1, 'id': 'heading-2', 'name': 'Heading 2', 'children': []},
        ]
        self.toc.build_from_toc_tokens(tokens)
        self.assertTrue(self.toc.has_entries)

    def test_build_from_nested_tokens(self):
        tokens = [
            {
                'level': 1,
                'id': 'main',
                'name': 'Main',
                'children': [
                    {'level': 2, 'id': 'sub-1', 'name': 'Sub 1', 'children': []},
                    {'level': 2, 'id': 'sub-2', 'name': 'Sub 2', 'children': []},
                ],
            },
        ]
        self.toc.build_from_toc_tokens(tokens)
        self.assertTrue(self.toc.has_entries)

    def test_clear(self):
        tokens = [
            {'level': 1, 'id': 'heading', 'name': 'Heading', 'children': []},
        ]
        self.toc.build_from_toc_tokens(tokens)
        self.assertTrue(self.toc.has_entries)
        self.toc.clear()
        self.assertFalse(self.toc.has_entries)

    def test_duplicate_headings(self):
        tokens = [
            {'level': 1, 'id': 'heading', 'name': 'Heading', 'children': []},
            {'level': 1, 'id': 'heading-1', 'name': 'Heading', 'children': []},
        ]
        self.toc.build_from_toc_tokens(tokens)
        self.assertTrue(self.toc.has_entries)


if __name__ == '__main__':
    unittest.main()
