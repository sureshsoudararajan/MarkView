#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Suresh Soundararajan
#
# build-appimage.sh — Build script to create MarkView-x86_64.AppImage
#
# ==============================================================================
# Host Dependencies Required to Build and Run the AppImage:
# ==============================================================================
# Build-time dependencies:
#   - bash (>= 4.0)
#   - curl or wget (for downloading appimagetool if not present)
#   - python3 (>= 3.10) with pip
#   - file (for MIME detection and packaging inspection)
#
# Runtime host system dependencies (provided by host desktop / distro):
#   - python3 (>= 3.10)
#   - python3-gi (PyGObject bindings)
#   - libgtk-4-1 (GTK 4.10+)
#   - libadwaita-1-0 (Libadwaita 1.4+)
#   - libwebkitgtk-6.0-4 (WebKitGTK 6.0)
#   - librsvg2-common (SVG icon rendering support)
#
# On Debian/Ubuntu systems, install build & runtime prerequisites with:
#   sudo apt install -y python3 python3-pip python3-gi gir1.2-gtk-4.0 \
#       gir1.2-adw-1 gir1.2-webkit-6.0 libgtk-4-dev libadwaita-1-dev \
#       libwebkitgtk-6.0-dev curl file
#
# On Fedora systems:
#   sudo dnf install -y python3 python3-pip python3-gobject gtk4 \
#       libadwaita webkitgtk6.0 curl file
#
# On Arch Linux systems:
#   sudo pacman -S python python-pip python-gobject gtk4 libadwaita \
#       webkitgtk-6.0 curl file
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${REPO_ROOT}/build/AppDir"
DIST_DIR="${REPO_ROOT}/dist"
TOOLS_DIR="${REPO_ROOT}/tools"
APP_ID="io.github.sureshsoundararajan.MarkView"
APP_NAME="MarkView"
ARCH="x86_64"
OUTPUT_IMAGE="${DIST_DIR}/${APP_NAME}-${ARCH}.AppImage"

echo "========================================================================"
echo " Building ${APP_NAME} ${ARCH} AppImage"
echo " Project Root: ${REPO_ROOT}"
echo "========================================================================"

# Step 1: Create AppDir directory structure
echo "==> [1/8] Preparing AppDir directory structure..."
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}/usr/bin"
mkdir -p "${BUILD_DIR}/usr/lib/markview"
mkdir -p "${BUILD_DIR}/usr/lib/python3/site-packages"
mkdir -p "${BUILD_DIR}/usr/share/markview"
mkdir -p "${BUILD_DIR}/usr/share/applications"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps"
mkdir -p "${BUILD_DIR}/usr/share/metainfo"
mkdir -p "${DIST_DIR}"
mkdir -p "${TOOLS_DIR}"

# Step 2: Copy Python source code to AppDir/usr/lib/markview/
echo "==> [2/8] Copying Python application source code..."
if [ -d "${REPO_ROOT}/src/markview" ]; then
    cp -r "${REPO_ROOT}/src/markview/"* "${BUILD_DIR}/usr/lib/markview/"
else
    echo "ERROR: Source directory ${REPO_ROOT}/src/markview not found!" >&2
    exit 1
fi

# Step 3: Install pip dependencies into AppDir/usr/lib/python3/site-packages/
echo "==> [3/8] Installing Python runtime dependencies into AppDir..."
PIP_CMD="pip3"
if [ -x "${REPO_ROOT}/.venv/bin/pip" ]; then
    PIP_CMD="${REPO_ROOT}/.venv/bin/pip"
fi

"${PIP_CMD}" install \
    --target="${BUILD_DIR}/usr/lib/python3/site-packages" \
    --upgrade \
    --no-compile \
    "markdown>=3.4" \
    "pymdown-extensions>=10.0" \
    "pygments>=2.15" \
    "bleach>=6.0"

# Step 4: Copy assets to AppDir/usr/share/markview/
echo "==> [4/8] Bundling web assets, styles, and templates..."
if [ -d "${REPO_ROOT}/assets" ]; then
    cp -r "${REPO_ROOT}/assets/"* "${BUILD_DIR}/usr/share/markview/"
else
    echo "Notice: No assets/ directory found at ${REPO_ROOT}/assets; creating empty placeholder."
    mkdir -p "${BUILD_DIR}/usr/share/markview"
fi

# Step 5: Copy desktop entry, icons, and metainfo
echo "==> [5/8] Copying desktop entry, icons, and AppStream metainfo..."
DESKTOP_SRC="${REPO_ROOT}/packaging/desktop/${APP_ID}.desktop"
METAINFO_SRC="${REPO_ROOT}/packaging/desktop/${APP_ID}.metainfo.xml"
ICON_SRC="${REPO_ROOT}/packaging/desktop/${APP_ID}.svg"

if [ ! -f "${ICON_SRC}" ] && [ -f "${REPO_ROOT}/test-data/images/logo.svg" ]; then
    ICON_SRC="${REPO_ROOT}/test-data/images/logo.svg"
fi

# Install desktop entry in standard path and at AppDir root
cp "${DESKTOP_SRC}" "${BUILD_DIR}/usr/share/applications/${APP_ID}.desktop"
cp "${DESKTOP_SRC}" "${BUILD_DIR}/${APP_ID}.desktop"

# Install application icon in standard theme path and at AppDir root
if [ -f "${ICON_SRC}" ]; then
    cp "${ICON_SRC}" "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps/${APP_ID}.svg"
    cp "${ICON_SRC}" "${BUILD_DIR}/${APP_ID}.svg"
    cp "${ICON_SRC}" "${BUILD_DIR}/.DirIcon"
fi

# Install AppStream metainfo
if [ -f "${METAINFO_SRC}" ]; then
    cp "${METAINFO_SRC}" "${BUILD_DIR}/usr/share/metainfo/${APP_ID}.metainfo.xml"
fi

# Step 6: Copy AppRun and ensure executable permissions
echo "==> [6/8] Installing AppRun entrypoint script..."
cp "${REPO_ROOT}/packaging/AppRun" "${BUILD_DIR}/AppRun"
chmod +x "${BUILD_DIR}/AppRun"

# Step 7: Download appimagetool if not present
echo "==> [7/8] Locating or downloading appimagetool..."
APPIMAGETOOL="${TOOLS_DIR}/appimagetool"

if command -v appimagetool &>/dev/null; then
    APPIMAGETOOL="$(command -v appimagetool)"
    echo "Found system appimagetool at: ${APPIMAGETOOL}"
elif [ ! -x "${APPIMAGETOOL}" ]; then
    echo "Downloading appimagetool-x86_64.AppImage to ${APPIMAGETOOL}..."
    TOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    if command -v curl &>/dev/null; then
        curl -fsSL -o "${APPIMAGETOOL}" "${TOOL_URL}"
    elif command -v wget &>/dev/null; then
        wget -qO "${APPIMAGETOOL}" "${TOOL_URL}"
    else
        echo "ERROR: Neither curl nor wget is available to download appimagetool." >&2
        exit 1
    fi
    chmod +x "${APPIMAGETOOL}"
fi

# Step 8: Run appimagetool to create MarkView-x86_64.AppImage
echo "==> [8/8] Generating final AppImage: ${OUTPUT_IMAGE}..."
export ARCH="x86_64"
export NO_STRIP=1
rm -f "${OUTPUT_IMAGE}"

# Run appimagetool (using --appimage-extract-and-run if executing an AppImage within container/environment)
if [ -x "${APPIMAGETOOL}" ]; then
    "${APPIMAGETOOL}" --appimage-extract-and-run "${BUILD_DIR}" "${OUTPUT_IMAGE}" || \
    "${APPIMAGETOOL}" "${BUILD_DIR}" "${OUTPUT_IMAGE}"
else
    echo "ERROR: appimagetool not executable at ${APPIMAGETOOL}" >&2
    exit 1
fi

echo "========================================================================"
echo " Build Completed Successfully!"
echo " AppImage created at: ${OUTPUT_IMAGE}"
echo "========================================================================"
