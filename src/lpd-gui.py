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
    visualization. The tool integrates seamlessly with the `lpd-main.exe` 
    executable for backend processing.

Features:
    - Select input CSV files through a file dialog.
    - Input transformer KVA to include loading analysis in the results.
    - Display analysis results in a scrollable text area within the GUI.
    - Generate and open graphical visualizations of load profiles.
    - Print analysis results directly from the GUI.
    - Clear all inputs and reset the GUI for new tasks.

Usage:
    1. Run this script using Python 3:
       $ python lpd-gui.py
    2. Select an input CSV file containing load data.
    3. Enter a transformer KVA size (or 0 to skip transformer analysis).
    4. Click "Run Analysis" to generate results and visualizations.

Requirements:
    - Python 3.x
    - Required libraries: tkinter, subprocess, os, threading
    - `lpd-main.exe` must be in the same directory as this script.

Output:
    - Displays load analysis results in the GUI.
    - Generates output files and visualizations:
      - `<input_file>_RESULTS.txt`: Analysis summary.
      - `<input_file>_RESULTS-GRAPH.png`: Visualization of load profile.

Changelog:
    - 11/26/2024:
        - Set working directory to enable logging in `lpd-main.exe`.
        - Adjusted spacing in GUI elements to prevent text cutoff.
        - Improved error handling for missing executable and invalid input.
        - Improve workflow and threading for background process (lpd-main.exe)

Compile instructions:
Syntax:
> pyinstaller --onefile --add-data "lpd-main.exe;." --distpath . lpd-gui.py
==============================================================================
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
import threading
import sys

default_text = """ INSTRUCTIONS FOR USE
This program will run a load analysis profile for data in input file.
Input CSV file is generated in Yukon and should be formatted:

Line 1  meter,date,time,kw
Line 2+ 85400796,2024-01-01,00:15:00.000,0.052

If transformer KVA is entered, a time based transformer loading profile will 
be generated in the output along with a graph. *** Single phase only ***
If KVA = 0, transformer loading will be skipped in output file.
Visualization file will not be available.

Program documentation is available in the Dispatch Google Docs files:
dispatch@provopower.org://docs.google.com/dispatch_notes
https://tinyurl.com/cshac3an
https://github.com/michalcza/load-profile
"""

def browse_file():
    # Open file dialog to select CSV file
    file_path = filedialog.askopenfilename(
        title="Select CSV File",
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
    )
    csv_path_entry.delete(0, tk.END)  # Clear any previous path
    csv_path_entry.insert(0, file_path)  # Insert the selected file path

def launch_analysis(csv_file, kva_value):

    # Clear error and status labels at the start
    root.after(0, clear_error_and_status_labels)
    
    def update_success_label():
        root.after(0, lambda: success_label.config(text=" Running..."))

    def update_error_label(message):
        root.after(0, lambda: error_label.config(text=" Error."))

    # Schedule GUI updates on the main thread
    root.after(0, update_success_label)

    # Clear previous content
    root.after(0, clear_error_label)
    root.after(0, clear_success_label)
    root.after(0, clear_output_textbox)

    # Check if the CSV file and KVA value are provided
    if not csv_file:
        root.after(0, lambda: update_error_label(" Error. Please select a CSV file."))
        return
    if not kva_value:
        root.after(0, lambda: update_error_label(" Error. Please enter the transformer KVA size."))
        return

    try:
        kva_value = float(kva_value)  # Convert KVA to float
    except ValueError:
        root.after(0, lambda: update_error_label(" Error. Transformer KVA must be a numerical value."))
        root.after(0, lambda: status_label.config(text=" Status: Failed - Invalid KVA value."))
        return

    try:
        # Prepare the command for subprocess
        # Ensure working directory is set correctly
        os.chdir(os.path.dirname(__file__))
        command = [os.path.join(os.path.dirname(__file__), "lpd-main.exe"), csv_file, "--transformer_kva", str(kva_value)]

        # Run the command
        subprocess.run(command, check=True)

        # Process output
        global base_name
        base_name = os.path.splitext(csv_file)[0]  # Clear csv extension
        global output_file
        output_file = f"{base_name}_RESULTS.txt"

        if os.path.isfile(output_file):
            with open(output_file, "r") as file:
                output_textbox.delete(1.0, tk.END)  # Clear previous content
                output_textbox.insert(tk.END, file.read())
        else:
            output_textbox.delete(1.0, tk.END)
            output_textbox.insert(tk.END, f"Output file '{output_file}' not found.")

        # Display print and open plot buttons
        root.after(0, lambda: plot_button.grid(row=4, column=3, pady=10, padx=10))
        root.after(0, lambda: print_button.grid(row=4, column=4, pady=10, padx=10))
        root.after(0, lambda: success_label.config(text=" Load analysis completed successfully."))

    except subprocess.CalledProcessError as e:
        root.after(0, lambda e=e: error_label.config(text=f" Subprocess Error: {e}"))
    except Exception as e:
        root.after(0, lambda e=e: error_label.config(text=f" An error occurred: {e}"))

def clear_success_label():
    error_label.config(text="")
def clear_error_label():
    error_label.config(text="")
def clear_output_textbox():
    output_textbox.delete(1.0, tk.END)
def clear_csv_path_entry():
    csv_path_entry.delete(0, tk.END)
def clear_kva_entry():
    csv_path_entry.delete(0, tk.END)
def open_plot():
    plot_file = f"{base_name}_RESULTS-GRAPH.png"  # Define the plot file path based on base_name
    # Check if the plot file exists
    if not os.path.isfile(plot_file):
        clear_error_label()
        clear_success_label()
        messagebox.showerror("Open File Error", "Error! Could not open plot file.\nTime based visualization not generated when KVA = 0.",)
        return
    try:
        if os.name == 'nt':  # Windows
            os.startfile(plot_file)
        elif os.name == 'posix':  # macOS
            os.system(f"open '{plot_file}'")
        else:
            raise OSError("Unsupported operating system for opening the plot file.")
    except Exception as e:
        print(f"Could not open the file: {e}")
        error_label.config(text=" Error! Could not open plot file.")
def print_output_file():
    # Check if the output file exists
    if not os.path.isfile(output_file):
        error_label.config(text=" Error! Output file not found.")
        return
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(["notepad.exe", "/p", output_file], check=True)
        elif os.name == 'posix':  # macOS and Linux
            subprocess.run(["lp", output_file], check=True)
        else:
            error_label.config(text=" Unsupported OS for printing.")
    except Exception as e:
        error_label.config(text=" An error occured while printing.")

def start_analysis_thread():
    # Retrieve widget values in the main thread
    csv_file = csv_path_entry.get()
    kva_value = kva_entry.get()

    # Start the background thread, passing these values
    threading.Thread(target=launch_analysis, args=(csv_file, kva_value), daemon=True).start()
    
def clear_all():
    csv_path_entry.delete(0, tk.END)    # Clear CSV path entry
    kva_entry.delete(0, tk.END)         # Clear KVA entry
    error_label.config(text="")         # Clear error label
    success_label.config(text="")       # Clear success label
    status_label.config(text="")        # Clear success label
    output_textbox.delete(1.0, tk.END)  # Clear output textbox
    output_textbox.insert(tk.END, default_text)
    plot_button.grid_remove()           # Hide plot button
    print_button.grid_remove()          # Hide print button
    
def clear_error_and_status_labels():
    error_label.config(text="")
    status_label.config(text="")
    
# Create the main window
root = tk.Tk()
root.title("Transformer Load Analysis")
root.resizable(False, False)  # Lock the window size

# CSV File selection
tk.Label(root, text="Select Input CSV File:").grid(row=0, column=0, padx=1, pady=10, sticky="w")
csv_path_entry = tk.Entry(root, width=35)
csv_path_entry.grid(row=0, column=1, padx=10, pady=10)
browse_button = tk.Button(root, text="Browse...", command=browse_file)
browse_button.grid(row=0, column=2, padx=1, pady=10)

# Transformer KVA input
tk.Label(root, text="Transformer KVA:").grid(row=0, column=3, padx=1, pady=1, sticky="w")
kva_entry = tk.Entry(root, width=10)
kva_entry.grid(row=0, column=4, padx=1, pady=10)

# Run Analysis button
run_button = tk.Button(root, text="Run Analysis", command=start_analysis_thread)
run_button.grid(row=0, column=5, padx=1, pady=10)

# Success label (to display the status message)
success_label = tk.Label(root, text="", fg="green")
success_label.grid(row=1, column=2, columnspan=5, padx=1, pady=1, sticky="w")

# Error label (to display the status message)
error_label = tk.Label(root, text="", fg="red")
error_label.grid(row=1, column=2, columnspan=5, padx=1, pady=1, sticky="w")

# Status label (to display the status message)
status_label = tk.Label(root, text="", fg="black")
status_label.grid(row=2, column=2, columnspan=5, padx=1, pady=1, sticky="w")

# Output Text Box to display the content of the output file
output_textbox = scrolledtext.ScrolledText(root, width=80, height=25, wrap=tk.WORD)
output_textbox.grid(row=3, column=0, columnspan=7, padx=1, pady=1)
output_textbox.insert(tk.END, default_text)

# Close button
close_button = tk.Button(root, text="Close", command=root.destroy)
close_button.grid(row=4, column=6, pady=10, padx=10)

# Visualize button
plot_button = tk.Button(root, text="Open Plot", command=open_plot)
plot_button.grid(row=4, column=3, pady=10, padx=10)
plot_button.grid_remove()  # Hide initially

# Print button
print_button = tk.Button(root, text="Print Output File", command=print_output_file)
print_button.grid(row=4, column=4, pady=10, padx=10)
print_button.grid_remove()  # Hide initially

# Clear All button
clear_all_button = tk.Button(root, text="Clear All", command=clear_all)
clear_all_button.grid(row=4, column=5, pady=10, padx=10)

root.mainloop()

# Add a text area
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=25)
text_area.insert(tk.END, default_text)
text_area.pack(padx=10, pady=10)
