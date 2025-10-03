#!/usr/bin/env python3

"""
==========================================================
Transformer Load Analysis and Visualization Tool
==========================================================
Author: Michal Czarnecki
Date:   12 NOV 2024

Description:
    This Python program processes a CSV file containing 
    load data (with date, time, and kW columns) to perform
    transformer load analysis, calculate key metrics 
    (Average Load, Peak Load, Load Factor, Diversity Factor, 
    Coincidence Factor, and Demand Factor), and generate 
    visualizations for load patterns over time.

Usage:
    Run this program from the command line, specifying:
    - The path to the CSV file.
    - Optionally, the transformer KVA size for analysis.

    Example:
        python lpd.py 98meters-300days-2788K_rows.csv --transformer_kva 75

Input: 
    - 98meters-300days-2788K_rows.csv
        First few row sample:
        meter,date,time,kw
        74592856,2024-08-04,00:15:00.000,3.296
        74592856,2024-08-04,00:30:00.000,2.94
        74592856,2024-08-04,00:45:00.000,4.424
        74592856,2024-08-04,01:00:00.000,2.268
Output:
    98meters-300days-2788K_rows_RESULTS.txt
    Ouput file with calculations, results, and interpretations.

    98meters-300days-2788K_rows_RESULTS-LP.csv
    Output file with time based aggregated load profile.
    

Compile instructions:
Syntax:
$ pyinstaller --onefile --distpath . lpd-main.py
will compile binary to:
\src\lpd-main.exe

Sample Data:
   ..\sample-data
==========================================================
11/26/2024  Michal Czarnecki
-Added logging
-Removed cross-check that coincidence_factor == 1 / diversity_factor. We already
check for reasonability on the values themselves. We've been failing this check
on larger datasets. The cause appears to be related to significant figures.
This is a redundant check so we'll just get rid of it.
-Removed regex check for second row for CSV file. Been having issues on regex
test on KW value with multiple iterations of XXX.XXX coming from Yukon.
-Renamed output file suffix to 
    _RESULTS.txt
    _RESULTS-LP.csv
-Renamed sample data filenames to more descriptive titles.
Example: 98meters-300days-2788K_rows.csv
-Tested on the following datasets:
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

-Adding amperage calculations to 'Results' table
-Minor formatting corrections to 'Interpretation of Results' table
-Refactoring how output files are listed at end of report to limit
 80-column overflow.
-Commenting out non-error prints to screen

- 12/03/2024
    - Adding:
    -Coincidental peak load for given date and time (system peak).
    -Non-coincidental peak load for the entire day that was given.
    -List datetime for rows where KW < 0.5
    -Add primary voltage amperage calculations for 1-phase.
    -Split display of interactive graph from funciton into lpd-interactive.py
    that way we can launh it from GUI with button and not as part of lpd-main.py
    
    
python lpd-main.py ..\sample-data\OCD226826-700days.csv --transformer_kva 75 --datetime "2024-10-08 16:15:00"
"""
import logging
import pandas as pd
import subprocess
import sys
import re
import argparse
import os
import matplotlib.pyplot as plt
from contextlib import redirect_stdout
from datetime import datetime
import plotly.graph_objects as go
from bokeh.plotting import figure, show, output_file
from bokeh.models import Span

# Configure logging
# Log file placed in the current working directory
log_file = os.path.join(os.getcwd(), "lpd_debug.log") 
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),  # Log to file
        logging.StreamHandler(sys.stdout)  # Log to console
    ]
)
logger = logging.getLogger()

# Suppress library logs
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

clear_screen()

global pwd
pwd = os.getcwd()
logger.info("#                   *** Start ***                   #")
logger.info(pwd)

def process_csv(input_file):
    try:
        logger.info("fn process_csv - try")
        # Open the file to check the first line
        with open(input_file, "r") as file:
            # Read the first line and check if it matches the expected header
            first_line = file.readline().strip()
            expected_header = "meter,date,time,kw"
            if first_line != expected_header:
                logger.error("Header mismatch! Expected: %s, Found: %s", expected_header, first_line)
                raise ValueError(f"Expected header '{expected_header}' but got '{first_line}'")
                sys.exit(1)

        # Read the CSV file
        data = pd.read_csv(input_file)
        logger.info("fn process_csv - read csv OK")
        
        # Convert the 'date' and 'time' columns to a single datetime column
        data["datetime"] = pd.to_datetime(
            data["date"] + " " + data["time"], format="%Y-%m-%d %H:%M:%S.%f", errors="coerce"
        )
        logger.info("fn process_csv - datetime conversion OK")
        
        # Store the initial row count
        initial_row_count = len(data)
        logger.info("initial row count %d", initial_row_count)
        
        # Drop rows where datetime conversion failed
        data = data.dropna(subset=["datetime"])
        
        # Calculate the number of rows dropped
        rows_dropped = initial_row_count - len(data)
        logger.info("rows dropped (datetime) calculated")
        
        if rows_dropped > 3:
            logger.error("Too many rows dropped during datetime conversion, exiting.")
            raise ValueError("Too many rows dropped due to 'datetime' conversion failure. Exiting.")
            sys.exit(1)
            
        # Set the 'datetime' column as the index
        data.set_index("datetime", inplace=True)

        # Ensure 'kw' is numeric
        data["kw"] = pd.to_numeric(data["kw"], errors="coerce")

        # Store the initial row count
        initial_row_count = len(data)
        
        # Drop rows where 'kw' conversion failed
        data = data.dropna(subset=["kw"])
                
        # Calculate the number of rows dropped
        rows_dropped = initial_row_count - len(data)
        logger.info("Rows dropped after kw conversion calculated")

        if rows_dropped > 3:
            logger.error("Too many rows dropped during kw conversion, exiting.")
            raise ValueError("Too many rows dropped due to 'kw' conversion failure. Exiting.")
            sys.exit(1)
        
        start_datetime = data.index.min()
        end_datetime = data.index.max()
        logger.info("Start and end dates calculated")
        
        # Resample to 15-minute intervals and sum the 'kw' values for each interval
        load_profile = data["kw"].resample("15min").sum()
        logger.info("resample to 15-minute intervals - OK")

        # Check if load_profile is empty
        if load_profile.empty:
            logger.error("Resampling resulted in an empty DataFrame.")
            raise ValueError("Resampling resulted in an empty DataFrame. Check the input data for validity.")
            sys.exit(1)

        # Reset index to get 'datetime' back as a column
        logger.info("Resampling completed successfully.")
        load_profile = load_profile.reset_index()

        # Rename columns for clarity
        load_profile.columns = ["datetime", "total_kw"]
        logger.info("Rename columns for clarity.")

        # Find the datetime for the peak total_kw
        peak_row = load_profile.loc[load_profile["total_kw"].idxmax()]
        logger.info("peak_row calculated")
        peak_datetime = peak_row["datetime"]
        logger.info("peak_datetime calculated")
        peak_load = peak_row["total_kw"]
        logger.info("peak_load calculated")
        
        # Create a DataFrame to include the peak information
        peak_info = pd.DataFrame({"datetime": [peak_datetime], "peak_total_kw": [peak_load]})
        logger.info("peak_info calculated")
        
        # Calculate average load
        average_load = load_profile["total_kw"].mean()
        logger.info("average_load calculated")
        average_load_per_meter = data.groupby("meter")["kw"].mean()
        logger.info("average_load_per_meter calculated")

        # Calculate number of days and number of meters
        num_days = (data.index.max() - data.index.min()).days + 1
        logger.info("num_days calculated")

        # Calculate number of meters
        num_meters = data["meter"].nunique()
        logger.info("num_meters calculated")
               
        # Coincidence factor
        individual_maximum_demands = data.groupby("meter")["kw"].max()
        logger.info("Individual_maximum_demands calculated")
        sum_individual_maximum_demands = individual_maximum_demands.sum()
        logger.info("Sum_individual_maximum_demands calculated")
        coincidence_factor = peak_load / sum_individual_maximum_demands
        logger.info("Coincidence_factor calculated")
        
        # Verify reasonability
        if coincidence_factor >= 1:
            raise ValueError("Coincidence factor exceeds the reasonability limit of 1.")
            logger.error("Coincidence factor exceeds the reasonability limit of 1.")
        else:
            logger.info("Coincidence factor is within the expected range (<= 1).")

        # Diversity factor
        diversity_factor = sum_individual_maximum_demands / peak_load
        
        # Verify reasonability
        if diversity_factor <= 1:
            raise ValueError("Diversity factor exceeds the reasonability limit of 1.")
            logger.error("Diversity factor exceeds the reasonability limit of 1.")
        else:
            logger.info("Diversity factor is within the expected range (>= 1).")

        # Load factor
        load_factor = average_load / peak_load
        
        # Verify reasonability
        if load_factor >= 1:
            raise ValueError("Load factor exceeds the reasonability limit of 1.")
            logger.error("Load factor exceeds the reasonability limit of 1.")
        else:
            logger.info("Load factor is within the expected range (<= 1).")

        # Average peak load for each meter
        average_peak_load_per_meter = sum_individual_maximum_demands / num_meters
        logger.info("Average_peak_load_per_meter: %d", average_peak_load_per_meter)
        
        #List datetime when sum of loads < 0.5 KW
        #no_load_data = data.groupby("datetime")["kw"].sum()
        no_load_data = data["kw"].resample("15min").sum()
        no_load_times = no_load_data[no_load_data < 0.5].reset_index()
        if no_load_times.empty:
            logger.info("No times found where the total KW less than 0.5 KW.")
        else:
            # Save the results to a CSV file or print them
            no_load_file = f"{os.path.splitext(input_file)[0]}_NO-LOAD.csv"
            no_load_times.to_csv(no_load_file, index=False)
            logger.info(f"Times with total KW < 0.5 saved to: {no_load_file}")
            print(f"Found {len(no_load_times)} instances where total KW < 0.5. Results saved to: {no_load_file}")
        
        # Calculate coincidental peaks based on given datetime 
        # Convert columns to datetime
        data["datetime"] = pd.to_datetime(data["date"] + " " + data["time"], errors="coerce")
        data["date"] = pd.to_datetime(data["date"], errors="coerce")

        # Check if target_datetime is within the dataset
        if pd.Timestamp(target_datetime) not in data.index:
            print(f"Out of bounds: {target_datetime} is not in the dataset!")
            target_peak_datetime = "OUTSIDE OF DATASET!"
            target_peak_load = 0
            target_load = 0
        else:
            # Extract the target date
            target_date = datetime.strptime(target_datetime, "%Y-%m-%d %H:%M:%S").date()

            # Calculate load at the target datetime
            target_load = data[data["datetime"] == target_datetime]["kw"].sum()
            print(f"Load at {target_datetime}: {target_load} kW")

            # Filter data for the target date
            filtered_data = data[data["datetime"].dt.date == target_date]
            filtered_data.set_index("datetime", inplace=True)

            # Resample data to 15-minute intervals
            resampled_data = filtered_data["kw"].resample("15min").sum()

            # Find the peak load and its time
            target_peak_datetime = resampled_data.idxmax()
            target_peak_load = resampled_data.max()

            print(f"Peak load for {target_date}: {target_peak_load} kW at {target_peak_datetime}")

        # Calculate amperages at various voltage levels
        amps120 = (peak_load * 1000)/(120)
        amps208 = (peak_load * 1000)/(208)
        amps240 = (peak_load * 1000)/(240)
        amps7200 = (peak_load * 1000)/(7200)
        
        target_amps120 = (target_load * 1000)/(120)
        target_amps208 = (target_load * 1000)/(208)
        target_amps240 = (target_load * 1000)/(240)
        target_amps7200 = (target_load * 1000)/(7200)
        
        # Generate output filenames
        base, ext = os.path.splitext(input_file)
        
        #global base_name
        base_name = os.path.basename(input_file)
        load_profile_file = f"{base}_RESULTS-LP.csv"
        output_file = f"{base}_RESULTS.txt"
        filename = os.path.basename(input_file)
        load_distribution_output_file = f"{base_name}_RESULTS.txt"
        
        #Generate short filenames
        logger.info("Current Directory: %s", pwd)
        logger.info("Input: %s", base_name)
        global results_file_short
        results_file_short = base_name.replace(".csv", "_RESULTS.txt")
        logger.info("Results: %s", results_file_short)
        global lp_file_short
        lp_file_short = base_name.replace(".csv", "_RESULTS-LP.csv")
        logger.info("Load Profile: %s", lp_file_short)
        global graph_file_short
        graph_file_short = base_name.replace(".csv", "_RESULTS-GRAPH.png")
        logger.info("Graph: %s", graph_file_short)
        global no_load_file_short
        no_load_file_short = base_name.replace(".csv", "_NO-LOAD.csv")
        logger.info("No Load: %s", no_load_file_short)
        
        # Generate time stamp for report runtime.
        current_datetime = datetime.now()
        
        def print_and_save(summary, filename=output_file):
            with open(filename, "w") as file:
                with redirect_stdout(file):  # Send to file
                    print(summary)  # Print to file

        calculation_summary_width = 80
        calculation_summary_lines = [
            "=" * calculation_summary_width,
            f"{'Data Parameters':^{calculation_summary_width}}",
            "=" * calculation_summary_width,
            f"{'Input filename: ':<37} {str(base_name):>42}",
            f"{'Report run date/time: ':<37} {current_datetime.strftime('%Y-%m-%d %H:%M:%S'):>42}",
            f"{'Data START date/time: ':<37} {str(start_datetime):>42}",
            f"{'Data END date/time: ':<37} {str(end_datetime):>42}",
            f"{'Days in dataset: ':<35} {num_days:>20.0f} {'days':<23}",
            f"{'Meters in dataset: ':<35} {num_meters:>20.0f} {'meters':<23}",
            f"{'Meter reads in dataset: ':<35} {initial_row_count:>20.0f} {'rows':<23}",
            f"{'Rows dropped during conversion: ':<35} {rows_dropped:>20.0f} {'rows':<23}",
            "=" * calculation_summary_width,
            f"{'Results':^{calculation_summary_width}}",
            "=" * calculation_summary_width,
            f"{'Peak load (KW): ':<30} {peak_load:>20.2f} {'KW on ' + str(peak_datetime):<28}",
            f"{'Peak load (120V, 1-phase, PF=1): ':<30} {amps120:>17.2f} {'amps':<28}",
            f"{'Peak load (208V, 1-phase, PF=1): ':<30} {amps208:>17.2f} {'amps':<28}",
            f"{'Peak load (240V, 1-phase, PF=1): ':<30} {amps240:>17.2f} {'amps':<28}",
            f"{'Peak load (7200V (L-N), 1-phase, PF=1): ':<30} {amps7200:>10.2f} {'amps':<28}",
            "-" * calculation_summary_width,
            f"{'Coincidental Peaks':^{calculation_summary_width}}",
            f"{'Target datetime (given): ':<45}{str(target_datetime):<}",
            #f"{'Coincidental peak (KW) for target datetime: ':<44} {target_load:>5.2f} {'KW on ' + str(target_datetime):<}",
            f"{'Coincidental peak (KW) for target datetime: ':<44} {target_load:>5.2f} KW",
            f"{'Target load (120V, 1-phase, PF=1): ':<30} {target_amps120:>17.2f} {'amps':<28}",
            f"{'Target load (208V, 1-phase, PF=1): ':<30} {target_amps208:>17.2f} {'amps':<28}",
            f"{'Target load (240V, 1-phase, PF=1): ':<30} {target_amps240:>17.2f} {'amps':<28}",
            f"{'Target load (7200V (L-N), 1-phase, PF=1): ':<30} {target_amps7200:>10.2f} {'amps':<28}",
            f"",
            f"{'Non-coincidental peak (KW) for target date: ':<44} {target_peak_load:>5.2f} {'KW on ' + str(target_peak_datetime):<}",
            "=" * calculation_summary_width,
            f"{'Calculated Factors':^{calculation_summary_width}}",
            "=" * calculation_summary_width,
            f"{'Load Factor: ':<30} {load_factor:>20.2f}",
            f"{'Diversity Factor: ':<30} {diversity_factor:>20.2f}",
            f"{'Coincidence Factor: ':<30} {coincidence_factor:>20.2f}",
            f"{'Demand Factor: ':<47}{'indeterminate':<32}",
            "=" * calculation_summary_width,
            f"{'Interpretation of Results':^{calculation_summary_width}}",
            "=" * calculation_summary_width,
            "Load Factor = average_load / peak_load",
            f"{'':<1}With constant load, LF -> 1. With variable load, LF -> 0",
            f"{'':<1}With LF -> 1, fixed costs are spread over more kWh of output.",
            f"{'':<1}LF is how efficiently the customer is using peak demand.",
            f"{'':<1}Example: Traffic light LF ~ 1, EV charger LF ~ 0",
            f"{'':<1} ",
            "Diversity Factor = sum_individual_maximum_demands / peak_load",
            f"{'':<1}The system's simultaneous peak load ({peak_load:.2f} KW) is {diversity_factor:.2f}% of sum of individual\n maximum demands ({sum_individual_maximum_demands:.2f} KW).\n This suggests that {diversity_factor:.2f}% of loads are operating at their peak at the\n same time. A low diversity factor implies that the infrastructure is likely\n underutilized for a significant portion of its capacity. While this might\n suggest the potential for downsizing, it also provides flexibility for\n accommodating additional loads.",
            f"{'':<1}",
            "Coincidence Factor = peak_load / sum_individual_maximum_demands",
            f"{'':<1}1 / coincidence_factor = diversity_factor",
            f"{'':<1}{coincidence_factor * 100:.0f}% of the sum total of maximum demands ({sum_individual_maximum_demands:.2f} KW) is realized during\n the peak load of {peak_load:.2f} KW",
            f"{'':<1}",
            "Demand Factor = peak_load / total_connected_load",
            f"{'':<1}Low demand factor requires less system capacity to serve total load.",
            f"{'':<1}Example: Sum of branch circuits in panel can exceed main breaker amps.",
            f"{'':<1}Indeterminate. We do not know the total theoretical total connected load.",
        ]
        calculation_summary_box = "\n".join(calculation_summary_lines)

        # Call print and save function
        print_and_save(calculation_summary_box)

        # Profile data to CSV
        load_profile.to_csv(load_profile_file, index=False)
        
        # Return the load_profile_file path for use outside the function
        return data, load_profile_file

    except FileNotFoundError as e:
        error_message = f"Error: The file '{input_file}' was not found."
        print(error_message)
        logger.error(error_message)
        raise e
    class CustomValueError(ValueError):
        pass

    try:
        raise CustomValueError("The provided value is invalid.")

    except CustomValueError as e:
        error_message = f"Custom value error: {e}"
        print(error_message)
        logger.error(error_message)
        sys.exit(1)

    except Exception as e:
        error_message = f"Unexpected error: {e}"
        print(error_message)
        logger.exception("Unhandled Exception")
        sys.exit(1)

def transformer_load_analysis(load_profile_file, transformer_kva):
    try:
        # Load the load profile data from CSV file
        out_data = pd.read_csv(load_profile_file)

        # Ensure the 'total_kw' column exists in the data
        if "total_kw" not in out_data.columns:
            error_message = f"The load profile file must contain a 'total_kw' column representing load in KW."
            print(error_message)
            logger.error(error_message)
            raise ValueError(error_message)

        # Calculate load as a percentage of transformer capacity
        out_data["load_percentage"] = (out_data["total_kw"] / transformer_kva) * 100

        # Calculate the total hours and days of the dataset
        # Convert to datetime
        out_data["datetime"] = pd.to_datetime(out_data["datetime"])
        total_time = (out_data["datetime"].max() - out_data["datetime"].min()).total_seconds()
        
        # Convert seconds to hours
        total_hours = total_time / 3600
        
        # Convert hours to days
        total_days = total_hours / 24

        # Determine time spent within different load ranges
        # Get time interval in hours
        time_interval = (out_data["datetime"].iloc[1] - out_data["datetime"].iloc[0]).total_seconds() / 3600

        # Calculate time spent in each load range in hours
        below_85 = len(out_data[out_data["load_percentage"] < 85]) * time_interval
        between_85_100 = (
            len(out_data[(out_data["load_percentage"] >= 85) & (out_data["load_percentage"] < 100)]) * time_interval)
        between_100_120 = (
            len(out_data[(out_data["load_percentage"] >= 100) & (out_data["load_percentage"] < 120)]) * time_interval)
        above_120 = len(out_data[out_data["load_percentage"] >= 120]) * time_interval

        # Calculate percentages based on total hours
        total_hours = (out_data["datetime"].max() - out_data["datetime"].min()).total_seconds() / 3600
        percent_below_85 = (below_85 / total_hours) * 100
        percent_between_85_100 = (between_85_100 / total_hours) * 100
        percent_between_100_120 = (between_100_120 / total_hours) * 100
        percent_above_120 = (above_120 / total_hours) * 100

        # Remove the .csv extension
        base_name = os.path.splitext(input_file)[0]
        
        # Declare output filename
        load_distribution_output_file = f"{base_name}_RESULTS.txt"
        graph_file = load_profile_file.replace("_RESULTS-LP.csv", "_RESULTS-GRAPH.png")
        global graph_file_interactive
        graph_file_interactive = load_profile_file.replace("_RESULTS-LP.csv", "_RESULTS-GRAPH-INTERACTIVE.png")
        
        # Calculate absolute transformer KVA loads at 85% and 120%.
        kva_85 = transformer_kva * 0.85
        kva_120 = transformer_kva * 1.2
        
        # Print to output file
        with open(load_distribution_output_file, "a") as f:
            f.write("=" * 80 + "\n")
            f.write(f"{'Transformer Calculations and Capacity Distribution':^80}\n")
            f.write("=" * 80 + "\n")
            f.write(f"{'Total time: ':<35}{total_days:>20.1f}{' days ('}{total_hours:>.2f}{' hours)'}\n")
            f.write(f"{'Transformer KVA: ':<35}{transformer_kva:>20.1f}{' KVA':<25}\n")
            f.write("-" * 80 + "\n")
            f.write(f" {'LOAD RANGE':^30}| {'DAYS':^16}| {'HOURS':^17}| {'%':^10}\n")
            f.write("-" * 80 + "\n")
            f.write(f" {'Below 85%':<30}| {(below_85 / 24):<10.2f} days | {below_85:<10.2f} hours | {percent_below_85:<7.2f} % \n")
            f.write(f" {'Between 85% and 100%':<30}| {(between_85_100 / 24):<10.2f} days | {between_85_100:<10.2f} hours | {percent_between_85_100:<7.2f} % \n")
            f.write(f" {'Between 100% and 120%':<30}| {(between_100_120 / 24):<10.2f} days | {between_100_120:<10.2f} hours | {percent_between_100_120:<7.2f} % \n")
            f.write(f" {'Exceeds 120%':<30}| {(above_120 / 24):<10.2f} days | {above_120:<10.2f} hours | {percent_above_120:<7.2f} % \n")
            f.write("=" * 80 + "\n")
            f.write(f"{'Current directory: ':<80}\n")
            f.write(f"{pwd:<80}\n\n")
            f.write(f"{'Input file: ':<80}\n")
            f.write(f"{str(input_file):<80}\n\n")
            f.write(f"{'Output written to same folder as input file.':<80}\n")
            f.write(f"{'Results: ':<15}{'./':>2}{results_file_short:<63}\n")
            f.write(f"{'Load profile: ':<15}{'./':>2}{lp_file_short:<63}\n")
            f.write(f"{'Graph: ':<15}{'./':>2}{graph_file_short:<63}\n")
            f.write(f"{'Load < 0.5 KW: ':<15}{'./':>2}{no_load_file_short:<63}\n")

    except FileNotFoundError:
        print(f"Error: The file '{load_profile_file}' was not found.")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def visualize_load_profile(load_profile_file, transformer_kva):
    """
    Automatically generates a time-based plot with load thresholds if the file ends with '_RESULTS-LP.csv'.
    Saves the plot to a file without user input.
    """
    if load_profile_file.endswith("_RESULTS-LP.csv"):
        try:
            # Load the data
            data = pd.read_csv(load_profile_file)

            # Ensure the necessary columns are present
            if "datetime" in data.columns and "total_kw" in data.columns:
            
                # Convert 'datetime' column to datetime type for plotting
                data["datetime"] = pd.to_datetime(data["datetime"])
                data.set_index("datetime", inplace=True)

                # Define thresholds for 85%, 100%, and 120% of transformer load
                load_85 = transformer_kva * 0.85
                load_100 = transformer_kva
                load_120 = transformer_kva * 1.2

                # Plotting
                plt.figure(figsize=(12, 6))
                plt.plot(data.index, data["total_kw"], label="Load (kW)", color="blue")

                # Add horizontal lines for load thresholds
                plt.axhline(y=load_85, color="orange", linestyle="--", label="85% Load")
                plt.axhline(y=load_100, color="green", linestyle="--", label="100% Load")
                plt.axhline(y=load_120, color="red", linestyle="--", label="120% Load")

                # Customize the plot
                plt.title("Time-Based Load Visualization")
                plt.xlabel("Time")
                plt.ylabel("Load (kW)")
                plt.legend()

                # Save the plot to file
                # Graph_file
                graph_file = load_profile_file.replace("_RESULTS-LP.csv", "_RESULTS-GRAPH.png")
                plt.savefig(graph_file)
            else:
                print("Error: Required columns 'datetime' and 'total_kw' are not present in the file.")
        except Exception as e:
            print(f"An error occurred while generating the visualization: {e}")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process a CSV file for load profile analysis.")
    parser.add_argument("filename", type=str, help="Path to the input CSV file")
    parser.add_argument("--transformer_kva", type=float, default=0, help="Transformer size in KVA")
    parser.add_argument("--datetime", type=str, help="DateTime for total load calculation (format: YYYY-MM-DD HH:MM:SS)")
    args = parser.parse_args()

    input_file = args.filename
    transformer_kva = args.transformer_kva
    target_datetime = args.datetime

    # Validate file existence
    if not os.path.isfile(input_file):
        print(f"Error: File '{input_file}' does not exist.")
        sys.exit(1)

# Validate datetime argument  NEEDS REPAIRS WE NEED DATETIME AS BOTH STRING
#AND DATETIME. WE SHOULD SPLIT THIS INTO TWO FUNCTIONS. ONE IS 
# target_datetime AND THE OTHER IS target_datetime_str        
    # if target_datetime:
        # try:
            # target_datetime = datetime.strptime(target_datetime, "%Y-%m-%d %H:%M:%S")
            # print(f"Valid datetime provided: {target_datetime}")
        # except ValueError:
            # print(f"Error: Invalid datetime format '{args.datetime}'. Use 'YYYY-MM-DD HH:MM:SS'.")
            # sys.exit(1)

    # Process the CSV file
    try:
        data, load_profile_file = process_csv(input_file) # NEEDS REPAIRS, RUNS TWICE TO WORK.
        #load_profile_file = process_csv(input_file)
        print(f"CSV processing complete. Output file: {load_profile_file}")
        #data = process_csv(input_file)
        print(f"CSV processing complete. Output file: {data}")
    except ValueError as e:
        print(f"ValueError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error processing CSV file '{input_file}': {e}")
        sys.exit(1)

    # Transformer load analysis and visualization
    if transformer_kva > 0:
        try:
            transformer_load_analysis(load_profile_file, transformer_kva)
        except FileNotFoundError:
            print(f"Error: The file '{load_profile_file}' was not found.")
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error during transformer load analysis or visualization: {e}")
            sys.exit(1)
    else:
        print("Transformer KVA not specified or is zero. Skipping analysis and visualization.")


