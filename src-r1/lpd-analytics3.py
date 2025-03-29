import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft
from flask import Flask, render_template_string
import os
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# Suppress Tkinter GUI root window
Tk().withdraw()

# Function to load a CSV file with error handling and dynamic selection
def load_csv_file(prompt):
    while True:
        try:
            print(prompt)
            file_path = askopenfilename(filetypes=[("CSV files", "*.csv")])
            if not file_path:
                raise ValueError("No file selected. Please select a valid CSV file.")
            if not file_path.endswith('.csv'):
                raise ValueError("Selected file is not a CSV. Please select a valid CSV file.")
            return pd.read_csv(file_path)
        except Exception as e:
            print(f"Error: {e}. Please try again.")

# Load datasets with error handling and dynamic file selection
print("Select the first CSV file (e.g., Power Usage Data):")
power_data = load_csv_file("Please select the power usage CSV file.")
print("Select the second CSV file (e.g., Weather Data):")
weather_data = load_csv_file("Please select the weather data CSV file.")

# Merge datasets by date and time with handling for mismatched or missing date-time entries
power_data['DateTime'] = pd.to_datetime(power_data['date'] + ' ' + power_data['time'], errors='coerce')
weather_data['DateTime'] = pd.to_datetime(weather_data['datetime'], errors='coerce')

# Drop rows with invalid date-time values
power_data = power_data.dropna(subset=['DateTime'])
weather_data = weather_data.dropna(subset=['DateTime'])

merged_data = pd.merge_asof(
    power_data.sort_values('DateTime'),
    weather_data.sort_values('DateTime'),
    on='DateTime',
    direction='nearest'
)

# Extract subsets based on weather conditions
clear_sky_data = merged_data[merged_data['weather_code'] == 0]

# Compute peak power usage and corresponding temperature_fs
peak_power_row = merged_data.loc[merged_data['kw'].idxmax()]
peak_power = peak_power_row['kw']
corresponding_temperature_f = peak_power_row['temperature_f']

# Aggregate data by weather condition
weather_summary = merged_data.groupby('weather_code').agg({
    'temperature_f': ['max', 'mean'],
    'precipitation_in': 'sum'
}).reset_index()
weather_summary.columns = ['weather_code', 'Peaktemperature_f', 'Meantemperature_f', 'Totalprecipitation_in']

# Compute correlation between peak loads and weather conditions
def compute_peak_load_correlation(data):
    grouped = data.groupby('weather_code').agg({
        'kw': 'max',
        'temperature_f': 'mean',
        'precipitation_in': 'mean'
    }).reset_index()
    correlation_matrix = grouped.corr()
    return correlation_matrix

peak_load_correlation_matrix = compute_peak_load_correlation(merged_data)

# Fourier transform for periodic analysis with interpretation
power_fft = fft(merged_data['kw'].fillna(0))
frequencies = np.fft.fftfreq(len(power_fft), d=1)

# Identify key periodic components
fft_magnitude = np.abs(power_fft)
peak_indices = np.argsort(fft_magnitude)[-5:]  # Top 5 frequency components
key_frequencies = frequencies[peak_indices]
key_magnitudes = fft_magnitude[peak_indices]

# Print interpretation of periodic components
print("Key Periodic Components:")
for freq, mag in zip(key_frequencies, key_magnitudes):
    period = 1 / freq if freq != 0 else "Infinity"
    print(f"Frequency: {freq:.5f}, Magnitude: {mag:.2f}, Period: {period}")

# Visualization setup
output_folder = "output_visuals"
os.makedirs(output_folder, exist_ok=True)

# Plot time series data
plt.figure()
plt.plot(merged_data['DateTime'], merged_data['kw'], label='Power Usage')
plt.title("Power Usage Over Time")
plt.xlabel("Time")
plt.ylabel("Power Usage")
plt.legend()
plt.savefig(os.path.join(output_folder, "power_usage_over_time.png"))

# Plot weather summary
weather_summary.plot(x='weather_code', y=['Peaktemperature_f', 'Meantemperature_f', 'Totalprecipitation_in'], kind='bar')
plt.title("Weather Summary Metrics")
plt.savefig(os.path.join(output_folder, "weather_summary_metrics.png"))

# Plot FFT results
plt.figure()
plt.plot(frequencies, fft_magnitude)
plt.scatter(key_frequencies, key_magnitudes, color='red', label='Key Components')
plt.title("Fourier Transform of Power Usage")
plt.xlabel("Frequency")
plt.ylabel("Amplitude")
plt.legend()
plt.savefig(os.path.join(output_folder, "fourier_transform.png"))

# Flask app to display results
app = Flask(__name__)

@app.route("/")
def index():
    weather_summary_html = weather_summary.to_html(index=False)
    peak_load_correlation_html = peak_load_correlation_matrix.to_html()
    return render_template_string(f"""
    <h1>Data Analysis Results</h1>
    <h2>Weather Summary</h2>
    {weather_summary_html}
    <h2>Peak Load Correlation Matrix</h2>
    {peak_load_correlation_html}
    <h2>Key Periodic Components</h2>
    <ul>
        {''.join([f'<li>Frequency: {freq:.5f}, Magnitude: {mag:.2f}, Period: {1/freq if freq != 0 else "Infinity"}</li>' for freq, mag in zip(key_frequencies, key_magnitudes)])}
    </ul>
    <h2>Visualizations</h2>
    <img src="/static/power_usage_over_time.png" alt="Power Usage Over Time">
    <img src="/static/weather_summary_metrics.png" alt="Weather Summary Metrics">
    <img src="/static/fourier_transform.png" alt="Fourier Transform">
    """)

# Save visuals to static folder
static_folder = os.path.join(app.root_path, 'static')
os.makedirs(static_folder, exist_ok=True)
for filename in os.listdir(output_folder):
    os.rename(os.path.join(output_folder, filename), os.path.join(static_folder, filename))

if __name__ == "__main__":
    app.run(debug=True)
