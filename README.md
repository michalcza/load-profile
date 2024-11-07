
# Load Processing and Transformer Analysis Script

This Python script processes load data from a CSV file and performs a series of analyses to estimate system loads. It includes capabilities to analyze transformer loads based on user-specified parameters, calculate various load metrics, and optionally visualize the results.

## Features

1. **CSV File Processing**: Reads and validates load data from a CSV file with `meter`, `date`, `time`, and `kw` columns.
2. **System Load Calculations**: Estimates total system load, peak load, and other metrics.
3. **Transformer Load Analysis**: Calculates load distribution relative to a specified transformer size (in KVA).
4. **Optional Visualization**: Generates a time-based plot of the load data with transformer capacity thresholds.

## Prerequisites

- Python 3.x
- Required Python libraries:
  - `pandas`
  - `argparse`
  - `matplotlib`

Install the required libraries using:
```bash
pip install pandas matplotlib
```

## Usage

### Running the Script

Run the script from the command line with:
```bash
python lpd.py <path_to_csv_file>
```

Replace `<path_to_csv_file>` with the path to your input CSV file containing load data.

### Input Format

The input CSV file should have the following columns:
- `meter`: Meter ID
- `date`: Date in `YYYY-MM-DD` format
- `time`: Time in `HH:MM:SS.sss` format
- `kw`: Load in kilowatts (KW)

The script checks the format of the first two lines in the CSV file to ensure they match the expected structure.

### Options and Flow

1. **Scale Factor**: Upon running, you will be prompted to input a scale factor for estimating the total system load:
   - Acceptable range: `1.0 - 2.0`
   - Default value: `1.2` if no input is provided

2. **Transformer Analysis**:
   - After CSV processing, the script will ask if you'd like to perform transformer load analysis.
   - If you choose to proceed, you will be prompted to enter the transformer size in KVA.

3. **Visualization**:
   - You can opt to visualize the load profile after transformer analysis.
   - The graph shows the load over time with thresholds at 85%, 100%, and 120% of the transformer capacity.

### Output Files

The script generates several output files based on the input CSV file:
- `<input_file>_out.csv`: Load profile data with timestamped total load.
- `<input_file>_peak.csv`: Summary of peak load information.
- `<input_file>_factors.csv`: Key metrics, including diversity, load, coincidence, and demand factors.
- `<input_file>_xfrm_loading.txt`: Transformer capacity distribution, detailing the time spent in different load ranges.
- `<input_file>_visualization.png` (optional): Graph of load data with transformer capacity thresholds.

### Example

To process `load_data.csv` and perform all analyses, use:
```bash
python lpd.py load_data.csv
```

When prompted:
- Enter a scale factor (e.g., `1.2`) or press Enter to use the default.
- If proceeding with transformer analysis, enter the transformer size in KVA (e.g., `500`).
- Choose to visualize the load profile data.

## Error Handling

The script includes error handling for:
- Missing or incorrect CSV headers
- Invalid data formats
- File not found errors

Errors are reported in the console, and the script exits if it encounters an issue.

## License

This project is open-source and free to use under the [MIT License](https://opensource.org/licenses/MIT).

## To Do
- Error handling when dropping rows with bad data.  Sample file `sample-LP_comma_head_202410231511.csv` Will show Diversity Factor <1 and it is assumed that this is due to dropped rows where time conversion failed.
```
        # Drop rows where datetime conversion failed
        data = data.dropna(subset=['datetime'])
```
Graph visualization shows hole in data 10/22/2024
```
========================================================================================================================
                                                   Calculated Factors
========================================================================================================================
Diversity Factor:                    0.19 = sum(individual_maximum_demands) / peak_load
                                            Must be >=1 (more than 1)
                                            Reciprocal if Coincidence Factor
                                            2.23 means that a meter operates at peak load 2.23% of the time.
```
- Transformer loading calculations need to clarify this is for single-phase XFRM only. Three-phase MDU (120/208V) will not calculate corrrectly.
- Add GUI to upload data file.
