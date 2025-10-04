#!/usr/bin/env python3
"""
==============================================================================
Load Profile Analysis GUI — one-file EXE–friendly
==============================================================================
Author:  Michal Czarnecki
Updated: 2025-10-02
Version:  1.3

Changes in this version:
 - 🧭 Runs all embedded scripts in the **CSV's folder** so outputs land next to input.
 - 📜 Captures **stdout/stderr** and Python **logging** into the GUI textbox.
 - 🌦️ Weather: respects the **Run Weather Analysis** checkbox.
 - 🌦️ Weather file path is resolved robustly:
     1) Prefer EXE dir pattern: `weather_{ZIP}_{START}_{END}.csv` (what lpd-weather.py writes
        when arguments.txt is missing in frozen mode)
     2) Fallback: `<base>_WEATHER.csv` next to the LP CSV
 - 🔗 Merge: only runs if weather analysis is enabled **and** a weather CSV was actually found.
 - 🌐 Interactive HTML is opened **once** from the GUI; embedded script should not auto-open.
 - 📝 Leaves external assets (plotly.json, weather-codes.json, config.py) on disk.

Design notes:
 - In dev (not frozen), files resolve relative to this file's directory.
 - In frozen (PyInstaller onefile), embedded scripts are extracted to a
   temp directory exposed via sys._MEIPASS; external assets are expected
   to live NEXT TO the EXE (sys.executable directory).
==============================================================================
"""

from __future__ import annotations

import os
import sys
import runpy
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import subprocess  # still used for "Open Folder" on Windows
import threading
import datetime
import pandas as pd
import contextlib
import logging
import webbrowser
from pathlib import Path
from typing import Optional, Tuple

DEBUG = False  # Set to True for extra prints

# ──────────────────────────────────────────────────────────────────────────────
# Frozen/dev path helpers
# ──────────────────────────────────────────────────────────────────────────────
def is_frozen() -> bool:
    """Return True when running as a PyInstaller-frozen executable."""
    return getattr(sys, "frozen", False) is True


def exe_dir() -> Path:
    """
    Directory containing the running EXE (frozen) or this source file (dev).
    Use for files we expect to ship next to the EXE (plotly.json, config.py, etc.).
    """
    return Path(sys.executable).parent if is_frozen() else Path(__file__).resolve().parent


def embedded_base_dir() -> Path:
    """
    Base directory for embedded resources when frozen (sys._MEIPASS),
    otherwise the directory of this source file. We load the bundled
    secondary scripts (lpd-*.py) from here in onefile mode.
    """
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def run_embedded_script(script_name: str, args: list[str]) -> int:
    """
    Execute an embedded *.py script (main/merge/interactive/weather) in-process.
    We temporarily replace sys.argv so the script sees the CLI it expects.
    IMPORTANT: Trap SystemExit AND temporarily monkeypatch os._exit so scripts
    cannot terminate the whole GUI process.
    Returns an integer exit code (0 = success).
    """
    script_path = embedded_base_dir() / script_name
    if not script_path.is_file():
        raise FileNotFoundError(f"Embedded script not found: {script_path}")

    old_argv = sys.argv
    import os as _os
    _orig_os_exit = _os._exit

    def _fake_exit(code=0):
        print(f"[WARN] {script_name} attempted os._exit({code}); converting to SystemExit.")
        raise SystemExit(code)

    _os._exit = _fake_exit

    try:
        sys.argv = [script_name] + list(args)
        if DEBUG:
            print(f"[DEBUG] run_embedded_script -> {sys.argv}")
        try:
            runpy.run_path(str(script_path), run_name="__main__")
            print(f"[INFO] {script_name} completed (no sys.exit).")
            return 0
        except SystemExit as se:
            code = se.code
            try:
                code = int(code)
            except Exception:
                code = 0 if code in (None, "") else 1
            if code == 0:
                print(f"[INFO] {script_name} exited cleanly with code 0.")
            else:
                print(f"[ERROR] {script_name} exited with code {code}.")
            return code
    finally:
        sys.argv = old_argv
        _os._exit = _orig_os_exit


# ──────────────────────────────────────────────────────────────────────────────
# Console/logging redirection into the GUI
# ──────────────────────────────────────────────────────────────────────────────
class RedirectText:
    """Redirects stdout/stderr into the GUI's scrolling text box."""

    def __init__(self, text_widget: tk.Text):
        self.text_widget = text_widget

    def write(self, string: str) -> None:
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)

    def flush(self) -> None:
        pass


class TextHandler(logging.Handler):
    """Route logging records into the GUI textbox (format: ts - LEVEL - msg)."""

    def __init__(self, text_widget: tk.Text):
        super().__init__()
        self.text_widget = text_widget
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        try:
            msg = self.format(record)
            self.text_widget.insert(tk.END, msg + "\n")
            self.text_widget.see(tk.END)
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────────────────────────────────────
@contextlib.contextmanager
def pushd(new_dir: Path):
    """
    Temporarily change CWD so relative outputs (e.g., *_RESULTS-LP.csv) are created
    next to the input CSV file, not in the EXE's working directory.
    """
    prev = Path.cwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(prev)


def round_to_nearest_15_minutes(dt: datetime.datetime) -> datetime.datetime:
    """Round a datetime object to the nearest 15-minute interval."""
    minute = (dt.minute + 7) // 15 * 15
    rounded_dt = dt.replace(minute=minute % 60, second=0, microsecond=0)
    if minute >= 60:
        rounded_dt += datetime.timedelta(hours=1)
    return rounded_dt


def results_lp_path(raw_csv_path: str) -> Path:
    """Given the raw input CSV path, return sibling <name>_RESULTS-LP.csv."""
    p = Path(raw_csv_path)
    return p.with_name(p.stem + "_RESULTS-LP.csv")


def lp_date_range(lp_csv: Path) -> Tuple[str, str]:
    """Return (start_date, end_date) as YYYY-MM-DD strings from LP CSV."""
    df = pd.read_csv(lp_csv, usecols=["datetime"])  # fast read
    s = pd.to_datetime(df["datetime"], errors="coerce").dropna()
    start = s.min().date().isoformat()
    end = s.max().date().isoformat()
    return start, end


def resolve_weather_path(zip_code: str, start_date: str, end_date: str, lp_csv: Path) -> Optional[Path]:
    """
    Resolve where lpd-weather.py actually wrote the weather CSV.
    Preference:
      1) EXE dir: weather_{zip}_{start}_{end}.csv
      2) LP folder: <base>_WEATHER.csv
    Returns Path if exists, else None.
    """
    # 1) EXE dir pattern (seen in your logs when arguments.txt missing)
    exe_weather = exe_dir() / f"weather_{zip_code}_{start_date}_{end_date}.csv"
    if exe_weather.is_file():
        return exe_weather

    # 2) Fallback next to the LP CSV
    lp_weather = lp_csv.with_name(lp_csv.stem.replace("_RESULTS-LP", "_WEATHER") + ".csv")
    if lp_weather.is_file():
        return lp_weather

    return None


# ──────────────────────────────────────────────────────────────────────────────
# GUI helpers and actions
# ──────────────────────────────────────────────────────────────────────────────
def display_datetime_range(csv_file: str) -> None:
    """
    Read the CSV and display the first and last date in the output box.
    We only read the 'date' column for a light/fast sniff.
    """
    try:
        df = pd.read_csv(csv_file, usecols=["date"])
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
        first_date = df["date"].min()
        last_date = df["date"].max()

        output_textbox.insert(
            tk.END,
            f"\n"
            f"{'#' * 80}\n\n"
            f"{'File Loaded: ':<15}{os.path.basename(csv_file):<63}\n"
            f"{'Start Date: ':<15}{first_date.strftime('%Y-%m-%d') if pd.notna(first_date) else 'N/A':<63}\n"
            f"{'End Date: ':<15}{last_date.strftime('%Y-%m-%d') if pd.notna(last_date) else 'N/A':<63}\n\n"
            f"{'#' * 80}\n"
        )
        output_textbox.see(tk.END)
        update_status("CSV file start and end dates read.", "success")
    except Exception as e:
        output_textbox.insert(tk.END, f"Error processing CSV: {e}\n")
        update_status("Error processing CSV file.", "error")


def browse_file() -> None:
    """Open a file dialog to select a CSV file and preview its date range."""
    file_path = filedialog.askopenfilename(
        title="Select CSV File", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
    )
    if file_path:
        csv_path_entry.delete(0, tk.END)
        csv_path_entry.insert(0, file_path)
        update_status("File selected successfully.", "success")
        display_datetime_range(file_path)


def save_arguments_to_file(csv_file: str, kva_value: str, datetime_value: str | None) -> None:
    """
    Write run arguments to 'arguments.txt'.
    - When frozen: try to write into the extracted bundle dir (sys._MEIPASS),
      which corresponds to “inside the EXE” at runtime.
    - If that fails (permissions), fallback next to the EXE.
    """
    primary = embedded_base_dir() / "arguments.txt"
    fallback = exe_dir() / "arguments.txt"

    payload = f'"{csv_file}" --transformer_kva {kva_value}'
    if datetime_value:
        payload += f' --datetime "{datetime_value}"'
    payload += "\n"

    try:
        primary.write_text(payload, encoding="utf-8")
        update_status(f"arguments.txt written: {primary}", "success")
        return
    except Exception as e:
        print(f"[WARN] Could not write to MEIPASS: {e}. Trying EXE folder...")

    try:
        fallback.write_text(payload, encoding="utf-8")
        update_status(f"arguments.txt written: {fallback}", "success")
    except Exception as e:
        print(f"[ERROR] Failed to write arguments.txt to both locations: {e}")
        update_status("An error occurred while saving arguments to file.", "error")


# NEW: run weather and return the resolved weather file path (or None)
def run_weather_and_resolve_path(zip_code: str, lp_results: Path) -> Optional[Path]:
    """
    Runs lpd-weather.py for the min/max dates found in lp_results, then resolves
    the actual weather CSV path using resolve_weather_path(). Returns Path or None.
    """
    try:
        if not weather_analysis_var.get():
            print("[INFO] Weather analysis unchecked; skipping weather generation.")
            return None

        if not lp_results.is_file():
            update_status("Load profile file not found; cannot run weather analysis.", "warning")
            return None

        start_date, end_date = lp_date_range(lp_results)
        update_status("Running weather analysis (lpd-weather.py)...", "info")
        rc = run_embedded_script("lpd-weather.py", [zip_code, start_date, end_date])
        if rc != 0:
            update_status("Weather analysis reported a non-zero exit code.", "warning")

        wx_path = resolve_weather_path(zip_code, start_date, end_date, lp_results)
        if wx_path and wx_path.is_file():
            update_status(f"Weather file found: {wx_path.name}", "success")
            return wx_path
        else:
            update_status("Weather file not found after generation.", "warning")
            return None

    except Exception as e:
        update_status(f"Error during weather analysis: {e}", "error")
        return None


def launch_analysis(csv_file: str, kva_value: str, datetime_value: str | None = None) -> None:
    """
    Run the full analysis pipeline by executing the embedded scripts in-process.
    External assets (plotly.json, weather-codes.json, config.py) are expected
    NEXT TO THE EXE/.py. We *cd* to the CSV folder so outputs live beside it.
    """
    try:
        update_status("Analysis started...", "success")
        clear_output_textbox()

        # Basic validation
        if not csv_file:
            update_status("Error: Please select a CSV file.", "error")
            return
        if not kva_value:
            update_status("Error: Please enter a transformer KVA size.", "error")
            return

        # Validate datetime if provided: allow 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'
        if datetime_value:
            dv = datetime_value.strip()
            if len(dv) not in (10, 19):
                update_status("Error: Invalid datetime format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS", "error")
                return

        # Write arguments.txt next to EXE/.py for consistency
        save_arguments_to_file(csv_file, kva_value, datetime_value)

        # Build a shared CLI arg list used by main/interactive
        base_command = [csv_file, "--transformer_kva", str(kva_value)]
        if datetime_value:
            base_command.extend(["--datetime", datetime_value.strip()])

        work_dir = Path(csv_file).parent if Path(csv_file).parent else Path.cwd()
        with pushd(work_dir):
            # 1) MAIN: compute results & _RESULTS-LP.csv
            update_status("Running analysis (lpd-main.py)...", "info")
            run_embedded_script("lpd-main.py", base_command)

            # Path to processed LP used by merge & interactive
            lp_results = results_lp_path(csv_file)

            # 2) WEATHER + MERGE (only if checkbox is set and a weather file exists)
            if weather_analysis_var.get():
                zip_code = (zipcode_entry.get().strip() or "84601")
                wx_path = run_weather_and_resolve_path(zip_code, lp_results)

                if wx_path and wx_path.is_file():
                    update_status("Merging weather with load profile (lpd-merge.py)...", "info")
                    run_embedded_script("lpd-merge.py", [str(lp_results), "--weather", str(wx_path), "--keep-weather"])
                else:
                    print("[WARN] Weather file missing; skipping merge.")
            else:
                print("[INFO] Weather analysis unchecked; skipping weather and merge.")

            # 3) INTERACTIVE view (writes HTML without auto-opening)
            update_status("Launching interactive view (lpd-interactive.py)...", "info")
            run_embedded_script("lpd-interactive.py", base_command)

        # Show final textual results if present (beside the CSV)
        base = Path(csv_file).with_suffix("")
        results_file = f"{base}_RESULTS.txt"
        if Path(results_file).is_file():
            with open(results_file, "r", encoding="utf-8", errors="ignore") as f:
                clear_output_textbox()
                output_textbox.insert(tk.END, f.read())
        else:
            print(f"[WARN] Expected results not found: {results_file}")

        # Open interactive HTML once (GUI controls opening)
        html_fallback = f"{base}_RESULTS-LP-INTERACTIVE.html"
        if Path(html_fallback).is_file():
            try:
                webbrowser.open("file://" + os.path.abspath(html_fallback))
            except Exception as e:
                print(f"[WARN] Could not open interactive HTML: {e}")

        update_status("Analysis completed.", "success")

    except Exception as e:
        print(f"[ERROR] launch_analysis failed: {e}")
        update_status("An error occurred during analysis.", "error")


def clear_output_textbox() -> None:
    """Clear the output text box."""
    output_textbox.delete(1.0, tk.END)


def open_folder() -> None:
    """Open the folder where the input CSV file lives."""
    csv_file = csv_path_entry.get()
    if not csv_file:
        update_status("Error: No file selected to open.", "error")
        return

    folder_path = os.path.normpath(os.path.dirname(csv_file))
    try:
        if os.name == "nt":
            subprocess.run(["explorer", folder_path], check=False)
        elif os.name == "posix":
            subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", folder_path], check=False)
        update_status(f"Opened folder: {folder_path}", "success")
    except Exception as e:
        update_status(f"Error opening folder: {e}", "error")


def clear_all() -> None:
    """Clear all user inputs and outputs."""
    csv_path_entry.delete(0, tk.END)
    kva_entry.delete(0, tk.END)
    datetime_entry.delete(0, tk.END)
    clear_output_textbox()
    output_textbox.insert(tk.END, default_text)
    update_status("Ready.")


def update_status(message: str, status_type: str = "info") -> None:
    """Update the status label with a message and color."""
    colors = {"success": "green", "error": "red", "warning": "orange", "info": "black"}
    status_label.config(text=message, fg=colors.get(status_type, "black"))
    if DEBUG:
        print(f"[{status_type.upper()}] {message}")


def start_analysis_thread() -> None:
    """Start a background thread for the analysis to keep the GUI responsive."""
    csv_file = csv_path_entry.get()
    kva_value = kva_entry.get()
    datetime_value = datetime_entry.get()

    def run_analysis():
        try:
            launch_analysis(csv_file, kva_value, datetime_value)
        except Exception as e:
            update_status(f"Error during analysis: {e}", "error")

    threading.Thread(target=run_analysis, daemon=True).start()


# ──────────────────────────────────────────────────────────────────────────────
# UI
# ──────────────────────────────────────────────────────────────────────────────
root = tk.Tk()
root.title("Load Profile Analysis")
root.resizable(False, False)

weather_analysis_var = tk.BooleanVar(value=True)

default_text = """                INSTRUCTIONS FOR USE
This program will run a load analysis profile for data in the input file.
Input CSV file is generated outside of this application and should be formatted:

Line 1: meter,date,time,kw
Line 2+: 85400796,2024-01-01,00:15:00.000,0.052

If transformer KVA is entered, a time-based transformer loading profile will 
be generated in the output along with a graph. (Single-phase only.)
If KVA = 0, transformer loading will be skipped in the output file, and no 
visualization will be available.
"""

default_kva = "75"

default_date = "2024-08-10 16:45:00"

# Top Frame
top_frame = tk.Frame(root)
top_frame.grid(row=0, column=0, columnspan=6, pady=5, padx=5, sticky="ew")
tk.Label(top_frame, text="Select Input CSV File:").pack(side="left", padx=5)
csv_path_entry = tk.Entry(top_frame, width=45)
csv_path_entry.pack(side="left", padx=5)
tk.Button(top_frame, text="Browse...", command=browse_file).pack(side="left", padx=5)

# Full Load KVA
tk.Label(top_frame, text="Full load KVA:").pack(side="left", padx=5)
kva_entry = tk.Entry(top_frame, width=8)
kva_entry.insert(0, default_kva)
kva_entry.pack(side="left", padx=5)

# Row 1
row1_frame = tk.Frame(root)
row1_frame.grid(row=1, column=0, columnspan=6, pady=5, padx=5, sticky="ew")
tk.Label(row1_frame, text="Target (YYYY-MM-DD HH:MM:SS):").pack(side="left", padx=5)
datetime_entry = tk.Entry(row1_frame, width=19)
datetime_entry.insert(0, default_date)
datetime_entry.pack(side="left", padx=5)
tk.Label(row1_frame, text="ZIP Code:").pack(side="left", padx=5)
zipcode_entry = tk.Entry(row1_frame, width=6)
zipcode_entry.insert(0, "84601")
zipcode_entry.pack(side="left", padx=5)
tk.Checkbutton(row1_frame, text="Run Weather Analysis", variable=weather_analysis_var).pack(side="left", padx=5)

# Status Label
status_label = tk.Label(root, text="Ready.", anchor="w")
status_label.grid(row=2, column=0, columnspan=6, sticky="w", padx=5, pady=2)

# Output Textbox
output_textbox = scrolledtext.ScrolledText(root, width=85, height=20, wrap=tk.WORD)
output_textbox.grid(row=3, column=0, columnspan=6, padx=5, pady=5)
output_textbox.insert(tk.END, default_text)

# Bottom Buttons
button_frame = tk.Frame(root)
button_frame.grid(row=4, column=3, columnspan=3, pady=5, padx=5)
tk.Button(button_frame, text="Open Folder", command=open_folder).pack(side="left", padx=5)
tk.Button(button_frame, text="Run Analysis", command=start_analysis_thread).pack(side="left", padx=5)
tk.Button(button_frame, text="Clear All", command=clear_all).pack(side="left", padx=5)
tk.Button(button_frame, text="Close", command=root.destroy).pack(side="left", padx=5)

# Redirect standard output and error to the text box
output_redirector = RedirectText(output_textbox)
sys.stdout = output_redirector
sys.stderr = output_redirector  # capture logging/tracebacks sent to stderr

# Route Python logging into the textbox as well
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)  # set to DEBUG for more detail
root_logger.addHandler(TextHandler(output_textbox))

# Run the main loop
if __name__ == "__main__":
    root.mainloop()
