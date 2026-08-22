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

# For Intel build, download a pre-built x86_64 Python
PYTHON_INTEL=""
VENV_INTEL_DIR=".venv-intel"

if [ ! -d "${VENV_INTEL_DIR}" ]; then
    echo "    Downloading x86_64 Python 3.11 for Intel build..."
    # Use latest release from astral-sh/python-build-standalone
    PYTHON_INTEL_URL="https://github.com/astral-sh/python-build-standalone/releases/download/20260814/cpython-3.11.16%2B20260814-x86_64-apple-darwin-install_only.tar.gz"
    TEMP_DIR=$(mktemp -d)
    cd "${TEMP_DIR}"
    
    # Download x86_64 Python
    curl -L -o python.tar.gz "${PYTHON_INTEL_URL}"
    tar -xzf python.tar.gz
    
    # Create venv using the downloaded x86_64 Python
    cd "${TEMP_DIR}/python/bin"
    ./python3 -m venv "${TEMP_DIR}/venv-intel"
    
    cd - > /dev/null
    rm -rf "${TEMP_DIR}"
    
    # Move venv to project root
    mv "${TEMP_DIR}/venv-intel" "${VENV_INTEL_DIR}"
    PYTHON_INTEL="${VENV_INTEL_DIR}/bin/python"  # Update to new location
    
    echo "    Installing dependencies into x86_64 venv..."
    "${PYTHON_INTEL}" -m pip install --upgrade pip
    "${PYTHON_INTEL}" -m pip install -r requirements.txt -r requirements-dev.txt
else
    echo "    Using existing Intel venv at ${VENV_INTEL_DIR}"
    PYTHON_INTEL="${VENV_INTEL_DIR}/bin/python"
fi

echo "==> Building applications with PyInstaller..."

# Generate spec files for each architecture
echo "    Generating spec files..."
python3 generate_specs.py

# Build ARM64 only (native on Apple Silicon)
echo "    Building macos-arm..."
rm -rf build "${DIST_DIR}"
"${PYTHON}" -m PyInstaller --noconfirm rbMigrate-arm.spec
mv "${DIST_DIR}/rbMigrate.app" "${DIST_DIR}/rbMigrate-arm.app"
echo "      Bundle built: ${DIST_DIR}/rbMigrate-arm.app"

# Build Intel only using Rosetta
echo "    Building macos-intel (using Rosetta)..."
# Create x86_64 virtual environment for Intel build
VENV_INTEL_DIR=".venv-intel"
if [ -x "${VENV_INTEL_DIR}/bin/python" ]; then
    echo "    Using existing Intel venv at ${VENV_INTEL_DIR}"
    PYTHON_INTEL="${VENV_INTEL_DIR}/bin/python"
else
    echo "    Creating x86_64 virtual environment for Intel build..."
    # Use arch -x86_64 to create an x86_64 venv
    arch -x86_64 python3 -m venv "${VENV_INTEL_DIR}"
    PYTHON_INTEL="${VENV_INTEL_DIR}/bin/python"
fi
"${PYTHON_INTEL}" -m pip install --upgrade pip
"${PYTHON_INTEL}" -m pip install -r requirements.txt -r requirements-dev.txt
rm -rf build "${DIST_DIR}"
arch -x86_64 "${PYTHON_INTEL}" -m PyInstaller --noconfirm rbMigrate-intel.spec
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
