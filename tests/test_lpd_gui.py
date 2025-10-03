import pytest
import subprocess
import os
from unittest.mock import patch, MagicMock
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

LDP_GUI = os.path.join(os.path.dirname(__file__), "../src-r2/lpd-gui.py")


# ================================
# 🚀 Basic Launch Test
# ================================
def test_lpd_gui_launches():
    """Test if lpd-gui.py launches without crashing"""
    result = subprocess.run(
        ["python", LDP_GUI],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "Error: lpd-gui.py failed to launch."


# ================================
# 🧪 Mock GUI Test (Simulating Button Clicks)
# ================================
@pytest.fixture
def mock_gui():
    """Fixture to mock tkinter root for the GUI."""
    root = tk.Tk()
    yield root
    root.destroy()


@pytest.fixture
def mock_file_dialog():
    """Fixture to mock file dialog for CSV selection."""
    with patch("tkinter.filedialog.askopenfilename", return_value="../sample-data/98meters-300days-2788K_rows.csv") as mock_dialog:
        yield mock_dialog


@pytest.fixture
def mock_messagebox():
    """Fixture to mock message box for displaying results."""
    with patch("tkinter.messagebox.showinfo") as mock_info:
        yield mock_info


# ================================
# 🎯 Test: Simulate File Selection
# ================================
def test_browse_file(mock_gui, mock_file_dialog):
    """Test the 'Browse' button and file selection."""
    from lpd_gui import browse_file

    csv_path_entry = tk.Entry(mock_gui)
    browse_file(csv_path_entry)
    assert csv_path_entry.get() == "../sample-data/98meters-300days-2788K_rows.csv", "File not selected properly."


# ================================
# 🎯 Test: Run Analysis with File Selected
# ================================
def test_run_analysis(mock_gui, mock_file_dialog, mock_messagebox):
    """Test running the analysis after file selection."""
    from lpd_gui import start_analysis_thread, csv_path_entry

    csv_path_entry = tk.Entry(mock_gui)
    csv_path_entry.insert(0, "../sample-data/98meters-300days-2788K_rows.csv")

    # Simulate clicking "Run Analysis"
    start_analysis_thread()
    mock_messagebox.assert_called_with("Success", "Analysis completed.")


# ================================
# 📁 Test: Open Folder
# ================================
def test_open_folder(mock_gui, mock_file_dialog):
    """Test the 'Open Folder' button."""
    from lpd_gui import open_folder, csv_path_entry

    csv_path_entry = tk.Entry(mock_gui)
    csv_path_entry.insert(0, "../sample-data/98meters-300days-2788K_rows.csv")

    with patch("subprocess.run") as mock_run:
        open_folder()
        mock_run.assert_called_once()


# ================================
# 🧹 Test: Clear All Inputs and Outputs
# ================================
def test_clear_all(mock_gui):
    """Test clearing all inputs and outputs."""
    from lpd_gui import clear_all, csv_path_entry, kva_entry, datetime_entry, output_textbox

    # Create mock input and output widgets
    csv_path_entry = tk.Entry(mock_gui)
    csv_path_entry.insert(0, "../sample-data/98meters-300days-2788K_rows.csv")

    kva_entry = tk.Entry(mock_gui)
    kva_entry.insert(0, "75")

    datetime_entry = tk.Entry(mock_gui)
    datetime_entry.insert(0, "2024-08-04 00:00:00")

    output_textbox = tk.Text(mock_gui)
    output_textbox.insert("1.0", "Test Output")

    # Clear all
    clear_all()

    # Check that all inputs and outputs are cleared
    assert csv_path_entry.get() == ""
    assert kva_entry.get() == ""
    assert datetime_entry.get() == ""
    assert output_textbox.get("1.0", "end-1c") == ""
