
## CSV Load Profile Processor

This project processes a CSV file containing `date`, `time`, and `kw` columns to create a load profile and identify peak load information.

## Requirements

- Python 3.x
- pandas
- argparse

## Installation

Install the required packages using pip:

```ssh
pip install pandas argparse
```

## Usage

### PowerShell Script: lpd.ps1

The PowerShell script adds a header to the CSV file (if not already present) and then calls the Python script to process the file.

```ssh
.\lpd.ps1 <path_to_csv_file>
.\lpd.ps1 LP_comma_202401301627.csv
```

The script verifies that the specified file exists, checks if the header is already present, adds the header if needed, and calls the Python script. It includes error handling for file not found and general exceptions.

### Python Script: lpd.py

The Python script processes the CSV file to create a load profile and identify peak load information.

```ssh
python lpd.py <path_to_csv_file>
python lpd.py LP_comma_202401301627.csv
```

The input CSV file must contain the following columns:

-   `date`: Date in YYYY-MM-DD format
-   `time`: Time in HH:MM:SS format
-   `kw`: Numeric values representing power consumption

The script generates two output files:

-   Load Profile CSV: Contains the resampled 15-minute interval load profile data with summed kw values.
-   Peak Info CSV: Contains the datetime and total_kw value for the peak load.

Example Output Files:

-   LP_comma_202401301627_out.csv: Load profile data

```
datetime,total_kw
2024-01-01 00:15:00,13.972
```

-   LP_comma_202401301627_peak.csv: Peak load information
```
datetime,peak_total_kw
2024-01-06 09:15:00,37.12
```


The script reads the data into a DataFrame, checks if date, time, and kw columns are present, combines ‘date’ and ‘time’ to create a new datetime column, drops invalid rows, sets the datetime column as the DataFrame index, converts kw column to numeric, resamples the kw values into 15-minute intervals and sums the values for each interval, resets the index to get datetime back as a column, renames columns for clarity, identifies the row with the maximum total_kw value, creates output filenames based on the input file name, and saves the load profile and peak info to CSV files. It also includes error handling for FileNotFoundError, ValueError, and general exceptions.