# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Suresh Soundararajan

"""Utility functions for file handling, path validation, and URL safety."""

import os
import re
import urllib.parse
from pathlib import Path
from typing import Optional

# Supported Markdown extensions
MARKDOWN_EXTENSIONS = {'.md', '.markdown', '.mdown', '.mkd', '.mdx'}

# Dangerous URL schemes
DANGEROUS_SCHEMES = {'javascript', 'vbscript', 'data', 'blob'}

# Allowed URL schemes for external links
SAFE_EXTERNAL_SCHEMES = {'http', 'https', 'mailto', 'ftp'}


def is_markdown_file(filepath: str) -> bool:
    """Check if a file has a recognized Markdown extension."""
    return Path(filepath).suffix.lower() in MARKDOWN_EXTENSIONS


def read_markdown_file(filepath: str) -> Optional[str]:
    """
    Read a Markdown file with encoding detection.

    Tries UTF-8 first, then falls back to latin-1.
    Returns None if the file cannot be read.
    """
    path = Path(filepath)
    if not path.is_file():
        return None

    # Try UTF-8 first (most common)
    for encoding in ('utf-8', 'utf-8-sig', 'latin-1'):
        try:
            return path.read_text(encoding=encoding)
        except (UnicodeDecodeError, ValueError):
            continue
        except (OSError, PermissionError):
            return None

    return None


def get_document_title(filepath: str) -> str:
    """Extract a display title from a file path."""
    return Path(filepath).stem


def get_document_dir(filepath: str) -> str:
    """Get the directory containing the document for resolving relative paths."""
    return str(Path(filepath).parent.resolve())


def validate_local_path(base_dir: str, relative_path: str) -> Optional[str]:
    """
    Validate and resolve a relative path within a base directory.

    Prevents path traversal attacks by ensuring the resolved path
    stays within the base directory.

    Returns the absolute path if valid, None otherwise.
    """
    try:
        base = Path(base_dir).resolve()
        target = (base / relative_path).resolve()

        # Check the resolved path is under the base directory
        if not str(target).startswith(str(base)):
            return None

        # Don't follow symlinks that escape the base directory
        if target.is_symlink():
            real_target = target.resolve()
            if not str(real_target).startswith(str(base)):
                return None

        return str(target)
    except (ValueError, OSError):
        return None


def validate_image_path(doc_dir: str, src: str) -> Optional[str]:
    """
    Validate an image source path relative to the document directory.

    Returns a safe file:// URI if the path is valid, None otherwise.
    """
    if not src:
        return None

    # Already an absolute file URI
    if src.startswith('file://'):
        return src

    # Remote URLs — don't validate, just pass through (handled by policy)
    if src.startswith(('http://', 'https://', 'data:')):
        return src

    # Relative path — validate it
    resolved = validate_local_path(doc_dir, src)
    if resolved and Path(resolved).exists():
        return f'file://{urllib.parse.quote(resolved)}'

    return None


def validate_external_url(url: str) -> bool:
    """
    Check if a URL is safe to open in an external browser.

    Returns True for http, https, mailto, and ftp URLs.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.scheme.lower() in SAFE_EXTERNAL_SCHEMES
    except (ValueError, AttributeError):
        return False


def is_dangerous_url(url: str) -> bool:
    """Check if a URL uses a dangerous scheme like javascript:."""
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.scheme.lower() in DANGEROUS_SCHEMES
    except (ValueError, AttributeError):
        return True


def is_local_markdown_link(url: str) -> bool:
    """Check if a URL points to a local Markdown file."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme and parsed.scheme not in ('file', ''):
            return False
        path = parsed.path
        return is_markdown_file(path)
    except (ValueError, AttributeError):
        return False


def resolve_local_markdown_link(doc_dir: str, url: str) -> Optional[str]:
    """
    Resolve a relative Markdown link to an absolute file path.

    Returns the absolute path if valid, None otherwise.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        path = urllib.parse.unquote(parsed.path)
        resolved = validate_local_path(doc_dir, path)
        if resolved and Path(resolved).exists():
            return resolved
    except (ValueError, AttributeError, OSError):
        pass
    return None


def get_file_filter_patterns():
    """Return file filter patterns for the GTK file chooser."""
    return [f'*{ext}' for ext in sorted(MARKDOWN_EXTENSIONS)]


def get_mime_types():
    """Return MIME types for Markdown files."""
    return ['text/markdown', 'text/x-markdown']


def find_asset_dir() -> str:
    """
    Locate the assets directory.

    Checks in order:
    1. MARKVIEW_DATA_DIR environment variable (AppImage)
    2. Relative to this source file (development)
    3. System data directories
    """
    # AppImage or explicit override
    env_dir = os.environ.get('MARKVIEW_DATA_DIR')
    if env_dir and Path(env_dir).is_dir():
        return env_dir

    # Development: assets/ relative to project root
    src_dir = Path(__file__).parent  # src/markview/
    project_root = src_dir.parent.parent  # project root
    dev_assets = project_root / 'assets'
    if dev_assets.is_dir():
        return str(dev_assets)

    # Installed: check XDG data dirs
    xdg_data_dirs = os.environ.get('XDG_DATA_DIRS', '/usr/share:/usr/local/share')
    for data_dir in xdg_data_dirs.split(':'):
        candidate = Path(data_dir) / 'markview'
        if candidate.is_dir():
            return str(candidate)

    # Fallback to dev path even if it doesn't exist
    return str(dev_assets)
