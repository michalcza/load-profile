
#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os

"""
Windows executable:
    Executable is available as ~\cmd-only\src\dist\lpd.exe
    and is created using:
    > pyinstaller --onefile load_profile.py
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
    # Get the CSV file path and transformer KVA
    csv_file = csv_path_entry.get()
    kva_value = kva_entry.get()
    
    # Check if the CSV file and KVA value are provided
    if not csv_file:
        messagebox.showerror("Error", "Please select a CSV file.")
        return
    if not kva_value:
        messagebox.showerror("Error", "Please enter the transformer KVA size.")
        return
    
    try:
        kva_value = float(kva_value)  # Convert KVA to float
    except ValueError:
        messagebox.showerror("Error", "Transformer KVA must be a numerical value.")
        return

    # Construct the command to run the executable
    command = ["lpd.py", csv_file, "--transformer_kva", str(kva_value)]
    
    # Run the command and capture output
    try:
        subprocess.run(command, check=True)
        messagebox.showinfo("Success", "Transformer load analysis completed successfully.")

        # Construct the output filename based on the input CSV filename pattern
        base_name = os.path.splitext(csv_file)[0]
        output_file = f"{base_name}_all_outputs.txt"
        
        # Check if the output file exists, then open it
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                output_content = f.read()
            # Display the content in a new window
            display_output(output_content)
        else:
            messagebox.showerror("Error", f"Output file '{output_file}' not found.")

    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def display_output(content):
    # Create a new window to display the output content
    output_window = tk.Toplevel(root)
    output_window.title("Analysis Output")
    
    # Add text widget to display the file content
    text_widget = tk.Text(output_window, wrap='word')
    text_widget.insert('1.0', content)
    text_widget.pack(expand=True, fill='both')

    # Close button
    close_button = tk.Button(output_window, text="Close", command=output_window.destroy)
    close_button.pack(pady=10)

# Create the main window
root = tk.Tk()
root.title("Transformer Load Analysis GUI")

# CSV File selection
tk.Label(root, text="Select Input CSV File:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
csv_path_entry = tk.Entry(root, width=50)
csv_path_entry.grid(row=0, column=1, padx=10, pady=5)
browse_button = tk.Button(root, text="Browse...", command=browse_file)
browse_button.grid(row=0, column=2, padx=10, pady=5)

# Transformer KVA input
tk.Label(root, text="Transformer KVA:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
kva_entry = tk.Entry(root, width=20)
kva_entry.grid(row=1, column=1, padx=10, pady=5)

# Run Analysis button
run_button = tk.Button(root, text="Run Analysis", command=launch_analysis)
run_button.grid(row=2, column=1, pady=20)

# Close button
close_button = tk.Button(root, text="Close", command=root.destroy)
close_button.grid(row=2, column=2, pady=20, padx=10)

# Start the GUI event loop
root.mainloop()
