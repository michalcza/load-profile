#!/usr/bin/env python3
"""
==============================================================================
Transformer Load Analysis GUI
==============================================================================
Author: Michal Czarnecki
Date:   11/26/2024
Version: 1.0

Description:
    This script provides a graphical user interface (GUI) for the Transformer 
    Load Analysis Tool. It allows users to select a CSV file containing load 
    data, input a transformer KVA size, and perform load analysis with 
    visualization. The tool integrates seamlessly with the `lpd-interactive.py` 
    backend script.

Usage:
    1. Run this script using Python 3:
       $ python lpd-gui.py
    2. Select an input CSV file containing load data.
    3. Enter a transformer KVA size (or 0 to skip transformer analysis).
    4. Optionally, enter a datetime in "YYYY-MM-DD HH:MM:SS" format.
    5. Click "Run Analysis" to generate results and visualizations.

Requirements:
    - Python 3.x
    - Required libraries: tkinter, subprocess, os, threading
==============================================================================
"""

import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import subprocess
import threading
import sys

class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        # Append the string to the text widget
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)  # Automatically scroll to the end

    def flush(self):
        # Needed for compatibility with some output streams
        pass




# Prevent recursive launch of the GUI executable
# if "lpd-gui" in sys.argv[0]:
    # print("Prevented recursive launch of lpd-gui.exe")
    # sys.exit(1)

default_text = """INSTRUCTIONS FOR USE
This program will run a load analysis profile for data in the input file.
Input CSV file is generated in Yukon and should be formatted:

Line 1: meter,date,time,kw
Line 2+: 85400796,2024-01-01,00:15:00.000,0.052

If transformer KVA is entered, a time-based transformer loading profile will 
be generated in the output along with a graph. (Single-phase only.)
If KVA = 0, transformer loading will be skipped in the output file, and no 
visualization will be available.
"""
default_kva = "75"
default_date = "2024-10-10 16:45:00"

def browse_file():
    """Open a file dialog to select a CSV file."""
    file_path = filedialog.askopenfilename(
        title="Select CSV File",
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
    )
    if file_path:
        csv_path_entry.delete(0, tk.END)
        csv_path_entry.insert(0, file_path)
        clear_output_textbox()
        update_status("")

# def launch_analysis(csv_file, kva_value, datetime_value=None):
    # """Run `lpd-main.py` first, then `lpd-interactive.py` last."""
    # try:
        # update_status("Analysis started...", "success")
        # clear_output_textbox()

        # if not csv_file:
            # update_status("Error: Please select a CSV file.", "error")
            # return
        # if not kva_value:
            # update_status("Error: Please enter a transformer KVA size, or 0 to skip.", "error")
            # return

        # # Change to the script's directory
        # os.chdir(os.path.dirname(__file__))
        # base_command = [csv_file, "--transformer_kva", str(kva_value)]
        # if datetime_value:
            # base_command.extend(["--datetime", datetime_value.strip()])

        # # Run lpd-main.py
        # main_command = [sys.executable, "lpd-main.exe"] + base_command
        # print("Running lpd-main.py with command:", " ".join(main_command))
        # subprocess.run(main_command, check=True)  # Wait for completion
        
        # # Check if the results file exists before running lpd-interactive.py
        # results_file = f"{os.path.splitext(csv_file)[0]}_RESULTS.txt"
        # if not os.path.isfile(results_file):
            # update_status(f"Error: {results_file} not generated by lpd-main.py.", "error")
            # return

        # # Optionally, handle additional processing or output validation here
        # # Example: Ensure output required by lpd-interactive.py is generated
        # results_file = f"{os.path.splitext(csv_file)[0]}_RESULTS.txt"
        # if not os.path.isfile(results_file):
            # update_status(f"Error: {results_file} not generated by lpd-main.py.", "error")
            # return

        # # Run lpd-interactive.py
        # interactive_command = [sys.executable, "lpd-interactive.exe"] + base_command
        # print("Running lpd-interactive.py with command:", " ".join(interactive_command))
        # subprocess.run(interactive_command, check=True)  # Wait for completion

        # # Display results generated by lpd-interactive.py
        # if os.path.isfile(results_file):
            # with open(results_file, "r") as file:
                # output_textbox.insert(tk.END, file.read())
        # else:
            # output_textbox.insert(tk.END, f"Output file '{results_file}' not found.")
        # update_status("Analysis completed.", "success")

    # except subprocess.CalledProcessError as e:
        # update_status(f"Subprocess error: {e}", "error")
    # except Exception as e:
        # update_status(f"An error occurred: {e}", "error")
# def launch_analysis(csv_file, kva_value, datetime_value=None):
    # """Run `lpd-main.exe` first, then `lpd-interactive.exe` last."""
    # try:
        # update_status("Analysis started...", "success")
        # clear_output_textbox()

        # if not csv_file:
            # update_status("Error: Please select a CSV file.", "error")
            # return
        # if not kva_value:
            # update_status("Error: Please enter a transformer KVA size, or 0 to skip.", "error")
            # return

        # # Change to the script's directory
        # os.chdir(os.path.dirname(__file__))
        # base_command = [csv_file, "--transformer_kva", str(kva_value)]
        # if datetime_value:
            # base_command.extend(["--datetime", datetime_value.strip()])

        # # Run lpd-main.exe
        # main_command = ["lpd-main.exe"] + base_command
        # print("Running lpd-main.exe with command:", " ".join(main_command))
        # subprocess.run(main_command, check=True)  # Wait for completion

        # # Check if the results file exists before running lpd-interactive.exe
        # results_file = f"{os.path.splitext(csv_file)[0]}_RESULTS.txt"
        # if not os.path.isfile(results_file):
            # update_status(f"Error: {results_file} not generated by lpd-main.exe.", "error")
            # return

        # # Run lpd-interactive.exe
        # interactive_command = ["lpd-interactive.exe"] + base_command
        # print("Running lpd-interactive.exe with command:", " ".join(interactive_command))
        # subprocess.run(interactive_command, check=True)  # Wait for completion

        # # Display results generated by lpd-interactive.exe
        # if os.path.isfile(results_file):
            # with open(results_file, "r") as file:
                # output_textbox.insert(tk.END, file.read())
        # else:
            # output_textbox.insert(tk.END, f"Output file '{results_file}' not found.")
        # update_status("Analysis completed.", "success")

    # except subprocess.CalledProcessError as e:
        # update_status(f"Subprocess error: {e}", "error")
    # except Exception as e:
        # update_status(f"An error occurred: {e}", "error")
def launch_analysis(csv_file, kva_value, datetime_value=None):
    """Run `lpd-main.exe` first, then `lpd-interactive.exe` last."""
    try:
        update_status("Analysis started...", "success")
        clear_output_textbox()

        if not csv_file:
            update_status("Error: Please select a CSV file.", "error")
            return
        if not kva_value:
            update_status("Error: Please enter a transformer KVA size, or 0 to skip.", "error")
            return

        # Validate datetime entry
        # if datetime_value:
            # try:
                # datetime.datetime.strptime(datetime_value.strip(), "%Y-%m-%d %H:%M:%S")
            # except ValueError:
                # update_status("Error: Invalid datetime format. Use YYYY-MM-DD HH:MM:SS.", "error")
                # return
                
        # Change to the script's directory
        os.chdir(os.path.dirname(__file__))
        base_command = [csv_file, "--transformer_kva", str(kva_value)]
        if datetime_value:
            base_command.extend(["--datetime", datetime_value.strip()])

        # Run lpd-main.exe explicitly
        main_command = [os.path.join(os.getcwd(), "lpd-main.exe")] + base_command
        print("Running lpd-main.exe with command:", " ".join(main_command))
        subprocess.run(main_command, check=True)  # Wait for completion

        # Check if the results file exists before running lpd-interactive.exe
        results_file = f"{os.path.splitext(csv_file)[0]}_RESULTS.txt"
        if not os.path.isfile(results_file):
            update_status(f"Error: {results_file} not generated by lpd-main.exe.", "error")
            return

        # Run lpd-interactive.exe explicitly
        interactive_command = [os.path.join(os.getcwd(), "lpd-interactive.exe")] + base_command
        print("Running lpd-interactive.exe with command:", " ".join(interactive_command))
        subprocess.run(interactive_command, check=True)  # Wait for completion

        # Display results generated by lpd-interactive.exe
        if os.path.isfile(results_file):
            with open(results_file, "r") as file:
                clear_output_textbox() # Clear textbox before writing report file.
                output_textbox.insert(tk.END, file.read())
        else:
            output_textbox.insert(tk.END, f"Output file '{results_file}' not found.")
        update_status("Analysis completed.", "success")

    except subprocess.CalledProcessError as e:
        update_status(f"Subprocess error: {e}", "error")
    except Exception as e:
        update_status(f"An error occurred: {e}", "error")

def clear_output_textbox():
    """Clear the output text box."""
    output_textbox.delete(1.0, tk.END)

def clear_all():
    """Clear all user inputs and outputs."""
    csv_path_entry.delete(0, tk.END)
    kva_entry.delete(0, tk.END)
    datetime_entry.delete(0, tk.END)
    clear_output_textbox()
    output_textbox.insert(tk.END, default_text)
    update_status("")

def update_status(message, status_type="info"):
    """Update the status label with a message."""
    colors = {"success": "green", "error": "red", "warning": "orange", "info": "black"}
    status_label.config(text=message, fg=colors.get(status_type, "black"))

def start_analysis_thread():
    """Start a background thread for the analysis."""
    csv_file = csv_path_entry.get()
    kva_value = kva_entry.get()
    datetime_value = datetime_entry.get()
    print(f"CSV File: {csv_file}, KVA Value: {kva_value}, Datetime: {datetime_value}")

    threading.Thread(
        target=launch_analysis,
        args=(csv_file, kva_value, datetime_value),
        daemon=True
    ).start()

# Create the main window
root = tk.Tk()
root.title("Transformer Load Analysis")
root.resizable(False, False)

# Input File
tk.Label(root, text="Select Input CSV File:").grid(row=0, column=0, padx=10, pady=2, sticky="w")
csv_path_entry = tk.Entry(root, width=40)
csv_path_entry.grid(row=0, column=1, padx=5, pady=2)
tk.Button(root, text="Browse...", command=browse_file).grid(row=0, column=2, padx=5, pady=2)

# Transformer KVA
tk.Label(root, text="Transformer KVA:").grid(row=0, column=3, padx=10, pady=2, sticky="w")
kva_entry = tk.Entry(root, width=10)
kva_entry.insert(0, default_kva)  # Insert the default value at position 0 (start)
kva_entry.grid(row=0, column=4, padx=5, pady=2)

# Datetime Input
tk.Label(root, text="Datetime (YYYY-MM-DD HH:MM:SS):").grid(row=1, column=0, padx=10, pady=2, sticky="w")
datetime_entry = tk.Entry(root, width=40)
datetime_entry.insert(0, default_date)  # Insert the default value at position 0 (start)
datetime_entry.grid(row=1, column=1, padx=5, pady=2)

# Run Analysis Button
tk.Button(root, text="Run Analysis", command=start_analysis_thread).grid(row=1, column=4, padx=5, pady=2)

# Status Label
status_label = tk.Label(root, text="", anchor="w")
status_label.grid(row=2, column=0, columnspan=5, sticky="w", padx=10, pady=2)

# Output Text Box
output_textbox = scrolledtext.ScrolledText(root, width=80, height=25, wrap=tk.WORD)
output_textbox.grid(row=3, column=0, columnspan=5, padx=10, pady=5)
output_textbox.insert(tk.END, default_text)

# Redirect standard output to the text box
output_redirector = RedirectText(output_textbox)
sys.stdout = output_redirector
# sys.stdout = original_stdout

# Clear and Close Buttons
tk.Button(root, text="Clear All", command=clear_all).grid(row=4, column=3, pady=5, padx=2)
tk.Button(root, text="Close", command=root.destroy).grid(row=4, column=4, pady=5, padx=2)

root.mainloop()
