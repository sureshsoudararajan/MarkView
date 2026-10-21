# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Suresh Soundararajan

"""Table of Contents extraction and sidebar management for MarkView."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, GObject, Gio, Pango


class TocEntry(GObject.Object):
    """A single heading entry in the Table of Contents."""

    __gtype_name__ = 'TocEntry'

    def __init__(self, title: str, anchor_id: str, level: int):
        super().__init__()
        self._title = title
        self._anchor_id = anchor_id
        self._level = level
        self._children = Gio.ListStore.new(TocEntry)

    @GObject.Property(type=str)
    def title(self) -> str:
        return self._title

    @GObject.Property(type=str)
    def anchor_id(self) -> str:
        return self._anchor_id

    @GObject.Property(type=int)
    def level(self) -> int:
        return self._level

    @property
    def children(self) -> Gio.ListStore:
        return self._children

    def add_child(self, child: 'TocEntry'):
        self._children.append(child)


class TableOfContents:
    """
    Manages the Table of Contents sidebar.

    Extracts heading information from Python-Markdown's TOC extension output
    and builds a navigable tree in a Gtk.ListView.
    """

    def __init__(self):
        self._entries = Gio.ListStore.new(TocEntry)
        self._flat_entries = Gio.ListStore.new(TocEntry)
        self._on_heading_clicked = None
        self._current_heading_id = None
        self._list_view = None
        self._selection_model = None

    def build_from_toc_tokens(self, toc_tokens: list):
        """
        Build the TOC from Python-Markdown's toc_tokens.

        toc_tokens is a list of dicts:
        [{'level': 1, 'id': 'heading-id', 'name': 'Heading Text', 'children': [...]}]
        """
        self._entries.remove_all()
        self._flat_entries.remove_all()

        def _process_tokens(tokens, parent_level=0):
            for token in tokens:
                entry = TocEntry(
                    title=token.get('name', ''),
                    anchor_id=token.get('id', ''),
                    level=token.get('level', 1),
                )
                self._entries.append(entry)
                self._flat_entries.append(entry)

                children = token.get('children', [])
                if children:
                    _process_tokens(children)

        _process_tokens(toc_tokens)

    def create_sidebar_widget(self, on_heading_clicked=None) -> Gtk.Widget:
        """
        Create the GTK sidebar widget for the Table of Contents.

        Args:
            on_heading_clicked: Callback(anchor_id: str) when a heading is clicked

        Returns:
            A Gtk.Box containing the TOC list
        """
        self._on_heading_clicked = on_heading_clicked

        # Main container
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.add_css_class('sidebar')
        box.set_size_request(240, -1)

        # Title
        title_label = Gtk.Label(label="Table of Contents")
        title_label.add_css_class('title-4')
        title_label.set_margin_top(12)
        title_label.set_margin_bottom(8)
        title_label.set_margin_start(16)
        title_label.set_margin_end(16)
        title_label.set_halign(Gtk.Align.START)
        box.append(title_label)

        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.append(separator)

        # Scrolled list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # Selection model
        self._selection_model = Gtk.SingleSelection.new(self._flat_entries)
        self._selection_model.set_autoselect(False)
        self._selection_model.set_can_unselect(True)

        # List view with factory
        factory = Gtk.SignalListItemFactory()
        factory.connect('setup', self._on_factory_setup)
        factory.connect('bind', self._on_factory_bind)

        self._list_view = Gtk.ListView.new(self._selection_model, factory)
        self._list_view.add_css_class('navigation-sidebar')
        self._list_view.set_single_click_activate(True)
        self._list_view.connect('activate', self._on_row_activated)

        scrolled.set_child(self._list_view)
        box.append(scrolled)

        return box

    def _on_factory_setup(self, factory, list_item):
        """Set up a TOC list item."""
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_margin_top(4)
        label.set_margin_bottom(4)
        label.set_margin_end(12)
        label.set_hexpand(True)
        label.set_can_target(False)
        list_item.set_child(label)

    def _on_factory_bind(self, factory, list_item):
        """Bind data to a TOC list item."""
        label = list_item.get_child()
        entry = list_item.get_item()

        label.set_text(entry.title)
        label.set_tooltip_text(entry.title)

        # Indent based on heading level
        level = entry.level
        indent = max(0, (level - 1)) * 16 + 12
        label.set_margin_start(indent)

        # Style based on level
        # Remove old level classes
        for i in range(1, 7):
            label.remove_css_class(f'toc-level-{i}')
        label.add_css_class(f'toc-level-{level}')

        if level <= 2:
            label.add_css_class('heading')
        else:
            label.remove_css_class('heading')

    def _on_row_activated(self, list_view, position):
        """Handle clicking on a TOC entry."""
        entry = self._flat_entries.get_item(position)
        if entry and self._on_heading_clicked:
            self._on_heading_clicked(entry.anchor_id)

    def set_current_heading(self, anchor_id: str):
        """Highlight the current heading in the TOC."""
        self._current_heading_id = anchor_id
        # Find and select the matching entry
        for i in range(self._flat_entries.get_n_items()):
            entry = self._flat_entries.get_item(i)
            if entry.anchor_id == anchor_id:
                if self._selection_model:
                    self._selection_model.set_selected(i)
                return

    def clear(self):
        """Clear all TOC entries."""
        self._entries.remove_all()
        self._flat_entries.remove_all()
        self._current_heading_id = None

    @property
    def has_entries(self) -> bool:
        """Whether the TOC has any entries."""
        return self._flat_entries.get_n_items() > 0
