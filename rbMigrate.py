#!/usr/bin/env python3
"""
rbMigrate

A tool to update file paths in your Rekordbox database after moving your music collection.
This script updates the FolderPath field in the DjmdContent table and optionally updates
the XML playlist files.

Usage:
    python rbMigrate.py [options]

Requirements:
    - Python 3.8+
    - pyrekordbox>=0.4.0

Author: Generated for Rekordbox migration
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from version import APP_VERSION

# Lazy imports to avoid SQLAlchemy hanging during initial import
# These are imported inside methods when needed


class PathUpdater:
    """Updates file paths in Rekordbox database."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        old_path: Optional[str] = None,
        new_path: Optional[str] = None,
        dry_run: bool = False,
        backup: bool = True,
        update_xml: bool = False,
        verbose: bool = False,
        force_continue: bool = False,
        auto_confirm: bool = False,
        is_interactive: bool = False,
    ):
        """
        Initialize the path updater.

        Args:
            db_path: Path to Rekordbox database. If None, auto-detect.
            old_path: Old file path to replace (e.g., "~/path/to/old/music").
            new_path: New file path (e.g., "/Volumes/ExternalDisk/path/to/new/music").
            dry_run: If True, only show what would change without modifying.
            backup: If True, create backup before modifying.
            update_xml: If True, update XML playlist files.
            verbose: If True, show detailed output.
            force_continue: If True, skip interactive prompts.
            auto_confirm: If True, skip the final confirmation prompt (used by GUI).
            is_interactive: If True, script is running in interactive mode.
        """
        self.dry_run = dry_run
        self.backup = backup
        self.update_xml = update_xml
        self.verbose = verbose
        self.db_path = db_path
        self.old_path = old_path
        self.new_path = new_path
        self.force_continue = force_continue
        self.auto_confirm = auto_confirm
        self.is_interactive = is_interactive
        self.db = None

        # Statistics
        self.stats = {
            "total_tracks": 0,
            "paths_updated": 0,
            "paths_skipped": 0,
            "files_not_found": 0,
            "errors": 0,
        }

    def verbose_print(self, message: str) -> None:
        """Print verbose output."""
        if self.verbose:
            print(message)

    def auto_detect_db_path(self) -> Optional[str]:
        """
        Auto-detect Rekordbox database path.

        Returns:
            Path to Rekordbox database, or None if not found.
        """
        try:
            from pyrekordbox.config import get_pioneer_install_dir
            pioneer_dir = get_pioneer_install_dir()
            if pioneer_dir:
                # Try multiple common directory structures
                # 1. Direct Pioneer/rekordbox/master.db (common on macOS)
                # 2. Pioneer/Master/master.db (legacy)
                # 3. Application Support/Pioneer/rekordbox/master.db (non-standard but common)
                # 4. Application Support/Pioneer DJ/Rekordbox/Master/master.db (standard)
                possible_paths = []

                # Check Pioneer/rekordbox/master.db (common on macOS)
                if pioneer_dir and (pioneer_dir / "rekordbox" / "master.db").exists():
                    possible_paths.append(pioneer_dir / "rekordbox" / "master.db")

                # Check Pioneer/rekordbox/master.db (non-standard but common)
                pioneer = Path.home() / "Library" / "Pioneer"
                if pioneer and (pioneer / "rekordbox" / "master.db").exists():
                    possible_paths.append(pioneer / "rekordbox" / "master.db")

                # Check Pioneer/Master/master.db (legacy)
                if pioneer and (pioneer / "Master" / "master.db").exists():
                    possible_paths.append(pioneer / "Master" / "master.db")

                # Check Application Support/Pioneer/rekordbox/master.db (non-standard but common)
                app_support = Path.home() / "Library" / "Application Support"
                if app_support and (app_support / "Pioneer" / "rekordbox" / "master.db").exists():
                    possible_paths.append(app_support / "Pioneer" / "rekordbox" / "master.db")

                # Check Application Support/Pioneer DJ/Rekordbox/Master/master.db (standard)
                if app_support and (app_support / "Pioneer DJ" / "Rekordbox" / "Master" / "master.db").exists():
                    possible_paths.append(app_support / "Pioneer DJ" / "Rekordbox" / "Master" / "master.db")

                # Return the first valid path found
                if possible_paths:
                    db_path = possible_paths[0]
                    self.verbose_print(f"Auto-detected database path: {db_path}")
                    return str(db_path)
        except Exception as e:
            self.verbose_print(f"Warning: Could not auto-detect database: {e}")

        return None

    def prompt_for_db_path(self) -> Optional[str]:
        """
        Prompt user for database path in interactive mode.

        Returns:
            Path to database, or None if user cancels.
        """
        print("\n" + "=" * 80)
        print("Rekordbox Database Location")
        print("=" * 80)

        # First, try auto-detection
        auto_path = self.auto_detect_db_path()
        if auto_path:
            print(f"\n✓ Auto-detected database location:")
            print(f"  {auto_path}")
            response = input("\nUse this location? (Y/n): ").strip().lower()
            if response != 'n':
                return auto_path

        # If auto-detection failed or user declined, prompt manually
        print("\nPlease specify the Rekordbox database location:")
        print("  - macOS: ~/Library/Application Support/Pioneer DJ/Rekordbox/Master/master.db")
        print("  - Windows: C:\\Users\\<username>\\AppData\\Roaming\\Pioneer DJ\\Rekordbox\\Master\\master.db")
        print("  - Linux: ~/.local/share/Pioneer DJ/Rekordbox/Master/master.db")
        print("  - Custom: Enter the full path to master.db")

        while True:
            db_path = input("\nDatabase path: ").strip()

            if not db_path:
                print("Error: Path cannot be empty")
                continue

            # Expand ~ to home directory
            db_path = os.path.expanduser(db_path)

            if not os.path.exists(db_path):
                print(f"Error: Path does not exist: {db_path}")
                response = input("Try again? (Y/n): ").strip().lower()
                if response == 'n':
                    return None
                continue

            if not db_path.endswith('master.db'):
                response = input(f"Path doesn't end with 'master.db': {db_path}. Continue? (y/N): ").strip().lower()
                if response != 'y':
                    continue

            return db_path

    def validate_paths(self) -> bool:
        """Validate that old and new paths are provided and exist (for old path)."""
        if not self.old_path:
            print("Error: --old-path is required")
            return False

        if not self.new_path:
            print("Error: --new-path is required")
            return False

        # Expand ~ to home directory
        old_path = os.path.expanduser(self.old_path)
        new_path = os.path.expanduser(self.new_path)

        # Check old path exists
        if not os.path.exists(old_path):
            print(f"Warning: Old path does not exist: {old_path}")
            # Only prompt for confirmation if we're in interactive mode (no --force flag)
            if not self.force_continue:
                response = input("Continue anyway? (y/N): ").strip().lower()
                if response != 'y':
                    return False
            else:
                print("Continuing anyway (--force flag was set)")

        self.old_path = old_path
        self.new_path = new_path
        return True

    def create_backup(self) -> Optional[str]:
        """
        Create a timestamped backup of the database.

        Returns:
            Path to backup file, or None if backup failed.
        """
        if not self.db_path:
            print("Error: Database path not set")
            return None

        backup_dir = Path(self.db_path).parent
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"master.db.backup_{timestamp}"

        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            print(f"✓ Backup created: {backup_path}")
            return str(backup_path)
        except Exception as e:
            print(f"✗ Error creating backup: {e}")
            return None

    def update_xml_files(self, xml_files: List[Path]) -> int:
        """
        Update XML playlist files.

        Note: XML files don't contain file paths directly, but we update
        the product version to ensure consistency.

        Args:
            xml_files: List of XML files to update.

        Returns:
            Number of XML files updated.
        """
        updated = 0
        for xml_file in xml_files:
            try:
                if xml_file.exists():
                    # Read XML
                    with open(xml_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Update product version to match database
                    # This ensures XML and database are consistent
                    import re
                    # Find and update PRODUCT version
                    pattern = r'<PRODUCT Name="rekordbox" Version="[^"]+"'
                    replacement = r'<PRODUCT Name="rekordbox" Version="7.2.16"'
                    new_content = re.sub(pattern, replacement, content)

                    if new_content != content:
                        if not self.dry_run:
                            with open(xml_file, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            print(f"✓ Updated: {xml_file.name}")
                            updated += 1
                        else:
                            print(f"[DRY-RUN] Would update: {xml_file.name}")
                            updated += 1
            except Exception as e:
                print(f"✗ Error updating {xml_file.name}: {e}")
                self.stats["errors"] += 1

        return updated

    def find_tracks_to_update(self) -> List[Dict]:
        """
        Find all tracks with paths matching the old path.

        Returns:
            List of track dictionaries with old and new paths.
        """
        # Import here to avoid SQLAlchemy hanging during initial import
        from pyrekordbox.db6 import Rekordbox6Database as RekordboxDatabase, tables

        self.verbose_print("Connecting to database...")
        self.db = RekordboxDatabase(self.db_path)

        # Query tracks where FolderPath starts with old path
        query = self.db.query(
            tables.DjmdContent.ID,
            tables.DjmdContent.FolderPath,
            tables.DjmdContent.FileNameL,
            tables.DjmdContent.FileNameS,
        ).filter(
            tables.DjmdContent.FolderPath.like(f"{self.old_path}%")
        )

        tracks = []
        for row in query.all():
            track_id, folder_path, filename_long, filename_short = row

            # Check if file exists at new path
            new_file_path = folder_path.replace(self.old_path, self.new_path)
            file_exists = os.path.exists(new_file_path)

            if not file_exists:
                self.stats["files_not_found"] += 1

            tracks.append({
                "id": track_id,
                "old_path": folder_path,
                "new_path": new_file_path,
                "filename_long": filename_long,
                "filename_short": filename_short,
                "file_exists": file_exists,
            })

            self.stats["total_tracks"] += 1

        self.db.close()
        return tracks

    def update_paths(self, tracks: List[Dict]) -> None:
        """
        Update paths in the database.

        Args:
            tracks: List of track dictionaries to update.
        """
        # Import here to avoid SQLAlchemy hanging during initial import
        from pyrekordbox.db6 import Rekordbox6Database as RekordboxDatabase, tables

        if not tracks:
            print("No tracks found matching the old path.")
            return

        print(f"\nFound {len(tracks)} track(s) with paths matching '{self.old_path}'")

        # Show preview
        print("\nPreview of changes:")
        print("-" * 100)
        for i, track in enumerate(tracks[:10], 1):  # Show first 10
            status = "✓" if track["file_exists"] else "✗"
            print(f"{i}. {status} {track['filename_long']}")
            print(f"   Old: {track['old_path']}")
            print(f"   New: {track['new_path']}")
            if not track["file_exists"]:
                print(f"   WARNING: File does not exist at new location")
            print()

        if len(tracks) > 10:
            print(f"... and {len(tracks) - 10} more track(s)")
            print()

        # Confirm (skipped in dry-run; GUI confirms via its own dialog)
        if self.dry_run:
            print("\n[DRY-RUN MODE] No changes were made.")
            print("Run without --dry-run to apply changes.")
            return

        if not (self.force_continue or self.auto_confirm):
            response = input(f"\nUpdate {len(tracks)} track(s)? (y/N): ").strip().lower()
            if response != 'y':
                print("Update cancelled.")
                return

        # Create backup if requested
        if self.backup:
            backup_path = self.create_backup()
            if not backup_path:
                print("Warning: Backup failed, continuing anyway...")

        # Update tracks
        print("\nUpdating tracks...")
        self.db = RekordboxDatabase(self.db_path)

        for track in tracks:
            try:
                # Update FolderPath
                self.db.query(tables.DjmdContent).filter(
                    tables.DjmdContent.ID == track["id"]
                ).update({"FolderPath": track["new_path"]})

                if track["file_exists"]:
                    self.stats["paths_updated"] += 1
                    print(f"✓ Updated: {track['filename_long']}")
                else:
                    self.stats["paths_skipped"] += 1
                    print(f"⊘ Skipped: {track['filename_long']} (file not found at new location)")

            except Exception as e:
                print(f"✗ Error updating {track['filename_long']}: {e}")
                self.stats["errors"] += 1

        # Commit changes
        self.db.commit()
        self.db.close()

        print(f"\n✓ Completed! Updated {self.stats['paths_updated']} path(s).")

    def run(self) -> int:
        """Run the path updater."""
        print("=" * 80)
        print("Rekordbox Path Updater")
        print("=" * 80)

        # In interactive mode, prompt for all values
        if self.is_interactive:
            # Prompt for database path first
            self.db_path = self.prompt_for_db_path()
            if not self.db_path:
                print("\nDatabase path not specified. Exiting.")
                return 1

            if not os.path.exists(self.db_path):
                print(f"\nError: Database not found: {self.db_path}")
                return 1

            # Prompt for old path
            print("\n" + "=" * 80)
            print("Old File Path")
            print("=" * 80)
            self.old_path = input("Old file path (e.g., '~/path/to/old/music'): ").strip()
            if not self.old_path:
                print("Error: Old path is required")
                return 1

            # Prompt for new path
            print("\n" + "=" * 80)
            print("New File Path")
            print("=" * 80)
            self.new_path = input("New file path (e.g., '/Volumes/ExternalDisk/path/to/new/music'): ").strip()
            if not self.new_path:
                print("Error: New path is required")
                return 1

            # Expand ~ to home directory
            self.old_path = os.path.expanduser(self.old_path)
            self.new_path = os.path.expanduser(self.new_path)

            # Check old path exists
            if not os.path.exists(self.old_path):
                print(f"Warning: Old path does not exist: {self.old_path}")
                response = input("Continue anyway? (y/N): ").strip().lower()
                if response != 'y':
                    print("Operation cancelled.")
                    return 1

        else:
            # In non-interactive mode, validate paths that are provided
            if not self.validate_paths():
                return 1

            # Expand ~ for paths that are provided
            if self.old_path:
                self.old_path = os.path.expanduser(self.old_path)
            if self.new_path:
                self.new_path = os.path.expanduser(self.new_path)

            # Set database path if not provided
            if not self.db_path:
                self.db_path = self.auto_detect_db_path()
                if not self.db_path:
                    print("\nError: Could not auto-detect database path.")
                    print("Please specify --db-path manually.")
                    return 1

                if not os.path.exists(self.db_path):
                    print(f"\nError: Database not found: {self.db_path}")
                    return 1

        print(f"\nDatabase: {self.db_path}")
        print(f"Old path: {self.old_path}")
        print(f"New path: {self.new_path}")

        if self.dry_run:
            print("Mode: DRY-RUN (no changes will be made)")

        if self.backup:
            print("Backup: Enabled")

        if self.update_xml:
            print("XML update: Enabled")

        print()

        # Find tracks to update
        tracks = self.find_tracks_to_update()

        if not tracks:
            print("No tracks found matching the old path.")
            return 0

        # Show summary
        print(f"\nSummary:")
        print(f"  Total tracks found: {self.stats['total_tracks']}")
        print(f"  Files not found at new location: {self.stats['files_not_found']}")
        print(f"  Paths to be updated: {len(tracks)}")

        # Update paths
        self.update_paths(tracks)

        # Update XML files if requested
        if self.update_xml and not self.dry_run:
            print("\n" + "=" * 80)
            print("Updating XML files...")
            print("=" * 80)

            # Find XML files
            db_dir = Path(self.db_path).parent
            xml_files = [
                db_dir / "masterPlaylists6.xml",
                db_dir / "automixPlaylist6.xml",
            ]

            updated_xml = self.update_xml_files(xml_files)
            print(f"\n✓ Updated {updated_xml} XML file(s).")

        # Final summary
        print("\n" + "=" * 80)
        print("Final Summary")
        print("=" * 80)
        print(f"Total tracks scanned: {self.stats['total_tracks']}")
        print(f"Paths updated: {self.stats['paths_updated']}")
        print(f"Paths skipped (file not found): {self.stats['paths_skipped']}")
        print(f"Errors: {self.stats['errors']}")
        print("=" * 80)

        return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update file paths in Rekordbox database after moving music collection.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python rbMigrate.py

  # Non-interactive with paths
  python rbMigrate.py \\
      --old-path "~/path/to/old/music" \\
      --new-path "/Volumes/ExternalDisk/path/to/new/music"

  # Dry-run to preview changes
  python rbMigrate.py \\
      --old-path "~/path/to/old/music" \\
      --new-path "/Volumes/ExternalDisk/path/to/new/music" \\
      --dry-run

  # With backup and XML update
  python rbMigrate.py \\
      --old-path "~/path/to/old/music" \\
      --new-path "/Volumes/ExternalDisk/path/to/new/music" \\
      --backup --update-xml

  # Specify custom database path
  python rbMigrate.py \\
      --db-path "/path/to/master.db" \\
      --old-path "~/path/to/old/music" \\
      --new-path "/Volumes/ExternalDisk/path/to/new/music"
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"rbMigrate {APP_VERSION}",
    )

    parser.add_argument(
        "--db-path",
        type=str,
        help="Path to Rekordbox database (master.db). If not specified, interactive prompt will ask for location.",
    )

    parser.add_argument(
        "--old-path",
        type=str,
        help="Old file path to replace (e.g., '~/path/to/old/music'). Use ~ for home directory.",
    )

    parser.add_argument(
        "--new-path",
        type=str,
        help="New file path (e.g., '/Volumes/ExternalDisk/path/to/new/music').",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying anything.",
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Disable automatic backup before making changes.",
    )

    parser.add_argument(
        "--update-xml",
        action="store_true",
        help="Update XML playlist files (metadata consistency).",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output during execution.",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force continue even if paths don't exist (non-interactive mode).",
    )

    args = parser.parse_args()

    # Set force_continue flag only when --force is explicitly set
    force_continue = args.force

    # Determine if running in interactive mode (no command-line args provided)
    is_interactive = not (args.db_path or args.old_path or args.new_path)

    updater = PathUpdater(
        db_path=args.db_path,
        old_path=args.old_path,
        new_path=args.new_path,
        dry_run=args.dry_run,
        backup=not args.no_backup,
        update_xml=args.update_xml,
        verbose=args.verbose,
        force_continue=force_continue,
        is_interactive=is_interactive,
    )

    sys.exit(updater.run())


if __name__ == "__main__":
    main()
