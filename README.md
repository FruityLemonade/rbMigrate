# rbMigrate - an Alpha Theta Rekordbox Path Updater

rbMigrate is a tool to update file paths in your Rekordbox database after moving your music collection. It automatically updates the `FolderPath` field in the `DjmdContent` table and optionally updates XML playlist files. Useful for exporting your Rekordbox library to an external drive or new computer. Confirmed working with rekordbox v7.x. but should also work with v.5.8. and v.6.x.

**Recommended:** Download the prebuilt GUI app from the [Releases](../../releases) page — no Python installation required.

<img width="804" height="760" alt="Screenshot 2026-08-22 at 14 45 08" src="https://github.com/user-attachments/assets/a2273565-83b0-4d3a-b2e3-fee18f188f7e" />


## Features

- ⭐️ **Automatic Path Replacement**: Updates all file paths in the database
- ⭐️ **Safety Features**:
  - Automatic backup creation before changes
  - Preview mode to see changes before applying them
  - File existence validation
- ⭐️ **Simple GUI**: Point-and-click wizard (macOS `.app` / Windows `.exe`) — recommended for most users
- ⭐️ **CLI Tool**: Command-line interface for advanced users
- ⭐️ **Flexible Configuration**:
  - Auto-detection of database location
  - Detailed reporting with live log pane
- ⭐️ **XML Support**: Optionally updates XML playlist metadata

## Dependencies

This project relies on the following open-source libraries:

- **[pyrekordbox](https://github.com/dylanljones/pyrekordbox)** - Rekordbox database library for Python
- **[sqlcipher3](https://github.com/coleifer/sqlcipher3)** - SQLite3 wrapper with SSL support
- **[lxml](https://lxml.de/)** - XML and HTML parsing library
- **[mutagen](https://github.com/quodlibet/mutagen)** - Audio metadata handling
- **[sqlalchemy](https://www.sqlalchemy.org/)** - SQL toolkit and ORM
- **[psutil](https://psutil.net/)** - Cross-platform process and system utilities

## Requirements

- Python 3.8 or higher
- pyrekordbox >= 0.4.0
- sqlcipher3 (required for database access)

## Downloads from Releases (Recommended)

**Get the prebuilt app — no Python installation required.**

Download the latest release from the [Releases](../../releases) page:

| Platform | Download | Quick Start |
|----------|----------|-------------|
| **macOS** | `rbMigrate-arm-v*-*.dmg` (Apple Silicon M1–M4) or `rbMigrate-intel-v*-*.dmg` (Intel Macs) | 1. Double-click to open 2. Drag to Applications 3. Launch from Applications |
| **Windows** | `rbMigrate.exe` | 1. Run the installer 2. Launch from Start menu |

> **macOS users:** the first launch shows an *"Apple could not verify…"* security
> prompt. This is expected for unsigned apps — see
> [Opening rbMigrate on macOS](#opening-rbmigrate-on-macos) for a 30-second fix.

**What's included:**
- All dependencies (pyrekordbox, sqlcipher3, tkinter, etc.)
- Ready to run — no Python setup needed
- Verified on the target platform

## Opening rbMigrate on macOS

rbMigrate is not signed with an Apple Developer certificate, so macOS Gatekeeper
blocks the first launch with:

> **"Apple could not verify "rbMigrate-intel" is free of malware that may harm
> your Mac or compromise your privacy."**

This warning appears for *any* app distributed outside the App Store without a
paid Apple developer notarization — it does not mean the app is malware. rbMigrate
is open source, so you can audit everything it does in this repository. To open
it anyway:

### Method 1: System Settings (recommended)

1. When the warning appears, click **Done** (do *not* click *Move to Trash*).
2. Open **System Settings → Privacy & Security**.
3. Scroll down to the **Security** section and find this message:
   > `"rbMigrate-intel" was blocked from use because it is not from an identified developer.`
4. Click **Allow Anyway**, then authenticate with your password or Touch ID.
5. Launch the app again. A second dialog appears asking if you're sure —
   click **Open**.

The app opens normally, and macOS won't ask again for this version.

### Method 2: Terminal one-liner

The block is caused by the quarantine attribute macOS adds to downloaded files.
Remove it once and launch normally afterwards:

```bash
xattr -dr com.apple.quarantine /Applications/rbMigrate-intel.app
```

Adjust the path if you run the app from somewhere else (e.g. `~/Downloads`).

> **Not sure which download you need?**
> Click the Apple menu () → *About This Mac*. If the Chip/Processor line says
> *Apple M1/M2/M3/M4*, use `rbMigrate-arm`; if it says *Intel*, use `rbMigrate-intel`.

## Installation

### Option 1: Download from Releases (Recommended)

See [Downloads from Releases](#downloads-from-releases--recommended) above for platform-specific instructions.

### Option 2: Build from Source

If you prefer to build the app yourself, or need to customize it:

#### Prerequisites

- **macOS**: Python 3.8+ with tkinter (the build script creates its own venv)
- **Windows**: Python 3.8+ (the build script creates its own venv)

#### Build Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/rbMigrate.git
   cd rbMigrate
   ```

2. **Build the app** (macOS)
   ```bash
   ./build_macos.sh
   ```
   Produces `dist/rbMigrate.app` and `dist/rbMigrate-<timestamp>.dmg`.

3. **Build the app** (Windows)
   ```bat
   build_windows.bat
   ```
   Produces `dist\rbMigrate.exe`.

4. **Run from source** (optional)
   ```bash
   python rbMigrate_gui.py
   ```

See [Building a Distributable App](#building-a-distributable-app) for details.

## GUI App

The GUI is the recommended interface — a simple, point-and-click wizard with all the features you need.

### Key Features

**Database selection**
- `Browse…` — open a file picker to select your Rekordbox `master.db`
- `Auto-detect` — automatically finds your database location (works on most systems)
- The file picker now correctly shows files ending in `.db` (not `.master.db`)

**Path management**
- Browse for old and new music folders
- Real-time validation — the app checks that paths exist before proceeding
- Path suggestions based on your OS (e.g., `~/Library/Application Support/Pioneer DJ/Rekordbox/Master/` on macOS)

**Safety controls**
- **Preview mode** — see exactly what will change before applying anything
- **Backup creation** — automatic timestamped backup before each update
- **Update DB** — apply the changes to your database

**XML playlist metadata**
- **Update XML** — optionally update XML playlist files (`masterPlaylists6.xml`, `automixPlaylist6.xml`)
- When enabled, the app checks for XML files in the same directory as your database
- If XML files don't exist, the toggle has no effect and 0 files are reported as updated
- XML files are only updated with the product version to ensure consistency with the database

**Live feedback**
- Real-time log pane showing exactly what the engine is doing
- Progress indicators for each step
- Clear success/error messages

### Using the GUI

**Quick workflow:**
1. Click **Preview changes** (default)
2. Review the summary in the log pane
3. If everything looks correct, click **Update DB**
4. Confirm the update when prompted
5. Close Rekordbox before updating to avoid database locks

**Safety tips:**
- Always run **Preview** first to see what will change
- The app creates a backup automatically (unless you disable it)
- Missing files at the new location are reported — the app won't update them
- You can cancel at any time during the update process

### Running from source

If you prefer to run the GUI directly from source:

```bash
python rbMigrate_gui.py
```

This is useful if you want to customize the code or develop new features.

**Note:** The GUI is deliberately simple. For advanced use cases (custom database paths on the command line, verbose output, force mode), use the CLI tool instead.

## Building a Distributable App

Prebuilt installers can be built with **PyInstaller**. PyInstaller does **not**
cross-compile, so:
- The **macOS** build must run on a Mac.
- The **Windows** build must run on Windows (or Windows CI).

### Prerequisites

- Python 3.8+ (the build creates its own venv)
- The runtime dependencies install automatically via `requirements.txt`
- `pyinstaller` (listed in `requirements-dev.txt`)

### macOS

```bash
./build_macos.sh
```

Produces `dist/rbMigrate.app` and `dist/rbMigrate-<timestamp>.dmg`.

### Windows

Run on a Windows machine:

```bat
build_windows.bat
```

Produces `dist\rbMigrate.exe`.

### Automatically on GitHub (recommended for the .exe)

If you don't have a Windows machine, push this repo to GitHub and the included
workflow (`.github/workflows/build.yml`) builds **both** the macOS app and the
Windows `.exe` on every push (and on demand via *Actions → Build → Run
workflow*). Download them from the workflow's *Artifacts* section. GitHub's
Windows runners typically come with a SQLCipher-compatible toolchain, and the
build script installs the remaining dependencies.

## Setup

### Option 1: Interactive Mode (Recommended for First Use)

Run the script without arguments to interactively set up the paths:

```bash
python rbMigrate.py
```

The script will prompt you for:
- Old file path (e.g., `~/path/to/old/musiclibrary/`)
- New file path (e.g., `/path/to/new/musiclibrary`)

### Option 2: Command-Line Mode

Specify all paths directly on the command line:

```bash
python rbMigrate.py \
    --old-path "~/path/to/old/musiclibrary" \
    --new-path "/path/to/new/musiclibrary"
```

## Usage

### Basic Usage

```bash
python rbMigrate.py \
    --old-path "~/path/to/old/musiclibrary" \
    --new-path "/path/to/new/musiclibrary"
```

### Dry-Run Mode

Preview what will change without modifying anything:

```bash
python rbMigrate.py \
    --old-path "~/path/to/old/musiclibrary" \
    --new-path "/path/to/new/musiclibrary" \
    --dry-run
```

### With Backup and XML Update

Enable automatic backup and XML metadata updates:

```bash
python rbMigrate.py \
    --old-path "~/path/to/old/musiclibrary" \
    --new-path "/path/to/new/musiclibrary" \
    --backup \
    --update-xml
```

### Custom Database Path

Specify a custom database location:

```bash
python rbMigrate.py \
    --db-path "/path/to/PIONEER/Master/master.db" \
    --old-path "~/path/to/old/musiclibrary" \
    --new-path "/path/to/new/musiclibrary"
```

### Verbose Output

Show detailed progress information:

```bash
python rbMigrate.py \
    --old-path "~/path/to/old/musiclibrary" \
    --new-path "/path/to/new/musiclibrary" \
    --verbose
```

### Disable Backup

Skip automatic backup creation (not recommended):

```bash
python rbMigrate.py \
    --old-path "~/path/to/old/musiclibrary" \
    --new-path "/path/to/new/musiclibrary" \
    --no-backup
```

## Command-Line Options

| Option | Description | Required |
|--------|-------------|----------|
| `--db-path` | Path to Rekordbox database (master.db) | No (auto-detected) |
| `--old-path` | Old file path to replace | Yes |
| `--new-path` | New file path | Yes |
| `--dry-run` | Preview changes without modifying | No |
| `--no-backup` | Disable automatic backup | No |
| `--update-xml` | Update XML playlist metadata | No |
| `--verbose` | Show detailed output | No |

## How It Works

### Database Update

The script uses the `pyrekordbox` library to access the Rekordbox database:

1. **Connects to database**: Uses `Rekordbox6Database` class
2. **Queries tracks**: Finds all tracks where `FolderPath` starts with the old path
3. **Validates files**: Checks if files exist at the new location
4. **Updates paths**: Modifies the `FolderPath` field for each track
5. **Commits changes**: Saves changes to the database

### XML Update

The script optionally updates XML playlist files (`masterPlaylists6.xml`, `automixPlaylist6.xml`):

- Updates the product version to ensure consistency
- Maintains compatibility with Rekordbox
- Does not modify file paths (XML files don't store them)

**When XML files are missing:**

If the "Update XML" toggle is enabled but no XML files exist in the database directory:
- The app silently skips the update
- 0 files are reported as updated in the log
- No error or warning is raised
- This is expected behavior when you have a fresh database with no playlist files

**How it works:**

The XML files are located in the same directory as your `master.db` file:
- macOS: `~/Library/Pioneer/rekordbox/masterPlaylists6.xml`
- macOS: `~/Library/Pioneer/rekordbox/automixPlaylist6.xml`
- Windows: `C:\Users\<username>\AppData\Roaming\Pioneer DJ\Rekordbox\masterPlaylists6.xml`

The app only updates XML files that actually exist on your system.

### Backup

Automatic backup creation:
- Timestamped filename: `master.db.backup_YYYYMMDD_HHMMSS`
- Stored in the same directory as the database
- Safe to keep multiple backups

## Troubleshooting

### macOS: "Apple could not verify 'rbMigrate-intel'…" when launching the app

Gatekeeper blocks unsigned apps on first launch — this is expected, not malware.
Follow the steps in [Opening rbMigrate on macOS](#opening-rbmigrate-on-macos).

### Error: "Required package not found: pyrekordbox"

**Solution**: Install the required package:

```bash
pip install pyrekordbox sqlcipher3
```

### Error: "'sqlcipher3' package not found"

**Solution**: Install sqlcipher3:

```bash
pip install sqlcipher3
```

### Error: Permission denied when installing packages

**Solution**: Use a virtual environment (recommended):

```bash
python3.11 -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install pyrekordbox sqlcipher3
python rbMigrate.py ...
```

### Error: "Could not auto-detect database"

**Solution**: Specify the database path manually:

```bash
python rbMigrate.py \
    --db-path "/path/to/PIONEER/Master/master.db" \
    --old-path "~/path/to/old/musiclibrary" \
    --new-path "/path/to/new/musiclibrary"
```

### Warning: "Old path does not exist"

**Solution**: Verify the path is correct. If the path is correct, you can continue:

```bash
python rbMigrate.py \
    --old-path "~/path/to/old/musiclibrary" \
    --new-path "/path/to/new/musiclibrary"
```

The script will ask for confirmation before proceeding.

### Error: "File does not exist at new location"

**Solution**: Ensure your music files are actually at the new location. The script will skip files that don't exist:

- Tracks with missing files will be skipped (not updated)
- You'll see a warning in the output
- Run again after verifying file locations

### Backup Failed

**Solution**: Check file permissions and disk space:

```bash
ls -la /path/to/PIONEER/Master/
```

Ensure you have write permissions to the database directory.

### Script Hangs or Times Out

**Solution**: This usually happens with very large libraries:

1. Try running in verbose mode to see progress:
   ```bash
   python rbMigrate.py --verbose ...
   ```
2. Close Rekordbox before running the script
3. Ensure the database is not being accessed by other processes

## Database Location

The script auto-detects the Rekordbox database location. Common locations:

### macOS
```
~/Library/Application Support/Pioneer DJ/Rekordbox/Master/master.db
```

### Windows
```
C:\\Users\\<username>\\AppData\\Roaming\\Pioneer DJ\\Rekordbox\\Master\\master.db
```

### Linux
```
~/.local/share/Pioneer DJ/Rekordbox/Master/master.db
```

### Custom Locations

If your database is in a custom location (as in your case):

```bash
python rbMigrate.py \
    --db-path "/path/to/PIONEER/Master/master.db" \
    --old-path "~/path/to/old/musiclibrary" \
    --new-path "/path/to/new/musiclibrary"
```

## Safety Best Practices

1. **Always create a backup** before making changes
2. **Use Preview mode** first to see what will change
3. **Verify file locations** before running
4. **Close Rekordbox** while the script is running
5. **Keep multiple backups** in case you need to restore

## Restoring from Backup

If you need to restore from a backup:

1. Stop Rekordbox
2. Find the backup file (e.g., `master.db.backup_20240821_143022`)
3. Rename the current database:
   ```bash
   mv master.db master.db.current
   ```
4. Restore from backup:
   ```bash
   cp master.db.backup_20240821_143022 master.db
   ```
5. Start Rekordbox

## FAQ

### Will this break my library?

No. The script only updates file paths in the database. It does not modify audio files or delete anything.

### Can I run this multiple times?

Yes. The script is idempotent - running it multiple times with the same paths is safe.

### What if I make a mistake?

Use a backup to restore. See the "Restoring from Backup" section above.

### Does this work with other DJ software?

Only Rekordbox. The database format is proprietary and specific to Pioneer DJ.

### How long does it take?

For a typical library (1000-5000 tracks), it takes 1-5 minutes. Very large libraries may take longer.

### What about playlists?

The script updates tracks in playlists automatically. Playlist references are updated as part of the database update.

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run with `--verbose` flag for detailed output
3. Ensure pyrekordbox is properly installed
4. Close Rekordbox before running the script

## License

This script is provided as-is for personal use. Use at your own risk.

## Changelog

### Version 0.2.0 (2026-08-22)
- Separate Apple Silicon and Intel builds (`rbMigrate-arm` / `rbMigrate-intel`)
- Versioned DMG filenames (e.g. `rbMigrate-arm-v0.2.0-<timestamp>.dmg`)
- App version shown in the GUI title bar, startup banner, and `--version` flag
- macOS app bundle now carries its version in the Info.plist
- Dropped the universal2 build: numpy and psutil don't publish universal2
  wheels, so a fat binary can't be produced from pip-installed dependencies
- Fixed Intel build failing in CI (x86_64 venv is now created in place instead
  of moved)
- Fixed ARM bundle being deleted before the Intel build finished
- Documented how to open the unsigned app past macOS Gatekeeper

### Version 0.1 (2024-08-21)
- Initial release
- Database path update functionality
- Backup creation
- Preview mode for safe updates
- XML metadata update
- Detailed reporting
- Comprehensive error handling
