
# README.md
# CSV Load Profile Processor

This project includes a PowerShell script and a Python script to process CSV files containing power consumption data and calculate various factors.

## Requirements

- PowerShell
- Python 3.x
- pandas
- argparse

## Installation

Install the required Python packages using pip:

```sh
pip install pandas argparse
``` 

## PowerShell Script: `lpd.ps1`

### Description

The PowerShell script adds a header to the CSV file (if not already present) and then calls the Python script to process the file.

### Usage
Run the PowerShell script with the path to the input CSV file as an argument:
`.\lpd.ps1 <path_to_csv_file>` 

### Example
`.\lpd.ps1 LP_comma_202401301627.csv` 

### Script Details
1.  **Check if File Exists**: Verifies that the specified file exists.
2.  **Check for Existing Header**: Reads the first line of the file to check if the header is already present.
3.  **Add Header if Needed**: If the header is not present, adds the header to the file.
4.  **Call Python Script**: Calls the Python script to process the CSV file.

### Error Handling
The script includes error handling for file not found and general exceptions.

## Python Script: `lpd.py`

### Description
The Python script processes the CSV file to create a load profile, identify peak load information, and calculate various factors.

### Usage
Run the Python script with the path to the input CSV file as an argument:
`python lpd.py <path_to_csv_file>` 

### Example
`python lpd.py LP_comma_202401301627.csv` 

### Input File Format
The input CSV file must contain the following columns:
-   `date`: Date in `YYYY-MM-DD` format
-   `time`: Time in `HH:MM:SS` format
-   `kw`: Numeric values representing power consumption

### Output Files
The script generates three output files:
1.  **Load Profile CSV**: Contains the resampled 15-minute interval load profile data with summed `kw` values.
2.  **Peak Info CSV**: Contains the datetime and `total_kw` value for the peak load.
3.  **Factors CSV**: Contains calculated values for diversity factor, load factor, coincidence factor, and demand factor.

### Example Output Files
-   `LP_comma_202401301627_out.csv`: Load profile data
```
datetime,total_kw
2024-01-01 00:15:00,13.972
```
-   `LP_comma_202401301627_peak.csv`: Peak load information
```
datetime,peak_total_kw
2024-01-06 09:15:00,37.12
```
-   `LP_comma_202401301627_factors.csv`: Calculated factors
```
factor,value
diversity_factor,1.7591594827586208
load_factor,0.4951682605962644
coincidence_factor,0.5684532924961715
demand_factor,0.5684532924961715
```

### Script Details
1.  **Read the CSV file**: Reads the data into a DataFrame.
2.  **Ensure required columns**: Checks if `date`, `time`, and `kw` columns are present.
3.  **Combine 'date' and 'time'**: Creates a new `datetime` column by combining `date` and `time` columns and converting them to a datetime object.
4.  **Drop invalid rows**: Drops rows where `datetime` conversion failed.
5.  **Set datetime index**: Sets the `datetime` column as the DataFrame index.
6.  **Ensure 'kw' is numeric**: Converts `kw` column to numeric, coercing errors.
7.  **Resample data**: Resamples the `kw` values into 15-minute intervals and sums the values for each interval.
8.  **Reset index**: Resets the index to get `datetime` back as a column.
9.  **Rename columns**: Renames columns for clarity.
10.  **Find peak load**: Identifies the row with the maximum `total_kw` value.
11.  **Calculate Factors**: Dynamically calculates individual maximum demands and total connected load from the data, and computes diversity factor, load factor, coincidence factor, and demand factor.
12.  **Generate output filenames**: Creates output filenames based on the input file name.
13.  **Save results**: Saves the load profile, peak info, and factors to CSV files.
14.  **Error Handling**: Catches and prints appropriate error messages for `FileNotFoundError`, `ValueError`, and general exceptions.