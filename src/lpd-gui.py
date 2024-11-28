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
        - Cleared previous inputs/results on file browse and validation errors.
    - 11/27/2024
        - Cleanup and consolidate messaging feedback into single function.

Compile instructions:
IMPORTANT!!! Build lpd-main.exe first, and then build lpd-gui.exe second.
Syntax:
$ pyinstaller --onefile --add-data "lpd-main.exe;." --distpath . lpd-gui.py

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
    
    # If a file was selected
    if file_path:
    
        # Clear any previous path
        csv_path_entry.delete(0, tk.END)  
        # Insert the selected file path
        csv_path_entry.insert(0, file_path)  

        # Clear previous content
        root.after(0, clear_error_and_status_labels)
        clear_output_textbox()

        # Hide plot button if currently displayed
        #if plot_button.grid_info():
        #   plot_button.configure(state=tk.NORMAL)

        # Hide print button if currently displayed
        #if print_button.grid_info():
        #   print_button.configure(state=tk.NORMAL)

def launch_analysis(csv_file, kva_value):
   
    # Schedule GUI updates on the main thread
    update_status("Analysis started...", "success")

    # Clear previous content
    root.after(0, clear_output_textbox)

    # Check if the CSV file and KVA value are provided
    if not csv_file:
        update_status("Error. Please select a CSV file.", "error")
        return
    if not kva_value:
        update_status("Error. Please select a transformer KVA size, or '0' to skip transformer analysis.", "error")
        return

    try:
        # Convert KVA to float
        kva_value = float(kva_value)  
    except ValueError:
        update_status("Error. Transformer KVA must be a numerical value.", "error")
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
        
        # Clear csv extension
        base_name = os.path.splitext(csv_file)[0]
        global output_file
        output_file = f"{base_name}_RESULTS.txt"

        if os.path.isfile(output_file):
            with open(output_file, "r") as file:
                # Clear previous content
                output_textbox.delete(1.0, tk.END)
                output_textbox.insert(tk.END, file.read())
                update_status("")
        else:
            output_textbox.delete(1.0, tk.END)
            output_textbox.insert(tk.END, f"Output file '{output_file}' not found.")

        # Display print and open plot buttons
        update_status("Analysis completed.", "success")
        plot_button.configure(state=tk.NORMAL)
        print_button.configure(state=tk.NORMAL)

    except subprocess.CalledProcessError as e:
        update_status(f"Subprocess Error: {e}", "error")
    except Exception as e:
        update_status(f"An error occurred: {e}", "error")

def clear_output_textbox():
    output_textbox.delete(1.0, tk.END)
def clear_csv_path_entry():
    csv_path_entry.delete(0, tk.END)
def clear_kva_entry():
    csv_path_entry.delete(0, tk.END)
def open_plot():
    # Define the plot file path based on base_name
    plot_file = f"{base_name}_RESULTS-GRAPH.png"
    
    # Check if the plot file exists
    if not os.path.isfile(plot_file):
        update_status("")
        messagebox.showerror("Open File Error", "Error! Could not open plot file.\nTime based visualization not generated when KVA = 0.",)
        return
    try:
        # Windows
        if os.name == 'nt':  
            os.startfile(plot_file)
        # macOS
        elif os.name == 'posix':  
            os.system(f"open '{plot_file}'")
        else:
            raise OSError("Unsupported operating system for opening the plot file.")
    except Exception as e:
        print(f"Could not open the file: {e}")
        update_status("Error! Could not open plot file.", "error")
def print_output_file():
    # Check if the output file exists
    if not os.path.isfile(output_file):
        update_status("Error! Output file not found.", "error")
        return
    try:
        # Windows
        if os.name == 'nt':  
            subprocess.run(["notepad.exe", "/p", output_file], check=True)
        # macOS and Linux
        elif os.name == 'posix':  
            subprocess.run(["lp", output_file], check=True)
        else:
            update_status("Unsupported OS for printing.", "error")
    except Exception as e:
        update_status(f"An error occurred while printing: {e}", "error")

def start_analysis_thread():

    # Retrieve widget values in the main thread
    csv_file = csv_path_entry.get()
    kva_value = kva_entry.get()

    # Start the background thread, passing these values
    threading.Thread(target=launch_analysis, args=(csv_file, kva_value), daemon=True).start()
    
def clear_all():
    csv_path_entry.delete(0, tk.END)
    kva_entry.delete(0, tk.END)
    output_textbox.delete(1.0, tk.END)
    output_textbox.insert(tk.END, default_text)
    plot_button.configure(state=tk.DISABLED)
    print_button.configure(state=tk.DISABLED)
    update_status("")
    
def clear_error_and_status_labels():
    update_status("")
    
def update_status(message, status_type="info"):
    """
    Update the status label with a message and style based on status type.
    
    :param message: The feedback message to display.
    :param status_type: Type of message ("info", "success", "error", "warning").
    """
    if status_type == "success":
        status_label.config(text=f"✔️ {message}", fg="green")
    elif status_type == "error":
        status_label.config(text=f"❌ {message}", fg="red")
    elif status_type == "warning":
        status_label.config(text=message, fg="orange")
    else:
        status_label.config(text=message, fg="black")

# Create the main window
root = tk.Tk()
root.title("Transformer Load Analysis")
root.resizable(False, False)  # Lock the window size

# Top row
# CSV File selection
tk.Label(root, text="Select Input CSV File:").grid(row=0, column=0, padx=10, pady=2, sticky="w")
csv_path_entry = tk.Entry(root, width=35)
csv_path_entry.grid(row=0, column=1, padx=5, pady=2)
browse_button = tk.Button(root, text="Browse...", command=browse_file)
browse_button.grid(row=0, column=2, padx=5, pady=2)

# Transformer KVA input
tk.Label(root, text="Transformer KVA:").grid(row=0, column=3, padx=1, pady=1, sticky="w")
kva_entry = tk.Entry(root, width=10)
kva_entry.grid(row=0, column=4, padx=5, pady=2)

# Run Analysis button
run_button = tk.Button(root, text="Run Analysis", command=start_analysis_thread)
run_button.grid(row=0, column=5, padx=5, pady=2)

# Unified status label
status_label = tk.Label(root, text="", anchor="w")
status_label.grid(row=2, column=1, columnspan=7, sticky="w", padx=5, pady=1)

# Output Text Box to display the content of the output file
output_textbox = scrolledtext.ScrolledText(root, width=80, height=25, wrap=tk.WORD)
output_textbox.grid(row=3, column=0, columnspan=7, padx=5, pady=2)
output_textbox.insert(tk.END, default_text)

# Bottom row buttons

# Visualize button
plot_button = tk.Button(root, text="Open Graph", command=open_plot)
plot_button.grid(row=4, column=2, pady=5, padx=2)
plot_button.configure(state=tk.DISABLED)  # Hide initially

# Print button
print_button = tk.Button(root, text="Print Results", command=print_output_file)
print_button.grid(row=4, column=3, pady=5, padx=2)
print_button.configure(state=tk.DISABLED)  # Hide initially

# Clear All button
clear_all_button = tk.Button(root, text="Clear All", command=clear_all)
clear_all_button.grid(row=4, column=4, pady=5, padx=2)

# Close button
close_button = tk.Button(root, text="Close", command=root.destroy)
close_button.grid(row=4, column=5, pady=5, padx=2)

root.mainloop()

# Add a text area
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=25)
text_area.insert(tk.END, default_text)
text_area.pack(padx=10, pady=10)
