# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Suresh Soundararajan

"""
Markdown rendering engine for MarkView.

Converts Markdown source to a complete, styled HTML page using:
- Python-Markdown with PyMdown Extensions for GFM-compatible parsing
- Pygments for syntax highlighting
- Bleach for HTML sanitization
- Custom CSS for GitHub-inspired styling
"""

import os
import re
import html
import urllib.parse
from pathlib import Path
from typing import Optional

import bleach
import markdown
from markdown.preprocessors import Preprocessor
from markdown.extensions import Extension

from markview.utils import find_asset_dir, validate_image_path

# Bleach whitelist configuration for HTML sanitization
ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'caption', 'cite',
    'code', 'col', 'colgroup', 'dd', 'del', 'details', 'dfn', 'div', 'dl',
    'dt', 'em', 'figcaption', 'figure', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'hr', 'i', 'img', 'ins', 'kbd', 'li', 'mark', 'ol', 'p', 'picture',
    'pre', 'q', 's', 'samp', 'small', 'source', 'span', 'strong', 'sub',
    'summary', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr',
    'tt', 'u', 'ul', 'var', 'wbr', 'input',
]

ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id', 'title', 'lang', 'dir', 'role', 'aria-label',
          'aria-hidden', 'data-type'],
    'a': ['href', 'rel', 'target', 'name'],
    'abbr': ['title'],
    'acronym': ['title'],
    'col': ['span', 'width'],
    'colgroup': ['span', 'width'],
    'details': ['open'],
    'img': ['src', 'alt', 'title', 'width', 'height', 'loading'],
    'input': ['type', 'checked', 'disabled'],
    'ol': ['start', 'type', 'reversed'],
    'source': ['src', 'type', 'media', 'srcset'],
    'td': ['colspan', 'rowspan', 'align', 'valign'],
    'th': ['colspan', 'rowspan', 'align', 'valign', 'scope'],
    'table': ['align', 'border', 'cellpadding', 'cellspacing', 'width'],
}


class GitHubAlertPreprocessor(Preprocessor):
    """
    Convert GitHub-style alert syntax to Python-Markdown admonition syntax.

    Transforms:
        > [!NOTE]
        > Content here

    Into:
        !!! note "Note"
            Content here
    """

    ALERT_PATTERN = re.compile(
        r'^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$',
        re.IGNORECASE
    )

    ALERT_TITLES = {
        'note': 'Note',
        'tip': 'Tip',
        'important': 'Important',
        'warning': 'Warning',
        'caution': 'Caution',
    }

    def run(self, lines):
        new_lines = []
        i = 0
        while i < len(lines):
            match = self.ALERT_PATTERN.match(lines[i])
            if match:
                alert_type = match.group(1).lower()
                title = self.ALERT_TITLES.get(alert_type, alert_type.title())
                new_lines.append(f'!!! {alert_type} "{title}"')

                i += 1
                # Collect the blockquote content
                while i < len(lines):
                    line = lines[i]
                    if line.startswith('> '):
                        # Strip the blockquote prefix, indent for admonition
                        content = line[2:]
                        new_lines.append(f'    {content}')
                    elif line.startswith('>'):
                        # Empty blockquote line
                        content = line[1:].strip()
                        new_lines.append(f'    {content}')
                    else:
                        # End of blockquote
                        break
                    i += 1
                new_lines.append('')  # blank line after admonition
            else:
                new_lines.append(lines[i])
                i += 1

        return new_lines


class GitHubAlertExtension(Extension):
    """Markdown extension for GitHub-style alerts."""

    def extendMarkdown(self, md):
        md.preprocessors.register(
            GitHubAlertPreprocessor(md), 'github_alerts', 105
        )


def _link_sanitizer(tag, name, value):
    """Custom Bleach attribute filter to sanitize links and images."""
    if name == 'href':
        # Block javascript: and other dangerous schemes
        try:
            parsed = urllib.parse.urlparse(value)
            if parsed.scheme.lower() in ('javascript', 'vbscript', 'data'):
                return None
        except (ValueError, AttributeError):
            return None
    if name == 'src' and tag == 'img':
        # Allow file://, relative paths, and data: URIs for images
        try:
            parsed = urllib.parse.urlparse(value)
            if parsed.scheme.lower() in ('javascript', 'vbscript'):
                return None
        except (ValueError, AttributeError):
            return None
    # Allow event handlers to be stripped (done by Bleach by default)
    if name.startswith('on'):
        return None
    return value


class MarkdownRenderer:
    """
    Renders Markdown source to a complete HTML page with styling.

    Features:
    - GFM-compatible Markdown rendering
    - Syntax highlighting via Pygments
    - GitHub-style alerts
    - Math delimiters for KaTeX
    - Mermaid diagram blocks
    - HTML sanitization
    - Light and dark theme support
    """

    def __init__(self):
        self._asset_dir = find_asset_dir()
        self._css_cache = {}
        self._toc_data = []
        self._setup_markdown()

    def _setup_markdown(self):
        """Configure the Markdown processor with all extensions."""
        # Mermaid custom fence
        def _mermaid_fence(source, language, class_name, options, md, **kwargs):
            return f'<pre class="mermaid">{html.escape(source)}</pre>'

        custom_fences = [
            {
                'name': 'mermaid',
                'class': 'mermaid',
                'format': _mermaid_fence,
            }
        ]

        self._extensions = [
            'markdown.extensions.tables',
            'markdown.extensions.footnotes',
            'markdown.extensions.attr_list',
            'markdown.extensions.md_in_html',
            'markdown.extensions.sane_lists',
            'markdown.extensions.smarty',
            'markdown.extensions.admonition',
            'markdown.extensions.toc',
            'pymdownx.tasklist',
            'pymdownx.tilde',
            'pymdownx.betterem',
            'pymdownx.mark',
            'pymdownx.magiclink',
            'pymdownx.keys',
            'pymdownx.emoji',
            'pymdownx.highlight',
            'pymdownx.inlinehilite',
            'pymdownx.superfences',
            'pymdownx.arithmatex',
            GitHubAlertExtension(),
        ]

        self._extension_configs = {
            'markdown.extensions.toc': {
                'permalink': False,
                'toc_depth': '1-6',
                'slugify': self._slugify,
            },
            'pymdownx.tasklist': {
                'custom_checkbox': True,
                'clickable_checkbox': False,
            },
            'pymdownx.highlight': {
                'use_pygments': True,
                'pygments_style': 'default',
                'noclasses': False,
                'linenums': False,
                'guess_lang': False,
            },
            'pymdownx.inlinehilite': {
                'style_plain_text': False,
            },
            'pymdownx.superfences': {
                'custom_fences': custom_fences,
            },
            'pymdownx.arithmatex': {
                'generic': True,
            },
            'pymdownx.emoji': {
                'emoji_index': self._get_emoji_index(),
                'emoji_generator': self._get_emoji_generator(),
            },
        }

    @staticmethod
    def _get_emoji_index():
        """Get emoji index function."""
        try:
            from pymdownx import gemoji
            return gemoji.gemoji
        except (ImportError, AttributeError):
            try:
                from pymdownx.emoji import gemoji
                return gemoji
            except (ImportError, AttributeError):
                return None

    @staticmethod
    def _get_emoji_generator():
        """Get emoji generator function."""
        try:
            from pymdownx.emoji import to_alt as emoji_generator
            return emoji_generator
        except (ImportError, AttributeError):
            return None

    @staticmethod
    def _slugify(value, separator='-'):
        """Create URL-friendly heading IDs, handling duplicates."""
        value = re.sub(r'[^\w\s-]', '', value.lower())
        return re.sub(r'[-\s]+', separator, value).strip(separator)

    def _load_css(self, name: str) -> str:
        """Load a CSS file from assets, with caching."""
        if name not in self._css_cache:
            css_path = Path(self._asset_dir) / 'styles' / name
            try:
                self._css_cache[name] = css_path.read_text(encoding='utf-8')
            except (OSError, FileNotFoundError):
                self._css_cache[name] = f'/* CSS file not found: {name} */'
        return self._css_cache[name]

    def _get_katex_assets(self) -> str:
        """Generate HTML to include bundled KaTeX assets."""
        katex_dir = Path(self._asset_dir) / 'renderer' / 'katex'
        if not katex_dir.is_dir():
            return '<!-- KaTeX not available -->'

        katex_css = katex_dir / 'katex.min.css'
        katex_js = katex_dir / 'katex.min.js'
        auto_render_js = katex_dir / 'auto-render.min.js'

        parts = []
        if katex_css.exists():
            css_uri = katex_css.as_uri()
            parts.append(f'<link rel="stylesheet" href="{css_uri}">')
        if katex_js.exists():
            js_uri = katex_js.as_uri()
            parts.append(f'<script defer src="{js_uri}"></script>')
        if auto_render_js.exists():
            js_uri = auto_render_js.as_uri()
            parts.append(f'<script defer src="{js_uri}"></script>')

        if parts:
            parts.append('''<script>
document.addEventListener("DOMContentLoaded", function() {
    if (typeof renderMathInElement !== 'undefined') {
        renderMathInElement(document.body, {
            delimiters: [
                {left: "$$", right: "$$", display: true},
                {left: "\\\\(", right: "\\\\)", display: false},
                {left: "\\\\[", right: "\\\\]", display: true}
            ],
            throwOnError: false
        });
    }
});
</script>''')

        return '\n'.join(parts)

    def _get_mermaid_assets(self) -> str:
        """Generate HTML to include bundled Mermaid.js."""
        mermaid_dir = Path(self._asset_dir) / 'renderer' / 'mermaid'
        if not mermaid_dir.is_dir():
            return '<!-- Mermaid not available -->'

        mermaid_js = mermaid_dir / 'mermaid.min.js'
        if not mermaid_js.exists():
            return '<!-- Mermaid JS not found -->'

        js_uri = mermaid_js.as_uri()
        return f'''<script src="{js_uri}"></script>
<script>
document.addEventListener("DOMContentLoaded", function() {{
    if (typeof mermaid !== 'undefined') {{
        var theme = document.body.classList.contains('dark') ? 'dark' : 'default';
        mermaid.initialize({{ startOnLoad: true, theme: theme, securityLevel: 'strict' }});
    }}
}});
</script>'''

    def sanitize_html(self, raw_html: str) -> str:
        """
        Sanitize HTML content to prevent XSS and other attacks.

        Strips dangerous tags, attributes, and URL schemes.
        """
        def _filter_attrs(tag, name, value):
            """Filter attributes during sanitization."""
            # Block all event handlers
            if name.startswith('on'):
                return False
            # Check tag-specific allowed attributes
            tag_attrs = ALLOWED_ATTRIBUTES.get(tag, [])
            global_attrs = ALLOWED_ATTRIBUTES.get('*', [])
            if name not in tag_attrs and name not in global_attrs:
                return False
            # Sanitize href/src values
            if name == 'href' and value:
                try:
                    parsed = urllib.parse.urlparse(value)
                    if parsed.scheme.lower() in ('javascript', 'vbscript'):
                        return False
                except (ValueError, AttributeError):
                    return False
            if name == 'src' and value:
                try:
                    parsed = urllib.parse.urlparse(value)
                    if parsed.scheme.lower() in ('javascript', 'vbscript'):
                        return False
                except (ValueError, AttributeError):
                    return False
            # Block type attribute values that could be dangerous for input
            if tag == 'input' and name == 'type':
                if value not in ('checkbox',):
                    return False
            return True

        # Strip dangerous tags and their inner contents completely
        raw_html = re.sub(
            r'<\s*(?:script|style|iframe|object|embed)[^>]*>[\s\S]*?<\s*/\s*(?:script|style|iframe|object|embed)\s*>',
            '',
            raw_html,
            flags=re.IGNORECASE
        )
        raw_html = re.sub(
            r'<\s*(?:script|style|iframe|object|embed)[^>]*/>',
            '',
            raw_html,
            flags=re.IGNORECASE
        )
        raw_html = re.sub(
            r'<\s*(?:script|style|iframe|object|embed)\b[^>]*>',
            '',
            raw_html,
            flags=re.IGNORECASE
        )

        cleaned = bleach.clean(
            raw_html,
            tags=ALLOWED_TAGS,
            attributes=_filter_attrs,
            strip=True,
            strip_comments=True,
        )
        return cleaned

    def render(self, markdown_source: str, doc_dir: str = '',
               dark_theme: bool = False) -> str:
        """
        Render Markdown source to a complete HTML page.

        Args:
            markdown_source: Raw Markdown text
            doc_dir: Directory containing the document (for relative paths)
            dark_theme: Whether to use dark theme styling

        Returns:
            Complete HTML page string
        """
        # Create a fresh Markdown instance each time to avoid state issues
        md = markdown.Markdown(
            extensions=self._extensions,
            extension_configs=self._extension_configs,
        )

        # Convert Markdown to HTML
        body_html = md.convert(markdown_source)

        # Extract TOC data for sidebar
        if hasattr(md, 'toc_tokens'):
            self._toc_data = md.toc_tokens
        else:
            self._toc_data = []

        # Sanitize the rendered HTML
        body_html = self.sanitize_html(body_html)

        # Fix relative image paths
        if doc_dir:
            body_html = self._fix_image_paths(body_html, doc_dir)

        # Assemble the full HTML page
        return self._build_html_page(body_html, doc_dir, dark_theme)

    def _fix_image_paths(self, html_content: str, doc_dir: str) -> str:
        """Convert relative image paths to absolute file:// URIs."""
        def _replace_src(match):
            src = match.group(1)
            quote = match.group(0)[4]  # quote character
            if src.startswith(('http://', 'https://', 'data:', 'file://')):
                return match.group(0)
            validated = validate_image_path(doc_dir, src)
            if validated:
                return f'src={quote}{validated}{quote}'
            # Keep original for missing images (browser will show broken icon)
            abs_path = Path(doc_dir) / src
            return f'src={quote}file://{urllib.parse.quote(str(abs_path))}{quote}'

        return re.sub(
            r'src=(["\'])([^"\']+)\1',
            lambda m: _replace_src_match(m, doc_dir),
            html_content
        )

    def _build_html_page(self, body_html: str, doc_dir: str,
                         dark_theme: bool) -> str:
        """Assemble a complete HTML page with styles and scripts."""
        theme_class = 'dark' if dark_theme else 'light'

        # Load CSS
        main_css = self._load_css('github-markdown.css')
        alerts_css = self._load_css('alerts.css')
        highlight_css_name = 'highlights-dark.css' if dark_theme else 'highlights-light.css'
        highlight_css = self._load_css(highlight_css_name)

        # Base tag for relative paths
        base_tag = ''
        if doc_dir:
            base_uri = Path(doc_dir).as_uri()
            base_tag = f'<base href="{base_uri}/">'

        # KaTeX and Mermaid assets
        katex_html = self._get_katex_assets()
        mermaid_html = self._get_mermaid_assets()

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline' file:; img-src file: data:; font-src file: data:; script-src file: 'unsafe-inline';">
    {base_tag}
    <style>
{main_css}
{alerts_css}
{highlight_css}
    </style>
    {katex_html}
</head>
<body class="{theme_class}">
    <article class="markdown-body">
{body_html}
    </article>
    {mermaid_html}
    <script>
    // Report headings for TOC current-section tracking
    function getVisibleHeading() {{
        var headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        for (var i = headings.length - 1; i >= 0; i--) {{
            var rect = headings[i].getBoundingClientRect();
            if (rect.top <= 80) {{
                return headings[i].id || '';
            }}
        }}
        return headings.length > 0 ? (headings[0].id || '') : '';
    }}
    </script>
</body>
</html>'''

    def get_toc_data(self):
        """Return the table of contents data from the last render."""
        return self._toc_data

    def clear_cache(self):
        """Clear the CSS cache (e.g., after theme change)."""
        self._css_cache.clear()


def _replace_src_match(match, doc_dir):
    """Helper to replace image src attributes with validated paths."""
    full_match = match.group(0)
    quote_char = full_match[4]  # The quote character after src=
    src = match.group(2)

    if src.startswith(('http://', 'https://', 'data:', 'file://')):
        return full_match

    validated = validate_image_path(doc_dir, src)
    if validated:
        return f'src={quote_char}{validated}{quote_char}'

    # Keep a file:// path for missing images (browser will show placeholder)
    abs_path = Path(doc_dir) / src
    file_uri = f'file://{urllib.parse.quote(str(abs_path.resolve()))}'
    return f'src={quote_char}{file_uri}{quote_char}'
