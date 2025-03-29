import os
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def load_data():
    """
    Prompts the user to select files for weather and power usage data.
    Returns the loaded datasets as pandas DataFrames.
    """
    root = tk.Tk()
    root.withdraw()
    
    messagebox.showinfo("File Selection", "Please select the weather data CSV file.")
    weather_file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    
    messagebox.showinfo("File Selection", "Please select the power usage data CSV file.")
    lp_file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])

    if not weather_file_path or not lp_file_path:
        messagebox.showerror("Error", "Both files must be selected.")
        raise FileNotFoundError("File selection was canceled.")

    weather_data = pd.read_csv(weather_file_path)
    lp_data = pd.read_csv(lp_file_path)
    return weather_data, lp_data

def clean_data(weather_data, lp_data):
    """
    Cleans and prepares the datasets for analysis.
    Returns a merged DataFrame.
    """
    # Convert date/time columns to datetime objects
    weather_data['datetime'] = pd.to_datetime(weather_data['datetime'])
    lp_data['datetime'] = pd.to_datetime(lp_data['date'] + ' ' + lp_data['time'])

    # Merge datasets on datetime
    combined_data = pd.merge(lp_data, weather_data, on='datetime', how='inner')

    # WMO Weather Code mapping
    wmo_weather_code_map = {
        0: "Clear sky",
        3: "Overcast (5/8 - 8/8 cloud cover)",
        60: "Slight rain, intermittent",
        # Add more mappings as needed
    }
    combined_data['weather_description'] = combined_data['weather_code'].map(wmo_weather_code_map)
    return combined_data

def analyze_data(combined_data):
    """
    Performs analysis and generates summary statistics.
    Returns summary data as DataFrames.
    """
    clear_sky_data = combined_data[combined_data['weather_description'] == "Clear sky"]
    overcast_data = combined_data[combined_data['weather_description'] == "Overcast (5/8 - 8/8 cloud cover)"]

    # Peak comparison
    peak_comparison_summary = pd.DataFrame({
        "Condition": ["Clear sky", "Overcast (5/8 - 8/8 cloud cover)"],
        "Peak Power Usage (kW)": [
            clear_sky_data['kw'].max(),
            overcast_data['kw'].max()
        ],
        "Temperature at Peak (\u00b0F)": [
            clear_sky_data.loc[clear_sky_data['kw'].idxmax(), 'temperature_f'] if not clear_sky_data.empty else None,
            overcast_data.loc[overcast_data['kw'].idxmax(), 'temperature_f'] if not overcast_data.empty else None
        ]
    })

    peak_loads_by_weather = combined_data.groupby('weather_description').agg({
        'kw': 'max',
        'temperature_f': 'mean',
        'precipitation_in': 'mean',
        'sunshine_duration_sec': 'mean'
    }).reset_index().sort_values('kw', ascending=False)

    return peak_comparison_summary, peak_loads_by_weather

def visualize_data(peak_comparison_summary, peak_loads_by_weather):
    """
    Generates visualizations for the analysis.
    """
    # Peak comparison visualization
    plt.figure(figsize=(10, 6))
    sns.barplot(data=peak_comparison_summary, x='Condition', y='Peak Power Usage (kW)', palette='rocket')
    plt.title("Peak Power Usage: Clear Sky vs Overcast")
    plt.ylabel("Peak Power Usage (kW)")
    plt.xlabel("Weather Condition")
    plt.show()

    # Peak loads by weather condition
    plt.figure(figsize=(12, 8))
    sns.barplot(data=peak_loads_by_weather, x='kw', y='weather_description', palette="plasma")
    plt.title("Peak Power Loads by Weather Condition")
    plt.xlabel("Peak Power Usage (kW)")
    plt.ylabel("Weather Condition")
    plt.show()

def main():
    try:
        weather_data, lp_data = load_data()
        combined_data = clean_data(weather_data, lp_data)
        peak_comparison_summary, peak_loads_by_weather = analyze_data(combined_data)
        visualize_data(peak_comparison_summary, peak_loads_by_weather)
        print("Analysis and visualization completed successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
