# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Suresh Soundararajan

"""MarkView application — Adw.Application subclass with actions and shortcuts."""

import sys
from pathlib import Path

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib

from markview import __app_id__, __app_name__, __version__, __author__
from markview.window import MarkViewWindow
from markview.preferences import Preferences, ThemeMode
from markview.utils import is_markdown_file, get_file_filter_patterns, get_mime_types


class MarkViewApplication(Adw.Application):
    """The MarkView application."""

    def __init__(self):
        super().__init__(
            application_id=__app_id__,
            flags=Gio.ApplicationFlags.HANDLES_OPEN,
        )
        self._preferences = Preferences()
        self._window = None

    def do_startup(self):
        """Application startup — register actions and shortcuts."""
        Adw.Application.do_startup(self)

        # Apply initial theme
        style_manager = self.get_style_manager()
        self._preferences.apply_theme(style_manager)

        # Register actions
        self._register_actions()

        # Register keyboard shortcuts
        self._register_shortcuts()

    def do_activate(self):
        """Application activation — create or present the main window."""
        if not self._window:
            self._window = MarkViewWindow(
                application=self,
                preferences=self._preferences,
            )
        self._window.present()

    def do_open(self, files, n_files, hint):
        """Handle opening files from the command line or file manager."""
        self.do_activate()
        if files:
            filepath = files[0].get_path()
            if filepath and is_markdown_file(filepath):
                self._window.open_file(filepath)

    # --- Actions ---

    def _register_actions(self):
        """Register all application actions."""
        # Open file
        action = Gio.SimpleAction.new('open-file', None)
        action.connect('activate', self._on_open_file)
        self.add_action(action)

        # Find
        action = Gio.SimpleAction.new('find', None)
        action.connect('activate', self._on_find)
        self.add_action(action)

        # Toggle TOC
        action = Gio.SimpleAction.new('toggle-toc', None)
        action.connect('activate', self._on_toggle_toc)
        self.add_action(action)

        # Theme (stateful with string parameter)
        action = Gio.SimpleAction.new('theme', GLib.VariantType.new('s'))
        action.connect('activate', self._on_theme_change)
        self.add_action(action)

        # Zoom
        action = Gio.SimpleAction.new('zoom-in', None)
        action.connect('activate', lambda a, p: self._preferences.zoom_in())
        self.add_action(action)

        action = Gio.SimpleAction.new('zoom-out', None)
        action.connect('activate', lambda a, p: self._preferences.zoom_out())
        self.add_action(action)

        action = Gio.SimpleAction.new('zoom-reset', None)
        action.connect('activate', lambda a, p: self._preferences.zoom_reset())
        self.add_action(action)

        # Fullscreen
        action = Gio.SimpleAction.new('toggle-fullscreen', None)
        action.connect('activate', self._on_toggle_fullscreen)
        self.add_action(action)

        # Show shortcuts
        action = Gio.SimpleAction.new('show-shortcuts', None)
        action.connect('activate', self._on_show_shortcuts)
        self.add_action(action)

        # About
        action = Gio.SimpleAction.new('about', None)
        action.connect('activate', self._on_about)
        self.add_action(action)

        # Quit
        action = Gio.SimpleAction.new('quit', None)
        action.connect('activate', lambda a, p: self.quit())
        self.add_action(action)

        # Close window
        action = Gio.SimpleAction.new('close-window', None)
        action.connect('activate', self._on_close_window)
        self.add_action(action)

    def _register_shortcuts(self):
        """Register keyboard shortcuts."""
        self.set_accels_for_action('app.open-file', ['<Control>o'])
        self.set_accels_for_action('app.find', ['<Control>f'])
        self.set_accels_for_action('app.toggle-toc', ['<Control>t'])
        self.set_accels_for_action('app.zoom-in', ['<Control>plus', '<Control>equal'])
        self.set_accels_for_action('app.zoom-out', ['<Control>minus'])
        self.set_accels_for_action('app.zoom-reset', ['<Control>0'])
        self.set_accels_for_action('app.toggle-fullscreen', ['F11'])
        self.set_accels_for_action('app.quit', ['<Control>q'])
        self.set_accels_for_action('app.close-window', ['<Control>w'])

    # --- Action Handlers ---

    def _on_open_file(self, action, param):
        """Show file chooser dialog."""
        if not self._window:
            return

        dialog = Gtk.FileDialog()
        dialog.set_title("Open Markdown File")

        # File filter
        filters = Gio.ListStore.new(Gtk.FileFilter)
        md_filter = Gtk.FileFilter()
        md_filter.set_name("Markdown Files")
        for pattern in get_file_filter_patterns():
            md_filter.add_pattern(pattern)
        for mime in get_mime_types():
            md_filter.add_mime_type(mime)
        filters.append(md_filter)

        all_filter = Gtk.FileFilter()
        all_filter.set_name("All Files")
        all_filter.add_pattern("*")
        filters.append(all_filter)

        dialog.set_filters(filters)
        dialog.set_default_filter(md_filter)

        dialog.open(self._window, None, self._on_file_chosen)

    def _on_file_chosen(self, dialog, result):
        """Handle file chooser result."""
        try:
            file = dialog.open_finish(result)
            if file:
                filepath = file.get_path()
                if filepath:
                    self._window.open_file(filepath)
        except GLib.Error:
            pass  # User cancelled

    def _on_find(self, action, param):
        """Show search bar."""
        if self._window:
            self._window.show_search()

    def _on_toggle_toc(self, action, param):
        """Toggle Table of Contents."""
        if self._window:
            self._window.toggle_toc()

    def _on_theme_change(self, action, param):
        """Change the application theme."""
        theme = param.get_string()
        if theme in (ThemeMode.LIGHT, ThemeMode.DARK, ThemeMode.SYSTEM):
            self._preferences.theme_mode = theme

    def _on_toggle_fullscreen(self, action, param):
        """Toggle fullscreen mode."""
        if self._window:
            if self._window.is_fullscreen():
                self._window.unfullscreen()
            else:
                self._window.fullscreen()

    def _on_close_window(self, action, param):
        """Close the current window."""
        if self._window:
            self._window.close()

    def _on_show_shortcuts(self, action, param):
        """Show keyboard shortcuts dialog."""
        if not self._window:
            return

        builder = Gtk.Builder()
        builder.add_from_string(SHORTCUTS_UI)
        shortcuts_window = builder.get_object('shortcuts-window')
        if shortcuts_window:
            shortcuts_window.set_transient_for(self._window)
            shortcuts_window.present()

    def _on_about(self, action, param):
        """Show the About dialog."""
        about = Adw.AboutDialog(
            application_name=__app_name__,
            application_icon=__app_id__,
            version=__version__,
            developer_name=__author__,
            developers=[__author__],
            copyright=f"© 2026 {__author__}",
            license_type=Gtk.License.MIT_X11,
            comments=(
                "A powerful, read-only Markdown viewer for Linux "
                "with rich GitHub-style rendering."
            ),
            issue_url="",
        )
        about.add_acknowledgement_section(
            "Powered By",
            [
                "Python-Markdown https://python-markdown.github.io/",
                "PyMdown Extensions https://facelessuser.github.io/pymdown-extensions/",
                "Pygments https://pygments.org/",
                "KaTeX https://katex.org/",
                "Mermaid https://mermaid.js.org/",
                "GTK https://gtk.org/",
                "WebKitGTK https://webkitgtk.org/",
            ],
        )
        about.present(self._window)


# --- Shortcuts Window XML ---
SHORTCUTS_UI = '''<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <object class="GtkShortcutsWindow" id="shortcuts-window">
    <property name="modal">1</property>
    <child>
      <object class="GtkShortcutsSection">
        <property name="section-name">shortcuts</property>
        <child>
          <object class="GtkShortcutsGroup">
            <property name="title">File</property>
            <child>
              <object class="GtkShortcutsShortcut">
                <property name="title">Open file</property>
                <property name="accelerator">&lt;Control&gt;o</property>
              </object>
            </child>
            <child>
              <object class="GtkShortcutsShortcut">
                <property name="title">Close window</property>
                <property name="accelerator">&lt;Control&gt;w</property>
              </object>
            </child>
            <child>
              <object class="GtkShortcutsShortcut">
                <property name="title">Quit</property>
                <property name="accelerator">&lt;Control&gt;q</property>
              </object>
            </child>
          </object>
        </child>
        <child>
          <object class="GtkShortcutsGroup">
            <property name="title">View</property>
            <child>
              <object class="GtkShortcutsShortcut">
                <property name="title">Find in document</property>
                <property name="accelerator">&lt;Control&gt;f</property>
              </object>
            </child>
            <child>
              <object class="GtkShortcutsShortcut">
                <property name="title">Table of Contents</property>
                <property name="accelerator">&lt;Control&gt;t</property>
              </object>
            </child>
            <child>
              <object class="GtkShortcutsShortcut">
                <property name="title">Toggle fullscreen</property>
                <property name="accelerator">F11</property>
              </object>
            </child>
          </object>
        </child>
        <child>
          <object class="GtkShortcutsGroup">
            <property name="title">Zoom</property>
            <child>
              <object class="GtkShortcutsShortcut">
                <property name="title">Zoom in</property>
                <property name="accelerator">&lt;Control&gt;plus</property>
              </object>
            </child>
            <child>
              <object class="GtkShortcutsShortcut">
                <property name="title">Zoom out</property>
                <property name="accelerator">&lt;Control&gt;minus</property>
              </object>
            </child>
            <child>
              <object class="GtkShortcutsShortcut">
                <property name="title">Reset zoom</property>
                <property name="accelerator">&lt;Control&gt;0</property>
              </object>
            </child>
          </object>
        </child>
      </object>
    </child>
  </object>
</interface>
'''
