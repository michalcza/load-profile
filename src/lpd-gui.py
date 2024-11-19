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

def launch_analysis():
    success_label.config(text="Running...")
    clear_error_label() # Clear previous content
    clear_success_label() # Clear previous content
    clear_output_textbox() # Clear previous content
    
    # Get the CSV file path and transformer KVA
    csv_file = csv_path_entry.get()
    kva_value = kva_entry.get()
    
    # Check if the CSV file and KVA value are provided
    if not csv_file:
        error_label.config(text="Error. Please select a CSV file.")
        return
    if not kva_value:
        error_label.config(text="Error. Please enter the transformer KVA size.")
        return
    
    try:
        kva_value = float(kva_value)  # Convert KVA to float
    except ValueError:
        error_label.config(text="Error. Transformer KVA must be a numerical value.")
        status_label.config(text="Status: Failed - Invalid KVA value.")
        return
    if kva_value == 0:
        success_label.config(text="Running...")
        status_label.config(text="Status: Transformer analysis skipped.")
        plot_button.grid_remove()  # Hide plot visualization
    # Construct the command to run the executable
    command = [os.path.join(os.path.dirname(__file__), "lpd-main.exe"), csv_file, "--transformer_kva", str(kva_value)]
    
    # Check if 'lpd-main.exe' exists before running the command
    if not os.path.isfile(command[0]):
        error_label.config(text="Error. Executable 'lpd-main.exe' not found. Please check the file path.")
        return
    try:
        subprocess.run(command, check=True)
        global base_name 
        base_name = os.path.splitext(csv_file)[0] # clear csv extension
        global output_file
        output_file = f"{base_name}_all_outputs.txt"
        if os.path.isfile(output_file):
            with open(output_file, "r") as file:
                output_textbox.delete(1.0, tk.END)  # Clear previous content
                output_textbox.insert(tk.END, file.read())
        else:
            output_textbox.delete(1.0, tk.END)
            output_textbox.insert(tk.END, f"Output file '{output_file}' not found.")
        # Display print and open plot buttons
        plot_button.grid(row=4, column=3, pady=10, padx=10)
        print_button.grid(row=4, column=4, pady=10, padx=10)
        # Print success message
        success_label.config(text="Load analysis completed successfully.")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
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
    plot_file = f"{base_name}_visualization.png"  # Define the plot file path based on base_name
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
        error_label.config(text="Error! Could not open plot file.")
def print_output_file():
    # Check if the output file exists
    if not os.path.isfile(output_file):
        error_label.config(text="Error! Output file not found.")
        return
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(["notepad.exe", "/p", output_file], check=True)
        elif os.name == 'posix':  # macOS and Linux
            subprocess.run(["lp", output_file], check=True)
        else:
            error_label.config(text="Unsupported OS for printing.")
    except Exception as e:
        error_label.config(text="An error occured while printing.")
def start_analysis_thread():
    threading.Thread(target=launch_analysis).start()
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

# Start the GUI event loop
root.mainloop()

# Create a menu bar
menu_bar = tk.Menu(root)

# File menu
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Load CSV", command=load_csv)
file_menu.add_command(label="Clear", command=clear_text)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=exit_application)
menu_bar.add_cascade(label="File", menu=file_menu)

# Help menu
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="Help", command=show_help)
help_menu.add_command(label="About", command=show_about)
menu_bar.add_cascade(label="Help", menu=help_menu)

# Add a text area
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=25)
text_area.insert(tk.END, default_text)
text_area.pack(padx=10, pady=10)
