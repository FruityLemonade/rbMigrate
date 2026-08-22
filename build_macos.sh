#!/usr/bin/env bash
#
# Build the rbMigrate macOS application (.app) and disk image (.dmg).
#
# PyInstaller needs a Python that has tkinter compiled in (the GUI's UI
# toolkit). The system python.org "framework" build ships tkinter; Homebrew's
# CLI builds often do not. This script picks a suitable interpreter:
#
#   1. If .venv/bin/python already exists (a working venv), reuse it.
#   2. Otherwise create .venv from the best available system Python
#      (prefer a python that can import _tkinter).
#
# Usage:
#   ./build_macos.sh
#
set -euo pipefail

cd "$(dirname "$0")"

STAMP="$(date +%Y%m%d_%H%M%S)"
VENV_DIR=".venv"
DIST_DIR="dist"
DMG_NAME="rbMigrate-${STAMP}.dmg"
APP_BUNDLE="${DIST_DIR}/rbMigrate.app"

echo "==> Preparing Python environment..."

pick_base_python() {
    # Return a python binary that can import _tkinter, else the default.
    local default
    default="$(command -v python3 || echo python3)"
    for cand in \
        /Library/Frameworks/Python.framework/Versions/*/bin/python3 \
        "$(command -v python3.12 || true)" \
        "$(command -v python3.11 || true)" \
        "$(command -v python3.10 || true)" \
        "$(command -v python3.9 || true)" \
        "$(command -v python3.8 || true)" \
        "$default"
    do
        [ -x "$cand" ] || continue
        if "$cand" -c "import _tkinter" >/dev/null 2>&1; then
            echo "$cand"
            return 0
        fi
    done
    echo "$default"
}

if [ -x "${VENV_DIR}/bin/python" ]; then
    echo "    Using existing virtual environment at ${VENV_DIR}"
    PYTHON="${VENV_DIR}/bin/python"
else
    BASE="$(pick_base_python)"
    echo "    Creating virtual environment from $BASE ..."
    "$BASE" -m venv "${VENV_DIR}"
    PYTHON="${VENV_DIR}/bin/python"
fi

echo "==> Installing build and runtime dependencies..."
"${PYTHON}" -m pip install --upgrade pip
"${PYTHON}" -m pip install -r requirements.txt -r requirements-dev.txt

echo "==> Building the application with PyInstaller..."
rm -rf build "${DIST_DIR}"
"${PYTHON}" -m PyInstaller --noconfirm rbMigrate.spec

if [ ! -d "${APP_BUNDLE}" ]; then
    echo "ERROR: expected PyInstaller output not found at ${APP_BUNDLE}" >&2
    exit 1
fi
echo "    Bundle built: ${APP_BUNDLE}"

echo "==> Creating disk image (.dmg)..."
STAGING_DIR="${DIST_DIR}/staging"
rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}"
cp -R "${APP_BUNDLE}" "${STAGING_DIR}/"

if hdiutil create \
    -volname "rbMigrate" \
    -srcfolder "${STAGING_DIR}" \
    -ov \
    -format UDZO \
    "${DIST_DIR}/${DMG_NAME}" 2>/dev/null; then
    rm -rf "${STAGING_DIR}"
    echo ""
    echo "Done!"
    echo "  App: ${DIST_DIR}/rbMigrate.app"
    echo "  DMG: ${DIST_DIR}/${DMG_NAME}"
else
    echo ""
    echo "  App built: ${DIST_DIR}/rbMigrate.app"
    echo "  WARNING: could not create the .dmg (${DMG_NAME})."
    echo "  The .dmg step requires macOS disk-image privileges. You can"
    echo "  either run this script on your normal Mac session, or drag"
    echo "  ${APP_BUNDLE} into your Applications folder directly."
    rm -rf "${STAGING_DIR}"
fi
