#!/usr/bin/env python3
"""
rbMigrate GUI

A Tkinter front-end for rbMigrate.py. Provides a simple wizard to update file
paths in a Rekordbox database after moving your music collection.

The GUI drives the same PathUpdater class as the CLI, piping its console output
into a live log pane in a background worker thread.

Usage:
    python rbMigrate_gui.py          # or run the packaged app

Requirements:
    Same as rbMigrate.py: Python 3.8+ with pyrekordbox, sqlcipher3, etc.
"""

import os
import queue
import sys
import threading
import traceback
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from rbMigrate import PathUpdater
    from version import APP_VERSION
except ImportError:
    # Allow running with ``python rbMigrate_gui.py`` from any directory.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from rbMigrate import PathUpdater
    from version import APP_VERSION


class QueueWriter:
    """A file-like object that forwards written text to a queue for the UI."""

    def __init__(self, q: "queue.Queue[str]"):
        self.q = q

    def write(self, message: str) -> int:
        if message:
            self.q.put(message)
        return len(message)

    def flush(self) -> None:
        pass


class MigrateApp(tk.Tk):
    """Main window of the rbMigrate GUI wizard."""

    def __init__(self):
        super().__init__()
        self.title(f"rbMigrate v{APP_VERSION} — Rekordbox Path Updater")
        self.minsize(680, 620)

        self.log_queue: "queue.Queue[str]" = queue.Queue()
        self.worker_thread: "threading.Thread | None" = None
        self.busy = False  # prevents overlapping operations

        self._build_ui()
        self._poll_log()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        pad = {"padx": 12, "pady": 4}

        header = ttk.Label(
            self,
            text="Update file paths in your Rekordbox database after moving "
                 "your music collection.",
            wraplength=650,
            justify="left",
        )
        header.grid(row=0, column=0, columnspan=3, sticky="w", **pad)

        # --- Database location ---
        ttk.Label(self, text="Rekordbox database (master.db):").grid(
            row=1, column=0, sticky="w", **pad)
        self.db_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.db_var).grid(
            row=1, column=1, sticky="ew", **pad)
        db_buttons = ttk.Frame(self)
        db_buttons.grid(row=1, column=2, sticky="e", **pad)
        ttk.Button(db_buttons, text="Browse…",
                   command=self._browse_db).pack(side="left", padx=2)
        ttk.Button(db_buttons, text="Auto-detect",
                   command=self._auto_detect).pack(side="left", padx=2)

        # --- Old / new paths ---
        ttk.Label(self, text="Old music path:").grid(
            row=2, column=0, sticky="w", **pad)
        self.old_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.old_var).grid(
            row=2, column=1, sticky="ew", **pad)
        ttk.Button(self, text="Browse…",
                   command=lambda: self._browse_folder("old_var")).grid(
            row=2, column=2, sticky="e", **pad)

        ttk.Label(self, text="New music path:").grid(
            row=3, column=0, sticky="w", **pad)
        self.new_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.new_var).grid(
            row=3, column=1, sticky="ew", **pad)
        ttk.Button(self, text="Browse…",
                   command=lambda: self._browse_folder("new_var")).grid(
            row=3, column=2, sticky="e", **pad)

        # --- Options ---
        options = ttk.LabelFrame(self, text="Options")
        options.grid(row=4, column=0, columnspan=3, sticky="ew", **pad)
        self.backup_var = tk.BooleanVar(value=True)
        self.update_xml_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options, text="Create backup before updating",
                        variable=self.backup_var).grid(
            row=0, column=0, sticky="w", padx=8, pady=4)
        ttk.Checkbutton(options, text="Update XML playlist metadata",
                        variable=self.update_xml_var).grid(
            row=0, column=1, sticky="w", padx=8, pady=4)

        # --- Action buttons ---
        actions = ttk.Frame(self)
        actions.grid(row=5, column=0, columnspan=3, sticky="e", **pad)
        self.preview_btn = ttk.Button(actions, text="Preview changes",
                                      command=self._preview)
        self.preview_btn.pack(side="left", padx=4)
        self.update_btn = ttk.Button(actions, text="Update DB",
                                     command=self._update, state="disabled")
        self.update_btn.pack(side="left", padx=4)
        self.clear_btn = ttk.Button(actions, text="Clear log",
                                    command=self._clear_log)
        self.clear_btn.pack(side="left", padx=4)

        # --- Log pane ---
        log_frame = ttk.LabelFrame(self, text="Log")
        log_frame.grid(row=6, column=0, columnspan=3, sticky="nsew",
                       padx=12, pady=(4, 12))
        self.log_text = tk.Text(log_frame, wrap="word", state="disabled",
                                height=18)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical",
                                  command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

        self.columnconfigure(1, weight=1)
        self.rowconfigure(6, weight=1)

        self._tag_banner()

    def _tag_banner(self) -> None:
        # Building the separator separately avoids a Python implicit-concat
        # gotcha: writing `"text\n" "=" * 80` concatenates `"text\n"` and `"="`
        # first, then multiplies the WHOLE thing by 80.
        lines = (
            f"rbMigrate v{APP_VERSION}\n"
            "Close Rekordbox before scanning or updating to avoid database "
            "locks.\n"
            "Start with \"Preview changes\", then review the summary before "
            "applying \"Update now\".\n"
        )
        self._append_log(lines + "=" * 80 + "\n")

    # ------------------------------------------------------- event handlers

    def _browse_db(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Rekordbox database",
            filetypes=[("Rekordbox database", "*.db"), ("All files", "*.*")])
        if path:
            self.db_var.set(path)

    def _browse_folder(self, var_name: str) -> None:
        path = filedialog.askdirectory(title="Choose folder")
        if path:
            getattr(self, var_name).set(path)

    def _auto_detect(self) -> None:
        updater = PathUpdater()
        detected = updater.auto_detect_db_path()
        if detected:
            self.db_var.set(detected)
            self._append_log(f"Auto-detected database: {detected}\n")
        else:
            messagebox.showwarning(
                "Not found",
                "Could not auto-detect the Rekordbox database.\n"
                "Please select it manually with \"Browse…\".")

    def _clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _preview(self) -> None:
        self._start_worker(apply=False)

    def _update(self) -> None:
        if messagebox.askyesno(
                "Confirm update",
                "This will modify your Rekordbox database.\n"
                "A backup will be created if the option is enabled.\n\n"
                "Continue?"):
            self._start_worker(apply=True)

    # --------------------------------------------------------------- worker

    def _start_worker(self, apply: bool) -> None:
        if self.busy:
            return

        err = self._validate_fields()
        if err:
            messagebox.showerror("Missing information", err)
            return

        # Build the updater with auto_confirm so no console prompt blocks the
        # worker thread. The GUI already handled confirmation for apply mode.
        updater = PathUpdater(
            db_path=os.path.expanduser(self.db_var.get()),
            old_path=os.path.expanduser(self.old_var.get()),
            new_path=os.path.expanduser(self.new_var.get()),
            dry_run=not apply,  # Only dry run if not applying
            backup=self.backup_var.get(),
            update_xml=self.update_xml_var.get(),
            verbose=True,
            force_continue=True,
            auto_confirm=True,
        )

        self._set_busy(True)
        self._clear_log()
        if not apply:
            self._append_log("Preview (no changes will be made)\n"
                             + "=" * 80 + "\n")
        else:
            self._append_log("Starting update...\n"
                             + "=" * 80 + "\n")

        # Route the updater's print() into our queue.
        old_stdout = sys.stdout
        sys.stdout = QueueWriter(self.log_queue)  # noqa: no thread-safety need

        def run() -> None:
            try:
                # find_tracks_to_update opens its own connection.
                tracks = updater.find_tracks_to_update()
                self.log_queue.put(
                    f"\nFound {len(tracks)} track(s) matching the old path.\n"
                    f"Review the summary above before updating.\n")
                if apply:
                    updater.update_paths(tracks)
                    if updater.update_xml:
                        db_dir = Path(updater.db_path).parent
                        xml_files = [
                            db_dir / "masterPlaylists6.xml",
                            db_dir / "automixPlaylist6.xml",
                        ]
                        n = updater.update_xml_files(xml_files)
                        self.log_queue.put(f"\nUpdated {n} XML file(s).\n")
            except Exception:
                self.log_queue.put("\nERROR: \n" + traceback.format_exc())
            finally:
                sys.stdout = old_stdout
                self.log_queue.put("\n[DONE]\n")

        t = threading.Thread(target=run, daemon=True)
        self.worker_thread = t
        t.start()
        self.after(100, self._poll_worker)

    def _set_busy(self, busy: bool) -> None:
        self.busy = busy
        state = "disabled" if busy else "normal"
        self.preview_btn.configure(state=state)
        self.update_btn.configure(state=state)
        self.clear_btn.configure(state=state)

    def _poll_worker(self) -> None:
        if self.worker_thread is None:
            return
        if self.worker_thread.is_alive():
            self.after(100, self._poll_worker)
        else:
            self._set_busy(False)
            self.worker_thread = None
            self.update_btn.configure(state="normal")

    # -------------------------------------------------------------- helpers

    def _validate_fields(self) -> "str | None":
        # Check for empty fields first
        fields = {
            "Rekordbox database": self.db_var.get(),
            "Old music path": self.old_var.get(),
            "New music path": self.new_var.get(),
        }
        for label, value in fields.items():
            if not value.strip():
                return f"Please fill in: {label}"

        # Check if database file exists and is valid
        db_path = self.db_var.get().strip()
        if db_path:
            db_path = os.path.expanduser(db_path)
            if not os.path.exists(db_path):
                return f"Database file not found: {db_path}"
            if not os.path.isfile(db_path):
                return f"Database path is not a file: {db_path}"

        # Check if old and new paths are different
        old_path = self.old_var.get().strip()
        new_path = self.new_var.get().strip()
        if old_path and new_path:
            old_path = os.path.expanduser(old_path)
            new_path = os.path.expanduser(new_path)
            if os.path.normpath(old_path) == os.path.normpath(new_path):
                return "Old and new paths must be different"

        return None

    def _poll_log(self) -> None:
        """Drain the log queue into the text pane on the UI thread."""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self._append_log(message)
        except queue.Empty:
            pass
        self.after(100, self._poll_log)

    def _append_log(self, text: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _on_close(self) -> None:
        if self.busy and not messagebox.askokcancel(
                "Quit", "An operation is still running. Quit anyway?"):
            return
        self.destroy()


def main() -> None:
    app = MigrateApp()
    app.mainloop()


if __name__ == "__main__":
    main()
