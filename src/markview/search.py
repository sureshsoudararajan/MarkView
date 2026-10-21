# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Suresh Soundararajan

"""Search controller for in-document text search in MarkView."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, WebKit, GLib


class SearchController:
    """
    Manages find-in-document functionality using WebKit's FindController.

    Provides a search bar UI and handles match navigation.
    """

    def __init__(self):
        self._webview = None
        self._find_controller = None
        self._search_bar = None
        self._search_entry = None
        self._match_count_label = None
        self._prev_button = None
        self._next_button = None
        self._current_match = 0
        self._total_matches = 0

    def create_search_bar(self) -> Gtk.SearchBar:
        """Create the search bar widget."""
        self._search_bar = Gtk.SearchBar()
        self._search_bar.set_show_close_button(True)

        # Search box with entry and navigation buttons
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.set_halign(Gtk.Align.CENTER)
        box.add_css_class('linked')

        # Search entry
        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text("Find in document…")
        self._search_entry.set_hexpand(True)
        self._search_entry.set_size_request(300, -1)
        self._search_entry.connect('search-changed', self._on_search_changed)
        self._search_entry.connect('activate', self._on_next_match)
        self._search_entry.connect(
            'stop-search', lambda e: self._search_bar.set_search_mode(False)
        )
        box.append(self._search_entry)

        # Connect search bar to entry
        self._search_bar.connect_entry(self._search_entry)

        # Match count label
        self._match_count_label = Gtk.Label(label="")
        self._match_count_label.add_css_class('dim-label')
        self._match_count_label.set_margin_start(6)
        self._match_count_label.set_margin_end(6)
        box.append(self._match_count_label)

        # Navigation buttons (outside linked group)
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        nav_box.add_css_class('linked')

        self._prev_button = Gtk.Button.new_from_icon_name('go-up-symbolic')
        self._prev_button.set_tooltip_text("Previous match (Shift+Enter)")
        self._prev_button.connect('clicked', self._on_prev_match)
        self._prev_button.set_sensitive(False)
        nav_box.append(self._prev_button)

        self._next_button = Gtk.Button.new_from_icon_name('go-down-symbolic')
        self._next_button.set_tooltip_text("Next match (Enter)")
        self._next_button.connect('clicked', self._on_next_match)
        self._next_button.set_sensitive(False)
        nav_box.append(self._next_button)

        # Outer box
        outer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        outer_box.set_halign(Gtk.Align.CENTER)
        outer_box.append(box)
        outer_box.append(nav_box)

        self._search_bar.set_child(outer_box)

        # Handle search bar visibility changes
        self._search_bar.connect(
            'notify::search-mode-enabled', self._on_search_mode_changed
        )

        return self._search_bar

    def set_webview(self, webview: WebKit.WebView):
        """Connect to a WebView's find controller."""
        self._webview = webview
        self._find_controller = webview.get_find_controller()

        self._find_controller.connect(
            'found-text', self._on_found_text
        )
        self._find_controller.connect(
            'failed-to-find-text', self._on_failed_to_find
        )
        self._find_controller.connect(
            'counted-matches', self._on_counted_matches
        )

    def show(self):
        """Show the search bar and focus the entry."""
        if self._search_bar:
            self._search_bar.set_search_mode(True)
            if self._search_entry:
                self._search_entry.grab_focus()

    def hide(self):
        """Hide the search bar and clear highlights."""
        if self._search_bar:
            self._search_bar.set_search_mode(False)

    def _on_search_changed(self, entry):
        """Handle search text changes."""
        text = entry.get_text()
        if not text or not self._find_controller:
            self._total_matches = 0
            self._update_match_count(0, 0)
            if self._find_controller:
                self._find_controller.search_finish()
            return

        # Search with case-insensitive matching and count matches accurately
        find_options = (
            WebKit.FindOptions.CASE_INSENSITIVE |
            WebKit.FindOptions.WRAP_AROUND
        )
        self._find_controller.search(text, find_options, 1000)
        self._find_controller.count_matches(text, find_options, 1000)

    def _on_next_match(self, *args):
        """Navigate to the next match."""
        if self._find_controller and self._total_matches > 0:
            self._find_controller.search_next()

    def _on_prev_match(self, *args):
        """Navigate to the previous match."""
        if self._find_controller and self._total_matches > 0:
            self._find_controller.search_previous()

    def _on_found_text(self, find_controller, match_count):
        """Handle when text is found."""
        self._prev_button.set_sensitive(True)
        self._next_button.set_sensitive(True)
        # WebKit emits G_MAXUINT (4294967295) when match count is uncounted
        if 0 < match_count < 4294967295:
            self._total_matches = match_count
            self._update_match_count(match_count, -1)

    def _on_counted_matches(self, find_controller, match_count):
        """Handle when total matches have been counted."""
        if match_count < 4294967295:
            self._total_matches = match_count
            self._update_match_count(match_count, -1)
            self._prev_button.set_sensitive(match_count > 0)
            self._next_button.set_sensitive(match_count > 0)

    def _on_failed_to_find(self, find_controller):
        """Handle when search text is not found."""
        self._total_matches = 0
        self._update_match_count(0, 0)
        self._prev_button.set_sensitive(False)
        self._next_button.set_sensitive(False)

    def _update_match_count(self, total, current=0):
        """Update the match count label."""
        if not self._match_count_label:
            return

        text = self._search_entry.get_text() if self._search_entry else ""
        if not text:
            self._match_count_label.set_text("")
            return

        # Avoid displaying G_MAXUINT or uninitialized match counts
        if 0 < total < 4294967295:
            if total == 1:
                self._match_count_label.set_text("1 match")
            elif total >= 1000:
                self._match_count_label.set_text("1,000+ matches")
            else:
                self._match_count_label.set_text(f"{total} matches")
        elif total == 0:
            self._match_count_label.set_text("No matches")
        else:
            self._match_count_label.set_text("")

    def _on_search_mode_changed(self, search_bar, pspec):
        """Handle search bar visibility changes."""
        if not search_bar.get_search_mode():
            # Clear search highlights when closing
            if self._find_controller:
                self._find_controller.search_finish()
            self._update_match_count(0, 0)
            self._prev_button.set_sensitive(False)
            self._next_button.set_sensitive(False)
