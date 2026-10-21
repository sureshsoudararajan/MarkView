#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Suresh Soundararajan
#
# install.sh — Installs MarkView AppImage and configures desktop integration
# (application menu, icons, MIME file associations)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "${SCRIPT_DIR}/src/markview" ]; then
    REPO_ROOT="${SCRIPT_DIR}"
else
    REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi
DIST_APPIMAGE="${REPO_ROOT}/dist/MarkView-x86_64.AppImage"

APP_ID="io.github.sureshsoundararajan.MarkView"
APP_NAME="MarkView"

# Target directories (user-level, no sudo required)
BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"
ICONS_DIR="${HOME}/.local/share/icons/hicolor"
METAINFO_DIR="${HOME}/.local/share/metainfo"

echo "========================================================================"
echo " Installing ${APP_NAME} for user: ${USER}"
echo "========================================================================"

# Check for built AppImage
if [ ! -f "${DIST_APPIMAGE}" ]; then
    echo "Notice: AppImage not found at ${DIST_APPIMAGE}."
    echo "Building AppImage first..."
    "${REPO_ROOT}/packaging/build-appimage.sh"
fi

if [ ! -f "${DIST_APPIMAGE}" ]; then
    echo "ERROR: Failed to find or build ${DIST_APPIMAGE}" >&2
    exit 1
fi

# Step 1: Install executable to ~/.local/bin/markview
echo "==> [1/5] Installing binary to ${BIN_DIR}/markview..."
mkdir -p "${BIN_DIR}"
cp -f "${DIST_APPIMAGE}" "${BIN_DIR}/markview"
chmod +x "${BIN_DIR}/markview"

# Step 2: Install icons to ~/.local/share/icons/hicolor/
echo "==> [2/5] Installing application icons..."
mkdir -p "${ICONS_DIR}/scalable/apps"
mkdir -p "${ICONS_DIR}/symbolic/apps"
mkdir -p "${ICONS_DIR}/48x48/apps"
mkdir -p "${ICONS_DIR}/128x128/apps"
mkdir -p "${ICONS_DIR}/256x256/apps"

ICON_SVG="${REPO_ROOT}/assets/icons/${APP_ID}.svg"
ICON_SYM="${REPO_ROOT}/assets/icons/${APP_ID}-symbolic.svg"

if [ -f "${ICON_SVG}" ]; then
    cp -f "${ICON_SVG}" "${ICONS_DIR}/scalable/apps/${APP_ID}.svg"
fi
if [ -f "${ICON_SYM}" ]; then
    cp -f "${ICON_SYM}" "${ICONS_DIR}/symbolic/apps/${APP_ID}-symbolic.svg"
fi

for size in 48x48 128x128 256x256; do
    PNG_SRC="${REPO_ROOT}/assets/icons/hicolor/${size}/apps/${APP_ID}.png"
    if [ -f "${PNG_SRC}" ]; then
        cp -f "${PNG_SRC}" "${ICONS_DIR}/${size}/apps/${APP_ID}.png"
    fi
done

# Step 3: Install .desktop file
echo "==> [3/5] Installing desktop entry to ${DESKTOP_DIR}..."
mkdir -p "${DESKTOP_DIR}"
cat > "${DESKTOP_DIR}/${APP_ID}.desktop" << EOF
[Desktop Entry]
Type=Application
Name=MarkView
GenericName=Markdown Viewer
Comment=A powerful, read-only Markdown viewer for Linux with rich GitHub-style rendering
Exec=${BIN_DIR}/markview %f
Icon=${APP_ID}
Categories=Utility;Viewer;
MimeType=text/markdown;text/x-markdown;
Terminal=false
StartupNotify=true
Keywords=markdown;viewer;document;reader;
EOF
chmod +x "${DESKTOP_DIR}/${APP_ID}.desktop"

# Step 4: Install AppStream metainfo
METAINFO_SRC="${REPO_ROOT}/packaging/desktop/${APP_ID}.metainfo.xml"
if [ -f "${METAINFO_SRC}" ]; then
    echo "==> [4/5] Installing AppStream metainfo..."
    mkdir -p "${METAINFO_DIR}"
    cp -f "${METAINFO_SRC}" "${METAINFO_DIR}/${APP_ID}.metainfo.xml"
fi

# Step 5: Update desktop database & caches
echo "==> [5/5] Updating desktop and icon caches..."
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true
fi

if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -q -t "${ICONS_DIR}" 2>/dev/null || true
fi

# Register default MIME handler for markdown
if command -v xdg-mime &>/dev/null; then
    xdg-mime default "${APP_ID}.desktop" text/markdown 2>/dev/null || true
    xdg-mime default "${APP_ID}.desktop" text/x-markdown 2>/dev/null || true
fi

echo "========================================================================"
echo " MarkView has been successfully installed!"
echo ""
echo " - Executable: ${BIN_DIR}/markview"
echo " - Desktop Entry: ${DESKTOP_DIR}/${APP_ID}.desktop"
echo " - Application Menu: MarkView will now appear in your app launcher"
echo " - Default Viewer: Registered for .md and .markdown files"
echo ""
if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    echo " Note: ${BIN_DIR} is not in your current PATH."
    echo " Add it by running: export PATH=\"\${HOME}/.local/bin:\$PATH\""
fi
echo "========================================================================"
