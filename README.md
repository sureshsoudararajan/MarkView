# MarkView

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![GTK 4](https://img.shields.io/badge/GTK-4.24-green.svg)](https://gtk.org/)
[![Libadwaita](https://img.shields.io/badge/Libadwaita-1.4%2B-orange.svg)](https://gnome.pages.gitlab.gnome.org/libadwaita/)
[![WebKitGTK](https://img.shields.io/badge/WebKitGTK-6.0-red.svg)](https://webkitgtk.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux-lightgrey.svg)](https://kernel.org/)

**MarkView** is a powerful, read-only Markdown viewer for Linux with rich GitHub-style rendering in a modern GNOME-inspired interface. Built from the ground up with GTK 4, Libadwaita, and WebKitGTK 6.0, MarkView provides desktop users with an authentic GitHub Flavored Markdown experience without the hazards of accidental file modification.

---

## Table of Contents

- [Why MarkView?](#why-markview)
- [Screenshots](#screenshots)
- [Features](#features)
- [Supported Markdown Features](#supported-markdown-features)
- [Design Limitations & Unsupported Features](#design-limitations--unsupported-features)
- [Installation](#installation)
  - [AppImage (Recommended)](#appimage-recommended)
  - [Desktop Integration](#desktop-integration)
- [Usage](#usage)
  - [Graphical Interface](#graphical-interface)
  - [Command-Line Interface](#command-line-interface)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Security Model](#security-model)
- [Building from Source](#building-from-source)
- [AppImage Packaging](#appimage-packaging)
- [Troubleshooting](#troubleshooting)
- [License & Author](#license--author)
- [Acknowledgements](#acknowledgements)

---

## Why MarkView?

Most markdown tools on Linux fall into one of two extremes: full-fledged code editors (which risk unintended keystrokes editing clean docs or dirtying git worktrees) or simple text previews that lack GitHub compatibility, math formatting, and diagram rendering.

MarkView is designed exclusively for **reading, reviewing, and reference**:

1. **Guaranteed Immutability** — MarkView has no editing buffer. Your notes, design documents, and changelogs remain pristine.
2. **Authentic GitHub Typography** — Rendered using modern CSS modeled after GitHub Flavored Markdown with support for light and dark themes.
3. **Desktop Harmony** — Fits seamlessly into GNOME and modern Linux desktops through Libadwaita widgets, adaptive layouts, and native theme detection.
4. **Sandboxed Security** — Untrusted documents cannot execute arbitrary JavaScript or escape document boundaries.

---

## Screenshots

<!-- Screenshot Placeholders -->
<div align="center">
  <p><em>MarkView in Light Mode (GitHub Theme)</em></p>
  <img src="https://raw.githubusercontent.com/sureshsoundararajan/MarkView/main/screenshots/markview-light.png" alt="MarkView Light Theme Preview" width="750" />
</div>

<div align="center">
  <p><em>MarkView in Dark Mode with KaTeX Math & Outline Sidebar</em></p>
  <img src="https://raw.githubusercontent.com/sureshsoundararajan/MarkView/main/screenshots/markview-dark.png" alt="MarkView Dark Theme Preview" width="750" />
</div>

---

## Features

- **Hardware-Accelerated Rendering**: Powered by WebKitGTK 6.0 for smooth scrolling, crisp typography, and sub-pixel antialiasing.
- **GitHub Flavored Markdown (GFM)**: Tables, task lists, strikethrough, autolinks, and GitHub callout alerts (`[!NOTE]`, `[!TIP]`, `[!IMPORTANT]`, `[!WARNING]`, `[!CAUTION]`).
- **Syntax Highlighting for 100+ Languages**: High-quality code highlighting via Pygments with language tags, line numbers, and horizontal scrolling.
- **Mathematical Notation (KaTeX)**: Lightning-fast rendering of inline math (`$E=mc^2$`) and display formulas without external network queries.
- **Diagrams & Visualizations (Mermaid.js)**: Flowcharts, sequence diagrams, and pie charts rendered directly from declarative text blocks.
- **Table of Contents Outline**: Interactive sidebar listing document headings with instant jump-to-section navigation.
- **Live File Watching**: Automatic, seamless document re-rendering when the source file is modified on disk using Linux inotify.
- **Adaptive Dark & Light Themes**: Follows system-wide GNOME / FreeDesktop dark preference with tailored color palettes for body, code, and math.
- **Zoom & Text Scaling**: Intuitive zoom controls (<kbd>Ctrl</kbd> + <kbd>+</kbd>, <kbd>Ctrl</kbd> + <kbd>-</kbd>, <kbd>Ctrl</kbd> + <kbd>0</kbd>) for accessibility.
- **Local Asset Resolution**: Resolves relative image paths (`images/banner.png`) safely relative to the active document directory.
- **Strict Multi-Layer Security**: Bleach HTML sanitization prevents Cross-Site Scripting (XSS), script injection, and path traversal vulnerabilities.

---

## Supported Markdown Features

| Feature Category | Markdown Syntax / Extension | Supported | Notes |
| :--- | :--- | :---: | :--- |
| **Headings** | `# H1` through `###### H6` | ✅ | Generates clean, slugified anchor IDs |
| **Duplicate Headings** | Identical heading text | ✅ | Disambiguated with numerical suffixes |
| **Inline Formatting** | `**bold**`, `*italic*`, `***both***` | ✅ | Supports both `*` and `_` markers |
| **Strikethrough** | `~~deleted text~~` | ✅ | GitHub Flavored Markdown standard |
| **Highlighted Text** | `==marked text==` | ✅ | PyMdown `mark` extension |
| **Keyboard Keys** | `<kbd>Ctrl</kbd> + <kbd>C</kbd>` | ✅ | Styled with native keycap borders |
| **Inline Code** | `` `code` `` | ✅ | Supports backticks inside double ticks |
| **Paragraphs & Breaks** | Trailing spaces or `\` | ✅ | Standard CommonMark wrapping and hard breaks |
| **External Links** | `[Title](https://...)` | ✅ | Opens safely in default system browser |
| **Relative Links** | `[Other Doc](notes.md)` | ✅ | Seamlessly navigates to target markdown file |
| **Anchor Links** | `[Jump](#target-section)` | ✅ | Smoothly scrolls to heading ID in page |
| **Autolinks** | `<https://...>`, `<mail@...>` | ✅ | Converted automatically to safe anchors |
| **Relative Images** | `![Alt](images/pic.png)` | ✅ | PNG, JPEG, SVG, WebP, GIF supported |
| **Missing Images** | `![Alt](missing.png)` | ✅ | Renders clean accessible fallback |
| **Unordered Lists** | `-`, `*`, `+` markers | ✅ | Indents up to arbitrary nesting levels |
| **Ordered Lists** | `1.`, `2.` and lazy `1.` | ✅ | Automatically sequences numbers correctly |
| **Task Lists** | `- [ ]` and `- [x]` | ✅ | Renders custom checkbox glyphs |
| **Code Blocks** | ` ```python ... ``` ` | ✅ | Pygments highlighting for 100+ languages |
| **Code Scrolling** | Extremely long code lines | ✅ | Horizontal scrollbars without breaking layout |
| **GFM Tables** | `\| Col 1 \| Col 2 \|` | ✅ | Full alignment: `:---`, `:---:`, `---:` |
| **Blockquotes** | `> quote` | ✅ | Nested quotes (`>>`) and rich inner elements |
| **GitHub Alerts** | `> [!NOTE]`, `> [!TIP]`, etc. | ✅ | All 5 alert types with standard accent badges |
| **Horizontal Rules** | `---`, `***`, `___` | ✅ | Thematic section divider styling |
| **Footnotes** | `[^1]` and `[^1]: text` | ✅ | Clickable jump links with return anchors |
| **Emoji Shortcodes** | `:smile:`, `:rocket:` | ✅ | PyMdown `emoji` extension mapping |
| **Unicode Glyphs** | 🚀, 🐧, 💻, 🦀, etc. | ✅ | Rendered with native system emoji fonts |
| **Inline Math** | `$E = mc^2$` | ✅ | KaTeX typesetting engine |
| **Display Math** | `$$\int_0^\infty ...$$` | ✅ | Centered display equations and matrices |
| **Mermaid Diagrams** | ` ```mermaid ... ``` ` | ✅ | Flowcharts, sequences, pie charts |
| **Character Escaping** | `\*`, `\_`, `\#`, `\[` | ✅ | Preserves literal punctuation characters |
| **Safe HTML** | `<div>`, `<span>`, `<details>` | ✅ | Safe semantic tags and classes permitted |

---

## Design Limitations & Unsupported Features

MarkView intentionally limits certain behaviors to guarantee document safety and consistent presentation:

- ❌ **No Document Editing**: MarkView is strictly a viewer. It does not provide text input areas, WYSIWYG editors, or save actions.
- ❌ **No Arbitrary JavaScript Execution**: User-authored `<script>` tags, inline event attributes (`onclick`, `onerror`, `onload`), and `javascript:` URIs are strictly stripped by Bleach.
- ❌ **No Remote Image Tracking**: By default, remote network images are blocked to safeguard user privacy against web beacons.
- ❌ **No Custom CSS Injections**: Raw `<style>` blocks and external `<link rel="stylesheet">` tags are sanitized to protect user interface styling integrity.
- ❌ **No Interactive Form Submissions**: `<form>`, `<input>`, and `<textarea>` elements cannot submit data to external endpoints.

---

## Installation

### AppImage (Recommended)

The standalone AppImage runs on any modern 64-bit Linux distribution (Ubuntu 22.04+, Fedora 38+, Arch, Debian 12+) without requiring root installation.

1. Download the latest `MarkView-x86_64.AppImage` from [Releases](https://github.com/sureshsoundararajan/MarkView/releases).
2. Make the AppImage executable:
   ```bash
   chmod +x MarkView-x86_64.AppImage
   ```
3. Run MarkView directly:
   ```bash
   ./MarkView-x86_64.AppImage [path/to/document.md]
   ```

### Automated Desktop Installation (One Command)

To automatically install MarkView into your desktop application menu, set up icons, create the `.desktop` file, and register MarkView as the default handler for Markdown files:

```bash
# Run the automated installer
./install.sh
```

This installs:
- **Binary**: `~/.local/bin/markview`
- **Application Menu**: `~/.local/share/applications/io.github.sureshsoundararajan.MarkView.desktop`
- **Icons**: SVG & PNG icons in `~/.local/share/icons/hicolor/`
- **File Associations**: Automatically registers `markview` for `.md` and `.markdown` files

To uninstall MarkView and remove desktop integration at any time:
```bash
./uninstall.sh
```

---

## Usage

### Graphical Interface

- **Open File**: Click the **Open** button in the header bar or press <kbd>Ctrl</kbd> + <kbd>O</kbd> to choose any `.md`, `.markdown`, `.mdown`, `.mkd`, or `.mdx` file.
- **Drag and Drop**: Drag any Markdown file from your file manager into the MarkView window to display it instantly.
- **Table of Contents**: Toggle the outline panel with the sidebar button or press <kbd>F9</kbd> to jump between document sections.
- **Theme Selection**: Toggle between system theme, light mode, or dark mode from the primary window menu.

### Command-Line Interface

Open files directly from your terminal:

```bash
# Open a specific file
markview README.md

# Open a document by absolute or relative path
markview /home/suresh/Documents/spec.markdown

# Launch empty window ready for file selection
markview
```

---

## Keyboard Shortcuts

| Action | Shortcut | Description |
| :--- | :--- | :--- |
| **Open File** | <kbd>Ctrl</kbd> + <kbd>O</kbd> | Open the file selection dialog |
| **Reload** | <kbd>Ctrl</kbd> + <kbd>R</kbd> or <kbd>F5</kbd> | Manually reload the active file from disk |
| **Toggle Sidebar** | <kbd>F9</kbd> | Show or hide the Table of Contents outline |
| **Zoom In** | <kbd>Ctrl</kbd> + <kbd>+</kbd> or <kbd>Ctrl</kbd> + <kbd>=</kbd> | Increase document font size |
| **Zoom Out** | <kbd>Ctrl</kbd> + <kbd>-</kbd> | Decrease document font size |
| **Reset Zoom** | <kbd>Ctrl</kbd> + <kbd>0</kbd> | Reset font size to default scale (100%) |
| **Find in Page** | <kbd>Ctrl</kbd> + <kbd>F</kbd> | Search for text within the current document |
| **Copy Text** | <kbd>Ctrl</kbd> + <kbd>C</kbd> | Copy selected text to the system clipboard |
| **Print / Export PDF** | <kbd>Ctrl</kbd> + <kbd>P</kbd> | Print or export the rendered document to PDF |
| **Close / Quit** | <kbd>Ctrl</kbd> + <kbd>Q</kbd> or <kbd>Ctrl</kbd> + <kbd>W</kbd> | Close active window or exit MarkView |

---

## Security Model

MarkView views untrusted Markdown files from external sources safely through a defense-in-depth architecture:

1. **Path Traversal Protection**: Relative links and image paths are validated against the document directory. Requests attempting directory escapes (`../../etc/passwd`) are discarded.
2. **HTML Sanitization (Bleach)**: Raw HTML parsed from Markdown is filtered against a strict tag and attribute allowlist. Potentially dangerous tags (`<script>`, `<iframe>`, `<object>`, `<embed>`) and inline event handlers (`onclick`, `onerror`, `onload`) are neutralized.
3. **WebKitGTK Process Sandboxing**: Rendered HTML executes inside an isolated WebKit subprocess. WebGL and remote plugins are disabled.
4. **Content Security Policy (CSP)**: A strict CSP header prevents inline script evaluation, restricts style origins, and blocks unauthorized cross-origin requests.
5. **Safe URL Schemes**: External links only trigger for safe protocols (`http:`, `https:`, `mailto:`, `ftp:`). Malicious protocols (`javascript:`, `vbscript:`, `data:`, `blob:`) are blocked.

---

## Building from Source

### Prerequisites

Ensure system development libraries and Python 3.10+ are installed:

#### Ubuntu 24.04 / Debian 12
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-gi \
    gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-webkit-6.0 \
    libgtk-4-dev libadwaita-1-dev libwebkitgtk-6.0-dev
```

#### Fedora 40 / 41
```bash
sudo dnf install -y python3 python3-pip python3-gobject \
    gtk4 libadwaita webkitgtk6.0 gtk4-devel libadwaita-devel webkitgtk6.0-devel
```

#### Arch Linux
```bash
sudo pacman -S python python-pip python-gobject gtk4 libadwaita webkitgtk-6.0
```

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/sureshsoundararajan/MarkView.git
   cd MarkView
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv --system-site-packages
   source .venv/bin/activate
   ```
   *(Note: `--system-site-packages` is recommended so the virtual environment accesses system PyGObject bindings).*

3. Install project dependencies in development mode:
   ```bash
   pip install -e .
   ```

4. Launch MarkView with the comprehensive test suite:
   ```bash
   python3 -m markview test-data/markdown-test-suite.md
   ```

---

## AppImage Packaging

MarkView includes an automated packaging script to produce self-contained AppImage bundles:

```bash
# Make sure the script is executable
chmod +x packaging/build-appimage.sh

# Run the build script
./packaging/build-appimage.sh
```

The script performs the following tasks:
1. Prepares the `build/AppDir` hierarchy.
2. Copies application source code into `usr/lib/markview`.
3. Installs standalone Python library dependencies into `usr/lib/python3/site-packages`.
4. Copies web assets, templates, icons, desktop files, and AppStream metadata.
5. Downloads the latest verified `appimagetool` (if not already installed).
6. Packages the output image to `dist/MarkView-x86_64.AppImage`.

---

## Troubleshooting

### WebKitGTK Compositing / Driver Issues
On some virtual machines or older GPUs, WebKitGTK may display a blank or flickering screen. Disable hardware compositing by setting:
```bash
export WEBKIT_DISABLE_COMPOSITING_MODE=1
markview document.md
```

### Missing PyGObject Typelibs
If you receive an error such as `Namespace Adw not available` or `Namespace WebKit not available`:
- Debian/Ubuntu: `sudo apt install gir1.2-adw-1 gir1.2-webkit-6.0`
- Fedora: `sudo dnf install libadwaita webkitgtk6.0`

### Display Server Issues (Wayland vs X11)
To force X11 backend fallback on systems with Wayland driver quirks:
```bash
GDK_BACKEND=x11 markview document.md
```

---

## License & Author

- **Author**: Suresh Soundararajan
- **License**: MIT License — see the [LICENSE](LICENSE) file for complete details.
- **Copyright**: &copy; 2026 Suresh Soundararajan

---

## Acknowledgements

MarkView builds on exceptional work by the open-source community:
- [GTK 4](https://gtk.org/) and [Libadwaita](https://gnome.pages.gitlab.gnome.org/libadwaita/) — Modern GNOME desktop framework
- [WebKitGTK](https://webkitgtk.org/) — Fast, secure open-source browser engine
- [Python-Markdown](https://python-markdown.github.io/) — Markdown parser engine
- [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/) — Advanced GFM syntax extensions
- [Pygments](https://pygments.org/) — Syntax highlighter for 100+ programming languages
- [Bleach](https://bleach.readthedocs.io/) — HTML sanitizing library by Mozilla
- [KaTeX](https://katex.org/) — Fast mathematical typesetting library
- [Mermaid.js](https://mermaid.js.org/) — JavaScript diagramming and charting tool
- [github-markdown-css](https://github.com/sindresorhus/github-markdown-css) — Inspiration for GitHub typography styles

See [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) for full license texts and copyright notices.
