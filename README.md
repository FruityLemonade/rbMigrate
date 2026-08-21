# rbMigrate - an Alpha Theta Rekordbox Path Updater

rbMigrate is a tool to update file paths in your Rekordbox database after moving your music collection. This python script automatically updates the `FolderPath` field in the `DjmdContent` table and optionally updates XML playlist files. Useful for exporting your Rekordbox library to an external drive or new computer.

## Features

- ⭐️ **Automatic Path Replacement**: Updates all file paths in the database
- ⭐️ **Safety Features**:
  - Automatic backup creation before changes
  - Dry-run mode to preview changes
  - File existence validation
- ⭐️ **Flexible Configuration**:
  - Interactive mode (prompts for paths)
  - Command-line mode with all options
  - Auto-detection of database location
- ⭐️ **Detailed Reporting**: Shows statistics and progress
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

## Installation

### 1. Create Virtual Environment (Recommended)

```bash
python3.11 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

### 2. Install Python Dependencies

```bash
pip install pyrekordbox sqlcipher3 lxml mutagen psutil sqlalchemy
```

All required dependencies are listed in the [Dependencies](#dependencies) section above.

### 3. Verify Installation

```bash
python -c "import pyrekordbox; print(pyrekordbox.__version__)"
python -c "import sqlcipher3; print(sqlcipher3.__version__)"
```

### 4. Run the Script

```bash
python rbMigrate.py --old-path "~/path/to/old/musiclibrary" --new-path "/path/to/new/musiclibrary"
```

**Note**: If you encounter permission errors, use the virtual environment method above instead of installing system-wide.

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

### Backup

Automatic backup creation:
- Timestamped filename: `master.db.backup_YYYYMMDD_HHMMSS`
- Stored in the same directory as the database
- Safe to keep multiple backups

## Troubleshooting

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
2. **Use dry-run mode** first to preview changes
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

### Version 0.1 (2024-08-21)
- Initial release
- Database path update functionality
- Backup creation
- Dry-run mode
- XML metadata update
- Detailed reporting
- Comprehensive error handling
