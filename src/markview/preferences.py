# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Suresh Soundararajan

"""Preferences management for MarkView — theme, zoom, and recent files."""

import json
import os
from pathlib import Path
from typing import Optional

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Adw, GLib


class ThemeMode:
    """Theme mode constants."""
    SYSTEM = 'system'
    LIGHT = 'light'
    DARK = 'dark'


class Preferences:
    """
    Manages user preferences with persistence to a JSON config file.

    Preferences are stored in XDG_CONFIG_HOME/markview/preferences.json.
    """

    DEFAULT_ZOOM = 1.0
    MIN_ZOOM = 0.5
    MAX_ZOOM = 3.0
    ZOOM_STEP = 0.1

    def __init__(self):
        self._config_dir = self._get_config_dir()
        self._config_file = self._config_dir / 'preferences.json'
        self._theme_mode = ThemeMode.SYSTEM
        self._zoom_level = self.DEFAULT_ZOOM
        self._recent_files = []
        self._max_recent = 10
        self._on_theme_changed = None
        self._on_zoom_changed = None
        self._load()

    @staticmethod
    def _get_config_dir() -> Path:
        """Get the configuration directory path."""
        config_home = os.environ.get(
            'XDG_CONFIG_HOME',
            str(Path.home() / '.config')
        )
        config_dir = Path(config_home) / 'markview'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def _load(self):
        """Load preferences from disk."""
        try:
            if self._config_file.exists():
                data = json.loads(self._config_file.read_text(encoding='utf-8'))
                self._theme_mode = data.get('theme_mode', ThemeMode.SYSTEM)
                self._zoom_level = float(data.get('zoom_level', self.DEFAULT_ZOOM))
                self._zoom_level = max(self.MIN_ZOOM, min(self.MAX_ZOOM, self._zoom_level))
                self._recent_files = data.get('recent_files', [])[:self._max_recent]
        except (json.JSONDecodeError, OSError, ValueError):
            pass  # Use defaults

    def _save(self):
        """Save preferences to disk."""
        try:
            data = {
                'theme_mode': self._theme_mode,
                'zoom_level': round(self._zoom_level, 2),
                'recent_files': self._recent_files[:self._max_recent],
            }
            self._config_file.write_text(
                json.dumps(data, indent=2), encoding='utf-8'
            )
        except OSError:
            pass  # Silently fail

    # --- Theme ---

    @property
    def theme_mode(self) -> str:
        return self._theme_mode

    @theme_mode.setter
    def theme_mode(self, mode: str):
        if mode in (ThemeMode.SYSTEM, ThemeMode.LIGHT, ThemeMode.DARK):
            self._theme_mode = mode
            self._save()
            if self._on_theme_changed:
                self._on_theme_changed(mode)

    def set_theme_changed_callback(self, callback):
        """Set callback for theme changes: callback(theme_mode: str)."""
        self._on_theme_changed = callback

    def apply_theme(self, style_manager: Adw.StyleManager):
        """Apply the current theme to the Adw.StyleManager."""
        if self._theme_mode == ThemeMode.LIGHT:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        elif self._theme_mode == ThemeMode.DARK:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.PREFER_LIGHT)

    def is_dark_theme(self, style_manager: Adw.StyleManager) -> bool:
        """Check if the current effective theme is dark."""
        return style_manager.get_dark()

    # --- Zoom ---

    @property
    def zoom_level(self) -> float:
        return self._zoom_level

    @zoom_level.setter
    def zoom_level(self, level: float):
        level = max(self.MIN_ZOOM, min(self.MAX_ZOOM, round(level, 2)))
        if level != self._zoom_level:
            self._zoom_level = level
            self._save()
            if self._on_zoom_changed:
                self._on_zoom_changed(level)

    def set_zoom_changed_callback(self, callback):
        """Set callback for zoom changes: callback(zoom_level: float)."""
        self._on_zoom_changed = callback

    def zoom_in(self):
        """Increase zoom level."""
        self.zoom_level = self._zoom_level + self.ZOOM_STEP

    def zoom_out(self):
        """Decrease zoom level."""
        self.zoom_level = self._zoom_level - self.ZOOM_STEP

    def zoom_reset(self):
        """Reset zoom to default level."""
        self.zoom_level = self.DEFAULT_ZOOM

    # --- Recent Files ---

    @property
    def recent_files(self) -> list:
        """Get list of recent file paths."""
        return list(self._recent_files)

    def add_recent_file(self, filepath: str):
        """Add a file to the recent files list."""
        filepath = str(Path(filepath).resolve())
        # Remove if already present
        if filepath in self._recent_files:
            self._recent_files.remove(filepath)
        # Add to front
        self._recent_files.insert(0, filepath)
        # Trim to max
        self._recent_files = self._recent_files[:self._max_recent]
        self._save()

    def remove_recent_file(self, filepath: str):
        """Remove a file from the recent files list."""
        filepath = str(Path(filepath).resolve())
        if filepath in self._recent_files:
            self._recent_files.remove(filepath)
            self._save()

    def clear_recent_files(self):
        """Clear all recent files."""
        self._recent_files.clear()
        self._save()
