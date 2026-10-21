# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Suresh Soundararajan

"""Main application window for MarkView."""

import os
import urllib.parse
from pathlib import Path

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, WebKit, Gio, GLib, Gdk

from markview import __app_name__, __version__
from markview.renderer import MarkdownRenderer
from markview.toc import TableOfContents
from markview.search import SearchController
from markview.preferences import Preferences, ThemeMode
from markview.utils import (
    is_markdown_file, read_markdown_file, get_document_title,
    get_document_dir, validate_external_url, is_dangerous_url,
    is_local_markdown_link, resolve_local_markdown_link,
    get_file_filter_patterns, get_mime_types, find_asset_dir,
)


class MarkViewWindow(Adw.ApplicationWindow):
    """The main MarkView application window."""

    def __init__(self, application, preferences: Preferences):
        super().__init__(
            application=application,
            title=__app_name__,
            default_width=1100,
            default_height=750,
        )

        self._preferences = preferences
        self._renderer = MarkdownRenderer()
        self._toc = TableOfContents()
        self._search = SearchController()
        self._current_file = None
        self._current_doc_dir = None
        self._navigation_history = []
        self._history_index = -1

        # Set up preferences callbacks
        self._preferences.set_theme_changed_callback(self._on_theme_changed)
        self._preferences.set_zoom_changed_callback(self._on_zoom_changed)

        self._build_ui()
        self._setup_drag_drop()
        self._setup_key_controller()

    def _build_ui(self):
        """Build the complete window UI."""
        # Main vertical layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # --- Header Bar ---
        self._header_bar = Adw.HeaderBar()

        # Open button
        open_button = Gtk.Button(icon_name='document-open-symbolic')
        open_button.set_tooltip_text("Open Markdown file (Ctrl+O)")
        open_button.set_action_name('app.open-file')
        self._header_bar.pack_start(open_button)

        # TOC toggle button
        self._toc_button = Gtk.ToggleButton(icon_name='view-list-symbolic')
        self._toc_button.set_tooltip_text("Toggle Table of Contents")
        self._toc_button.set_active(False)
        self._toc_button.connect('toggled', self._on_toc_toggled)
        self._header_bar.pack_start(self._toc_button)

        # Title widget
        self._title_widget = Adw.WindowTitle(
            title=__app_name__,
            subtitle=""
        )
        self._header_bar.set_title_widget(self._title_widget)

        # Menu button
        menu_button = Gtk.MenuButton(icon_name='open-menu-symbolic')
        menu_button.set_tooltip_text("Main menu")
        menu_button.set_menu_model(self._create_menu_model())
        self._header_bar.pack_end(menu_button)

        main_box.append(self._header_bar)

        # --- Search Bar ---
        self._search_bar = self._search.create_search_bar()
        main_box.append(self._search_bar)

        # --- Content Area ---
        self._overlay_split = Adw.OverlaySplitView()
        self._overlay_split.set_collapsed(False)
        self._overlay_split.set_show_sidebar(False)
        self._overlay_split.set_min_sidebar_width(220)
        self._overlay_split.set_max_sidebar_width(380)
        self._overlay_split.set_sidebar_width_fraction(0.25)
        self._overlay_split.connect('notify::show-sidebar', self._on_split_show_sidebar_changed)

        # Sidebar (TOC)
        toc_widget = self._toc.create_sidebar_widget(
            on_heading_clicked=self._scroll_to_heading
        )
        self._overlay_split.set_sidebar(toc_widget)

        # Content stack (WebView or empty state)
        self._content_stack = Gtk.Stack()
        self._content_stack.set_transition_type(
            Gtk.StackTransitionType.CROSSFADE
        )

        # Empty state
        self._empty_state = self._create_empty_state()
        self._content_stack.add_named(self._empty_state, 'empty')

        # WebView container
        self._webview = self._create_webview()
        webview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        webview_box.append(self._webview)
        self._content_stack.add_named(webview_box, 'document')

        self._overlay_split.set_content(self._content_stack)
        main_box.append(self._overlay_split)

        self._content_stack.set_visible_child_name('empty')

        self.set_content(main_box)

        # Connect search to webview
        self._search.set_webview(self._webview)

        # Apply initial zoom
        self._webview.set_zoom_level(self._preferences.zoom_level)

    def _create_empty_state(self) -> Gtk.Widget:
        """Create the welcome/empty state screen."""
        status_page = Adw.StatusPage()
        status_page.set_icon_name('document-open-symbolic')
        status_page.set_title(__app_name__)
        status_page.set_description(
            "A powerful, read-only Markdown viewer for Linux\n"
            "with rich GitHub-style rendering"
        )

        # Button box
        button_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            halign=Gtk.Align.CENTER,
        )

        open_btn = Gtk.Button(label="Open Markdown File")
        open_btn.add_css_class('suggested-action')
        open_btn.add_css_class('pill')
        open_btn.set_action_name('app.open-file')
        button_box.append(open_btn)

        hint_label = Gtk.Label(
            label="You can also drag and drop a Markdown file here"
        )
        hint_label.add_css_class('dim-label')
        hint_label.add_css_class('caption')
        button_box.append(hint_label)

        # Recent files
        recent_files = self._preferences.recent_files
        if recent_files:
            recent_label = Gtk.Label(label="Recent Files")
            recent_label.add_css_class('title-4')
            recent_label.set_margin_top(24)
            button_box.append(recent_label)

            recent_list = Gtk.ListBox()
            recent_list.set_selection_mode(Gtk.SelectionMode.NONE)
            recent_list.add_css_class('boxed-list')
            recent_list.set_size_request(400, -1)

            for filepath in recent_files[:5]:
                if Path(filepath).exists():
                    row = Adw.ActionRow()
                    row.set_title(Path(filepath).name)
                    row.set_subtitle(str(Path(filepath).parent))
                    row.set_activatable(True)
                    row.connect(
                        'activated',
                        lambda r, f=filepath: self.open_file(f)
                    )
                    icon = Gtk.Image.new_from_icon_name(
                        'document-open-symbolic'
                    )
                    row.add_prefix(icon)
                    recent_list.append(row)

            if recent_list.get_first_child():
                button_box.append(recent_list)

        status_page.set_child(button_box)
        return status_page

    def _create_webview(self) -> WebKit.WebView:
        """Create a security-hardened WebKit WebView."""
        webview = WebKit.WebView()

        # Security settings
        settings = webview.get_settings()
        settings.set_enable_javascript(True)  # Needed for KaTeX/Mermaid
        settings.set_enable_javascript_markup(False)  # Block inline scripts in content
        settings.set_allow_file_access_from_file_urls(True)  # For local images
        settings.set_allow_universal_access_from_file_urls(False)
        settings.set_enable_html5_database(False)
        settings.set_enable_html5_local_storage(False)
        settings.set_enable_offline_web_application_cache(False)
        settings.set_enable_page_cache(False)
        settings.set_enable_webaudio(False)
        settings.set_enable_webgl(False)
        settings.set_enable_webrtc(False)
        settings.set_enable_media(False)
        settings.set_enable_media_stream(False)
        settings.set_enable_mediasource(False)
        settings.set_javascript_can_access_clipboard(False)
        settings.set_javascript_can_open_windows_automatically(False)
        settings.set_enable_developer_extras(False)
        settings.set_enable_smooth_scrolling(True)
        settings.set_enable_back_forward_navigation_gestures(False)

        # Navigation policy — block all navigation except scrolling
        webview.connect('decide-policy', self._on_decide_policy)

        # Expand to fill
        webview.set_vexpand(True)
        webview.set_hexpand(True)

        return webview

    def _create_menu_model(self) -> Gio.Menu:
        """Create the main application menu."""
        menu = Gio.Menu()

        # File section
        file_section = Gio.Menu()
        file_section.append("Open File…", "app.open-file")
        menu.append_section(None, file_section)

        # View section
        view_section = Gio.Menu()
        view_section.append("Find in Document", "app.find")
        view_section.append("Table of Contents", "app.toggle-toc")
        menu.append_section(None, view_section)

        # Appearance submenu
        appearance_menu = Gio.Menu()
        appearance_menu.append("Light", "app.theme::light")
        appearance_menu.append("Dark", "app.theme::dark")
        appearance_menu.append("Follow System", "app.theme::system")
        menu.append_submenu("Appearance", appearance_menu)

        # Zoom section
        zoom_section = Gio.Menu()
        zoom_section.append("Zoom In", "app.zoom-in")
        zoom_section.append("Zoom Out", "app.zoom-out")
        zoom_section.append("Reset Zoom", "app.zoom-reset")
        menu.append_section(None, zoom_section)

        # Help section
        help_section = Gio.Menu()
        help_section.append("Keyboard Shortcuts", "app.show-shortcuts")
        help_section.append("About MarkView", "app.about")
        menu.append_section(None, help_section)

        return menu

    def _setup_drag_drop(self):
        """Set up drag and drop for Markdown files."""
        drop_target = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        drop_target.connect('drop', self._on_drop)
        self.add_controller(drop_target)

    def _on_drop(self, drop_target, value, x, y):
        """Handle dropped files."""
        if isinstance(value, Gio.File):
            filepath = value.get_path()
            if filepath and is_markdown_file(filepath):
                self.open_file(filepath)
                return True
        return False

    def _setup_key_controller(self):
        """Set up keyboard event handling."""
        key_controller = Gtk.EventControllerKey()
        key_controller.connect('key-pressed', self._on_key_pressed)
        self.add_controller(key_controller)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        """Handle key press events."""
        # Escape: close search or exit fullscreen
        if keyval == Gdk.KEY_Escape:
            if self._search_bar.get_search_mode():
                self._search.hide()
                return True
            if self.is_fullscreen():
                self.unfullscreen()
                return True
        return False

    # --- File Opening ---

    def open_file(self, filepath: str):
        """Open and render a Markdown file."""
        filepath = str(Path(filepath).resolve())

        # Read the file
        content = read_markdown_file(filepath)
        if content is None:
            self._show_error(
                "Cannot Open File",
                f"The file could not be read:\n{filepath}"
            )
            return

        self._current_file = filepath
        self._current_doc_dir = get_document_dir(filepath)

        # Update title
        title = get_document_title(filepath)
        self._title_widget.set_title(title)
        self._title_widget.set_subtitle(filepath)

        # Add to recent files
        self._preferences.add_recent_file(filepath)

        # Add to navigation history
        self._navigation_history.append(filepath)
        self._history_index = len(self._navigation_history) - 1

        # Render the document
        self._render_document(content)

    def _render_document(self, markdown_source: str):
        """Render Markdown content and display it."""
        style_manager = self.get_application().get_style_manager()
        is_dark = self._preferences.is_dark_theme(style_manager)

        # Clear CSS cache so theme changes take effect
        self._renderer.clear_cache()

        # Render to HTML
        html_content = self._renderer.render(
            markdown_source,
            doc_dir=self._current_doc_dir or '',
            dark_theme=is_dark,
        )

        # Load HTML into WebView
        if self._current_doc_dir:
            base_uri = Path(self._current_doc_dir).as_uri() + '/'
        else:
            base_uri = 'file:///'

        self._webview.load_html(html_content, base_uri)

        # Apply zoom
        self._webview.set_zoom_level(self._preferences.zoom_level)

        # Update TOC
        toc_data = self._renderer.get_toc_data()
        self._toc.build_from_toc_tokens(toc_data)

        # Enable TOC button if there are headings
        self._toc_button.set_sensitive(self._toc.has_entries)

        # Switch to document view
        self._content_stack.set_visible_child_name('document')

    def reload_document(self):
        """Reload the current document (e.g., after theme change)."""
        if self._current_file:
            content = read_markdown_file(self._current_file)
            if content:
                self._render_document(content)

    # --- Navigation Policy ---

    def _on_decide_policy(self, webview, decision, decision_type):
        """Handle navigation decisions in the WebView."""
        if decision_type == WebKit.PolicyDecisionType.NAVIGATION_ACTION:
            nav_action = decision.get_navigation_action()
            request = nav_action.get_request()
            uri = request.get_uri()

            if not uri:
                decision.use()
                return True

            # Allow about:blank and data: URIs (initial load)
            if uri.startswith(('about:', 'data:')):
                decision.use()
                return True

            # Allow file:// URIs for the document directory
            if uri.startswith('file://'):
                decoded_path = urllib.parse.unquote(
                    urllib.parse.urlparse(uri).path
                )
                # Allow loading the rendered HTML itself
                if nav_action.get_navigation_type() == WebKit.NavigationType.OTHER:
                    decision.use()
                    return True
                # Check if it's a local Markdown file
                if is_markdown_file(decoded_path) and Path(decoded_path).exists():
                    decision.ignore()
                    GLib.idle_add(self.open_file, decoded_path)
                    return True
                # Fragment-only navigation (anchor links)
                fragment = urllib.parse.urlparse(uri).fragment
                if fragment:
                    decision.use()
                    return True

            # External URLs — open in system browser
            if uri.startswith(('http://', 'https://', 'mailto:')):
                decision.ignore()
                if not is_dangerous_url(uri):
                    self._open_external_url(uri)
                return True

            # Block everything else
            decision.ignore()
            return True

        elif decision_type == WebKit.PolicyDecisionType.NEW_WINDOW_ACTION:
            # Block opening new windows
            nav_action = decision.get_navigation_action()
            request = nav_action.get_request()
            uri = request.get_uri()
            decision.ignore()
            if uri and not is_dangerous_url(uri):
                self._open_external_url(uri)
            return True

        decision.use()
        return True

    def _open_external_url(self, url: str):
        """Open a URL in the system's default browser."""
        if validate_external_url(url):
            try:
                launcher = Gtk.UriLauncher.new(url)
                launcher.launch(self, None, None)
            except Exception:
                pass

    # --- TOC ---

    def _on_toc_toggled(self, button):
        """Toggle the Table of Contents sidebar."""
        show = button.get_active()
        self._overlay_split.set_show_sidebar(show)

    def _on_split_show_sidebar_changed(self, split, pspec):
        """Keep the TOC header bar button state in sync."""
        is_showing = split.get_show_sidebar()
        if self._toc_button.get_active() != is_showing:
            self._toc_button.set_active(is_showing)

    def _scroll_to_heading(self, anchor_id: str):
        """Scroll the WebView to a heading by its anchor ID."""
        if anchor_id:
            import json
            id_json = json.dumps(anchor_id)
            js = f'''
            (function() {{
                var id = {id_json};
                var el = document.getElementById(id);
                if (!el) {{
                    try {{
                        el = document.querySelector('[id="' + CSS.escape(id) + '"]');
                    }} catch (e) {{}}
                }}
                if (el) {{
                    el.scrollIntoView({{ behavior: "smooth", block: "start" }});
                }}
            }})();
            '''
            self._webview.evaluate_javascript(js, -1, None, None, None, None, None)

    # --- Theme ---

    def _on_theme_changed(self, theme_mode: str):
        """Handle theme change."""
        style_manager = self.get_application().get_style_manager()
        self._preferences.apply_theme(style_manager)
        # Re-render with new theme
        self.reload_document()

    # --- Zoom ---

    def _on_zoom_changed(self, zoom_level: float):
        """Handle zoom level change."""
        self._webview.set_zoom_level(zoom_level)

    # --- Utilities ---

    def _show_error(self, title: str, message: str):
        """Show an error dialog."""
        dialog = Adw.AlertDialog(
            heading=title,
            body=message,
        )
        dialog.add_response('ok', 'OK')
        dialog.set_default_response('ok')
        dialog.present(self)

    def show_search(self):
        """Show the search bar."""
        self._search.show()

    def toggle_toc(self):
        """Toggle the TOC sidebar."""
        self._toc_button.set_active(not self._toc_button.get_active())

    def get_current_file(self) -> str:
        """Get the path of the currently open file."""
        return self._current_file
