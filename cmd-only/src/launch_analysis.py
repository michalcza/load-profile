def launch_analysis():
    # Get the CSV file path and transformer KVA
    csv_file = csv_path_entry.get()
    kva_value = kva_entry.get()
    
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

    # Construct the command with an absolute path
    command = ["C:\Users\micha\GitHub\load-profile\cmd-only\src\lpd.exe", csv_file, "--transformer_kva", str(kva_value)]
    
    # Print command for debugging
    print("Running command:", command)
    
    # Run the command
    try:
        subprocess.run(command, check=True)
        messagebox.showinfo("Success", "Transformer load analysis completed successfully.")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
    except FileNotFoundError:
        messagebox.showerror("Error", "Executable not found. Please check the path.")
