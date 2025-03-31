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

## Function Map

Below is an ASCII map of all the functions within each file and how they get called from each file:

```
lpd-gui.py
==========
round_to_nearest_15_minutes()
display_datetime_range()
browse_file()
    └── update_status()
    └── display_datetime_range()
save_arguments_to_file()
    └── open()
    └── print()
launch_analysis()
    └── update_status()
    └── clear_output_textbox()
    └── save_arguments_to_file()
    └── launch_weather_analysis()
    └── update_status()
    └── update_status()
    └── str()
    └── print()
launch_weather_analysis()
    └── update_status()
    └── update_status()
clear_output_textbox()
open_folder()
    └── update_status()
clear_all()
    └── clear_output_textbox()
    └── update_status()
update_status()
start_analysis_thread()
    └── launch_analysis()
    └── update_status()
run_analysis()
    └── launch_analysis()
    └── update_status()

lpd-interactive.py
==================
load_style()
    └── open()
load_weather_codes()
    └── open()
translate_weather_codes()
group_weather_observations()
weather_observations()
    └── open()
process_csv()
add_traces()
    └── add_transformer_thresholds()
    └── add_daily_peak_load()
add_transformer_thresholds()
add_daily_peak_load()
add_weather_traces()
annotate_peak_load()
    └── max()
visualize_load_profile_interactive()
    └── load_style()
    └── add_traces()
    └── add_weather_traces()
    └── annotate_peak_load()
    └── handle_target_datetime()
handle_target_datetime()
    └── print()

lpd-main.py
===========
clear_screen()
process_csv()
    └── len()
    └── print_and_save()
    └── open()
    └── ValueError()
    └── print()
transformer_load_analysis()
    └── print()
    └── ValueError()
visualize_load_profile()
    └── print()
print_and_save()
    └── open()
    └── redirect_stdout()

lpd-merge.py
============
process_csv()
process_weather()
    └── print()

lpd-weather.py
==============
get_lat_lon_from_zip()
    └── print()
fetch_weather_for_date_range()
    └── zip()
    └── print()
main()
    └── len()
    └── get_lat_lon_from_zip()
    └── fetch_weather_for_date_range()
    └── open()
```

---

## File Tree
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
|   |   lpd-gui.spec
|   |   lpd-interactive.exe
|   |   lpd-interactive.py
|   |   lpd-interactive.spec
|   |   lpd-interactive2.py
|   |   lpd-main.exe
|   |   lpd-main.py
|   |   lpd-main.spec
|   |   lpd-weather.py
|   |   lpd_debug.log
|   |   weather-codes.txt
|   |   weather.py
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
