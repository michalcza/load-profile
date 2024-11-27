
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
- `pandas`
- `matplotlib`
- `tkinter` (comes pre-installed with Python)

### Operating Systems
- Windows
- Linux
- macOS

---

## Files
### 1. `lpd-gui.py`
- A graphical interface for running the tool.
- Features:
  - File selection dialog.
  - Input for transformer KVA size.
  - Displays output directly in the GUI.
  
### 2. `lpd-gui.exe`
- Binary executable wrappper of lpd-gui.py
- Makes sure all rewuired libraries are pre-packaged.
- Use the following syntax to compile. MUST BE COMPILED SECOND.
`$ pyinstaller --onefile --add-data "lpd-main.exe;." --distpath . lpd-gui.py`

### 3. `lpd-main.py`
- Command-line utility for performing the load analysis.
- Features:
  - Processes CSV files.
  - Generates outputs: `.txt`, `.csv`, and `.png` files.
  
### 4. `lpd-main.exe`
- Binary executable wrappper of lpd-main.py
- Launched in command-line, or through lpd-gui.exe, or lpd-gui.py
- Use the following syntax to compile. MUST BE COMPILED FIRST.
`$ pyinstaller --onefile --distpath . lpd-main.py`

### Output Files:
- `<input_file>_RESULTS.txt`: Contains analysis summary and metrics.
- `<input_file>_RESULTS-LP.csv`: Aggregated time-based load profile data.
- `<input_file>_RESULTS-GRAPH.png`: Graphical visualization of the load profile.

---

## Usage

### Graphical Interface (GUI)
1. Run the GUI (command line):
   ```bash
   python lpd-gui.py
   ```
   or executable binary"
   ```bash
   lpd-gui.exe
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
   Example:
   ```bash
   python lpd-main.py 98meters-300days-2788K_rows.csv --transformer_kva 75
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

### Requirements:
- Columns: `meter`, `date`, `time`, and `kw`.
- Date Format: `YYYY-MM-DD`.
- Time Format: `HH:MM:SS.mmm`.
- `kw`: Numeric values representing load in kilowatts.

---

## Outputs
- **Analysis Summary**: Detailed metrics including Load Factor, Diversity Factor, and Coincidence Factor.
- **Load Profile CSV**: Aggregated time-based load profile data.
- **Visualization Graph**: A time-series plot showing load percentages against transformer capacity thresholds.

---

## Sample Data and Results
The tool has been tested on datasets of various sizes:

+--------+-------+-------+----------+---------+
| Meters | Days  | Rows  | Filesize | Status  |
+--------+-------+-------+----------+---------+
|     22 |   365 |  731K |   28.4MB | PASS    |
|     22 |   500 | 1000K |   38.9MB | PASS    |
|     22 |   736 | 1470K |   57.0MB | PASS    |
|      8 |   364 |  278K |   10.8MB | PASS    |
|      8 |   405 |  307K |   11.9MB | PASS    |
|      8 |    14 |   10K |    0.4MB | PASS    |
|      8 |    30 |   24K |    0.8MB | PASS    |
|    932 |     7 |  545K |   21.1MB | PASS    |
|     98 |   300 | 2788K |  108.0MB | PASS    |
|     98 |   600 | 5596K |  216.8MB | PASS    |
+--------+-------+-------+----------+---------+

---

## Documentation
- Additional documentation is available:
  - [Google Docs](https://tinyurl.com/cshac3an)
  - [GitHub Repository](https://github.com/michalcza/load-profile)

---

## Author
- **Michal Czarnecki**
- Email: mczarnecki@gmail.com

--- 
