#!/usr/bin/env bash
#
# Build the rbMigrate macOS application (.app) and disk images (.dmg).
#
# Builds three versions:
#   1. macos-arm - Apple Silicon only
#   2. macos-intel - Intel only
#   3. macos-universal - Both architectures
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

echo "==> Building applications with PyInstaller..."

# Generate spec files for each architecture
echo "    Generating spec files..."
python3 generate_specs.py

# Build ARM64 only
echo "    Building macos-arm..."
rm -rf build "${DIST_DIR}"
"${PYTHON}" -m PyInstaller --noconfirm rbMigrate-arm.spec
mv "${DIST_DIR}/rbMigrate.app" "${DIST_DIR}/rbMigrate-arm.app"
echo "      Bundle built: ${DIST_DIR}/rbMigrate-arm.app"

# Build Intel only
echo "    Building macos-intel..."
rm -rf build "${DIST_DIR}"
"${PYTHON}" -m PyInstaller --noconfirm rbMigrate-intel.spec
mv "${DIST_DIR}/rbMigrate.app" "${DIST_DIR}/rbMigrate-intel.app"
echo "      Bundle built: ${DIST_DIR}/rbMigrate-intel.app"

# Build Universal2 (both architectures)
echo "    Building macos-universal..."
rm -rf build "${DIST_DIR}"
"${PYTHON}" -m PyInstaller --noconfirm rbMigrate-universal.spec
mv "${DIST_DIR}/rbMigrate.app" "${DIST_DIR}/rbMigrate-universal.app"
echo "      Bundle built: ${DIST_DIR}/rbMigrate-universal.app"

# Create DMGs
echo "==> Creating disk images (.dmg)..."

for app in "${DIST_DIR}/rbMigrate-"*.app; do
    APP_NAME=$(basename "${app}" .app)
    DMG_NAME="${DIST_DIR}/${APP_NAME}-${STAMP}.dmg"
    STAGING_DIR="${DIST_DIR}/staging-${APP_NAME}"
    
    rm -rf "${STAGING_DIR}"
    mkdir -p "${STAGING_DIR}"
    cp -R "${app}" "${STAGING_DIR}/"
    
    if hdiutil create \
        -volname "rbMigrate" \
        -srcfolder "${STAGING_DIR}" \
        -ov \
        -format UDZO \
        "${DMG_NAME}" 2>/dev/null; then
        rm -rf "${STAGING_DIR}"
        echo ""
        echo "Done!"
        echo "  ${APP_NAME}: ${DMG_NAME}"
    else
        echo ""
        echo "  ${APP_NAME}: ${STAGING_DIR}/${APP_NAME}.app"
        echo "  WARNING: could not create the .dmg (${DMG_NAME})."
        echo "  The .dmg step requires macOS disk-image privileges. You can"
        echo "  either run this script on your normal Mac session, or drag"
        echo "  ${app} into your Applications folder directly."
        rm -rf "${STAGING_DIR}"
    fi
done
