# Transformer Load Analysis Tool

## Overview

This project is a **Transformer Load Analysis and Visualization Tool** designed to process load data from CSV files. It performs various calculations such as load factors, diversity factors, and peak loads, and provides visualizations to help analyze transformer loading patterns.

The tool includes a graphical interface (GUI) for ease of use and a command-line utility for automated workflows.

---

## Features

- **Process CSV Load Data**:
  - Accepts CSV files with `meter`, `date`, `time`, and `kw` columns.
- **Transformer Analysis**:
  - Optionally analyzes load profiles against transformer KVA ratings.
- **Visualization**:
  - Generates time-based load profile graphs.
- **Metrics Calculation**:
  - Load Factor, Diversity Factor, Coincidence Factor, and more.
- **Error Handling**:
  - Validates input data and provides detailed error messages.
- **GUI Interface**:
  - Easy-to-use graphical interface for selecting files and configuring settings.

---

## Requirements

### Dependencies

Ensure the following Python libraries are installed:

```
pandas
matplotlib
tkinter
plotly
bokeh
```

`pip install -r requirements.txt`
`pip install pandas matplotlib plotly bokeh`

```Ubuntu
sudo apt-get install python3-tk
```
```MacOS
brew install python-tk
```

### Operating Systems

- Windows
- Linux
- macOS

---

## Files

## Input Data Format
The input CSV file should have the following structure:
```csv
meter,date,time,kw
85400796,2024-01-01,00:15:00.000,0.052
85400796,2024-01-01,00:30:00.000,0.048
```

### Main Scripts

- `lpd-gui.py`: GUI interface for load analysis.
- `lpd-main.py`: Main script for performing transformer load analysis.
- `lpd-interactive.py`: Generates interactive visualizations.
- `lpd-merge.py`: Merges load profiles with weather data.
- `lpd-weather.py`: Fetches weather data using APIs.

---

## Function Summary (./src-weather)

Below is a concise list of all functions with a short synopsis:

| **File**             | **Function**                         | **Synopsis**                                           |
|----------------------|--------------------------------------|--------------------------------------------------------|
| `lpd-gui.py`         | `round_to_nearest_15_minutes`        | Rounds datetime to the nearest 15-minute interval.     |
| `lpd-gui.py`         | `display_datetime_range`             | Reads CSV and displays the first and last date.        |
| `lpd-gui.py`         | `browse_file`                        | Opens file dialog to select CSV file.                  |
| `lpd-gui.py`         | `save_arguments_to_file`             | Saves user input arguments to a file.                  |
| `lpd-gui.py`         | `launch_analysis`                    | Launches load analysis and calls required scripts.     |
| `lpd-gui.py`         | `launch_weather_analysis`            | Runs weather analysis using lpd-weather.py.            |
| `lpd-gui.py`         | `clear_output_textbox`               | Clears the text output box in the GUI.                 |
| `lpd-gui.py`         | `open_folder`                        | Opens folder where input CSV is located.               |
| `lpd-gui.py`         | `clear_all`                          | Clears all user inputs and resets output.              |
| `lpd-gui.py`         | `update_status`                      | Updates status message in GUI.                         |
| `lpd-gui.py`         | `start_analysis_thread`              | Starts analysis in a background thread.                |
| `lpd-interactive.py` | `load_style`                         | Loads plotly graph styling from plotly.json.           |
| `lpd-interactive.py` | `load_weather_codes`                 | Loads weather codes from JSON.                         |
| `lpd-interactive.py` | `translate_weather_codes`            | Maps weather codes to descriptions.                    |
| `lpd-interactive.py` | `group_weather_observations`         | Groups consecutive identical weather observations.     |
| `lpd-interactive.py` | `weather_observations`               | Creates weather timeline visualization.                |
| `lpd-interactive.py` | `process_csv`                        | Loads load profile with weather data.                  |
| `lpd-interactive.py` | `add_traces`                         | Adds graph traces for load profile.                    |
| `lpd-interactive.py` | `add_transformer_thresholds`         | Adds threshold markers for transformer KVA % levels    |
| `lpd-interactive.py` | `add_daily_peak_load`                | Adds markers for daily peak loads.                     |
| `lpd-interactive.py` | `add_weather_traces`                 | Adds weather traces to graph.                          |
| `lpd-interactive.py` | `annotate_peak_load`                 | Annotates the graph with peak load values.             |
| `lpd-interactive.py` | `visualize_load_profile_interactive` | Generates interactive load profile visualization.      |
| `lpd-interactive.py` | `handle_target_datetime`             | Handles target datetime markers on graph.              |
| `lpd-main.py`        | `clear_screen`                       | Clears the console screen.                             |
| `lpd-main.py`        | `process_csv`                        | Processes CSV to generate load profile and results.    |
| `lpd-main.py`        | `transformer_load_analysis`          | Analyzes load profiles vs. transformer capacity.       |
| `lpd-main.py`        | `visualize_load_profile`             | Generates a time-based load profile visualization.     |
| `lpd-main.py`        | `print_and_save`                     | Saves analysis summary and prints to file.             |
| `lpd-merge.py`       | `process_csv`                        | Loads load profile CSV file.                           |
| `lpd-merge.py`       | `process_weather`                    | Loads and merges weather data with load profile.       |
| `lpd-weather.py`     | `get_lat_lon_from_zip`               | Fetches latitude/longitude from ZIP code using API.    |
| `lpd-weather.py`     | `fetch_weather_for_date_range`       | Fetches weather data for a using Open-Meteo API        |
| `lpd-weather.py`     | `main`                               | Main function to fetch and save weather data.          |
---


## File Tree
```
.
|   .gitattributes
|   .gitignore
|   LICENSE
|   README.md
|   requirements.txt
|
+---sample-data
|       22meters-365days-731K_rows.csv
|       22meters-500days-1000K_rows.csv
|       22meters-736days-1470K_rows.csv
|       22meters-list.csv
|       8meters-14days-10K_rows.csv
|       8meters-30days-23K_rows.csv
|       8meters-364days-278K_rows.csv
|       8meters-405days-307K_rows.csv
|       8meters-list.csv
|       923meters-7days-545K_rows.csv
|       98meters-300days-2788K_rows.csv
|       98meters-600days-5596K_rows.csv
|       98meters-list.csv
|       OCD226826-365days.csv
|       OCD226826-700days.csv
|
+---src-r1
|   |   arguments.txt
|   |   config.py
|   |   lpd-analytics.py
|   |   lpd-analytics2.py
|   |   lpd-analytics3.py
|   |   lpd-combined-analysis.py
|   |   lpd-gui.py
|   |   lpd-interactive.exe
|   |   lpd-interactive.py
|   |   lpd-interactive.spec
|   |   lpd-interactive2.py
|   |   lpd-main.exe
|   |   lpd-main.py
|   |
+---src-r2
|   |   arguments.txt
|   |   config.py
|   |   lpd-gui.py
|   |   lpd-interactive.py
|   |   lpd-main.py
|   |   lpd-merge.py
|   |   lpd-weather.py
|   |   lpd_debug.log
|   |   plotly.json
|   |   weather-codes.json
|   |
|
\---tests
    |   test-all.py
    |   test_lpd_gui.py
```
## Usage

### Graphical Interface (GUI)

1. Run the GUI (command line):
   ```bash
   python lpd-gui.py
   ```
2. Follow the on-screen instructions:
   - Select the input CSV file.
   - Enter the transformer KVA size.
   - Run the analysis and view results directly in the application.

### Command-Line Utility

1. Run the tool from the terminal:
   ```bash
   python lpd-main.py <input_csv_file> --transformer_kva <kva_size>
   ```
2. Outputs:
   - Analysis summary saved in `<input_file>_RESULTS.txt`.
   - Load profile saved in `<input_file>_RESULTS-LP.csv`.
   - Graph saved in `<input_file>_RESULTS-GRAPH.png`.

---


## Input Data Format
The input CSV file should have the following structure:
```csv
meter,date,time,kw
85400796,2024-01-01,00:15:00.000,0.052
85400796,2024-01-01,00:30:00.000,0.048
```
---

## Outputs

- **Analysis Summary**: Detailed metrics including Load Factor, Diversity Factor, and Coincidence Factor.
- **Load Profile CSV**: Aggregated time-based load profile data.
- **Visualization Graph**: A time-series plot showing load percentages against transformer capacity thresholds.

## Compiler syntax (future)
`pyinstaller --onefile --add-data "lpd-main.exe;." --distpath . lpd-gui.py`
`pyinstaller --onefile --distpath . lpd-main.py`
`pyinstaller --onefile --add-data "lpd-main.exe;lpd-main.exe" --add-data "lpd-interactive.exe;lpd-interactive.exe" --distpath . lpd-gui.py`

## Documentation
Additional documentation is available:
[GitHub Repository](https://github.com/michalcza/load-profile)
  
## Author
- **Michal Czarnecki**
- Email: mczarnecki@gmail.com
