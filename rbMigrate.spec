# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for the rbMigrate GUI.
#
# Builds a windowed (no console) app on macOS (.app) / Windows (.exe).
#
# Usage:
#   macOS:  pyinstaller rbMigrate.spec
#   Windows:pyinstaller rbMigrate.spec

from PyInstaller.utils.hooks import collect_all
import sys

# PyInstaller doesn't put the spec's directory on sys.path when it execs
# this file; SPECPATH is a built-in spec global pointing at that directory.
sys.path.insert(0, SPECPATH)

from version import APP_VERSION

block_cipher = None

# PyInstaller ships dedicated hooks for sqlalchemy, lxml, mutagen, and psutil,
# so we only need to explicitly bundle the two obscure packages that rbMigrate
# imports lazily at runtime:
#   - pyrekordbox  (Rekordbox database library; loaded inside methods)
#   - sqlcipher3   (SQLCipher wrapper; ships a C extension + dynamic library)
datas = []
binaries = []
hiddenimports = []

for name in ("pyrekordbox", "sqlcipher3"):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(
        name, include_py_files=True)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

# Explicit hidden imports PyInstaller's static analysis misses because the
# rbMigrate script imports them lazily inside methods.
hiddenimports += [
    "pyrekordbox.db6",
    "pyrekordbox.db6.tables",
]

a = Analysis(
    ["rbMigrate_gui.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="rbMigrate",
    icon="app_icon.ico",  # Windows icon
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # windowed app, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,  # Set via spec file generation script
    codesign_identity=None,
    entitlements_file=None,
)

# macOS app bundle wrapper (a no-op collection on Windows; pyinstaller
# produces dist\rbMigrate.exe directly).
app = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="rbMigrate",
)

# On macOS, wrap COLLECT into a double-clickable .app bundle with an
# Info.plist. PyInstaller arranges Contents/MacOS/rbMigrate as the launcher.
if sys.platform == "darwin":
    app = BUNDLE(
        app,
        name="rbMigrate.app",
        icon="app_icon.icns",
        bundle_identifier="com.rbmigrate.app",
        info_plist={
            "NSHighResolutionCapable": True,
            "NSHumanReadableCopyright": "rbMigrate",
            "CFBundleShortVersionString": APP_VERSION,
            "CFBundleVersion": APP_VERSION,
        },
    )
