import tkinter as tk
from tkinter import ttk

def on_button_click():
    print("Button clicked!")

# Create the main window
root = tk.Tk()
root.title("Test GUI")

# Create a frame for the buttons
frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E))

# Add a button
test_button = ttk.Button(frame, text="Click Me", command=on_button_click)
test_button.grid(row=0, column=0, padx=5, pady=5)

# Run the application
root.mainloop()
