#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Suresh Soundararajan
#
# uninstall.sh — Removes MarkView installation and desktop integration

set -euo pipefail

APP_ID="io.github.sureshsoundararajan.MarkView"
BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"
ICONS_DIR="${HOME}/.local/share/icons/hicolor"
METAINFO_DIR="${HOME}/.local/share/metainfo"

echo "Uninstalling MarkView..."

rm -f "${BIN_DIR}/markview"
rm -f "${DESKTOP_DIR}/${APP_ID}.desktop"
rm -f "${METAINFO_DIR}/${APP_ID}.metainfo.xml"
rm -f "${ICONS_DIR}/scalable/apps/${APP_ID}.svg"
rm -f "${ICONS_DIR}/symbolic/apps/${APP_ID}-symbolic.svg"
for size in 48x48 128x128 256x256; do
    rm -f "${ICONS_DIR}/${size}/apps/${APP_ID}.png"
done

if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true
fi

if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -q -t "${ICONS_DIR}" 2>/dev/null || true
fi

echo "MarkView uninstalled successfully."
