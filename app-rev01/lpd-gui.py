import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import json
import os

def load_file():
    print("Load file button clicked")
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    print(f"Selected file: {file_path}")
    if file_path:
        results = run_lpd_script(file_path)
        if results:
            display_results(results)

def run_lpd_script(file_path):
    try:
        # Get the full path to lpd.py
        script_path = os.path.join(os.path.dirname(__file__), 'lpd.py')
        
        # Debug: Print the command being run
        print(f"Running command: python {script_path} {file_path}")
        
        result = subprocess.run(['python', script_path, file_path], capture_output=True, text=True)
        
        # Debug: Print the result of the command
        print(f"Return code: {result.returncode}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        
        if result.returncode != 0:
            messagebox.showerror("Error", f"Failed to run lpd.py script.\n\n{result.stderr}")
            return None
        return json.loads(result.stdout)
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
        return None

def display_results(results):
    if "error" in results:
        messagebox.showerror("Error", results["error"])
        return

    result_text = (
        f"Number of Days: {results['num_days']}\n"
        f"Number of Meters: {results['num_meters']}\n"
        f"Average Load: {results['average_load']:.2f} kW\n"
        f"Peak Load: {results['peak_load']:.2f} kW\n"
        f"Peak Load Datetime: {results['peak_datetime']}\n"
        f"Diversity Factor: {results['diversity_factor']:.2f}\n"
        f"Load Factor: {results['load_factor']:.2f}\n"
        f"Coincidence Factor: {results['coincidence_factor']:.2f}\n"
        f"Demand Factor: {results['demand_factor']:.2f}\n"
    )
    result_label.config(text=result_text)

# Create the main window
root = tk.Tk()
root.title("CSV Processor")

# Create a frame for the buttons
frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E))

# Add a button to load the CSV file
load_button = ttk.Button(frame, text="Load CSV File", command=load_file)
load_button.grid(row=0, column=0, padx=5, pady=5)

# Add a label to display the results
result_label = ttk.Label(root, text="", padding="10", justify="left")
result_label.grid(row=1, column=0, sticky=(tk.W, tk.E))

# Run the application
root.mainloop()
