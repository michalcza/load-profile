#!/usr/bin/env python3

import pandas as pd
import subprocess
import sys
import re
import argparse
import os
import matplotlib.pyplot as plt
from contextlib import redirect_stdout

def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

clear_screen()

def process_csv(input_file):
    try:
        print(f"=" * 80)
        print(f"{'Data Manipulation':^80}")
        print(f"=" * 80)
        print(f"Processing file: {input_file}")
        
        # Open the file to check the first two lines
        with open(input_file, "r") as file:
            # Read the first line and check if it matches the expected header
            first_line = file.readline().strip()
            expected_header = "meter,date,time,kw"
            if first_line != expected_header:
                raise ValueError(f"Expected header '{expected_header}' but got '{first_line}'")
                sys.exit(1)
            # Read the second line and check if it matches the expected pattern
            second_line = file.readline().strip()
            # Define a regex pattern for the example format
            # Line 1            # meter,date,time,kw
            # Line 2            # 85400796,2024-01-01,00:15:00.000,0.052
            pattern = r"^\d{8},(20[1-9][0-9])-([0-1][0-9])-([0-3][0-9]),([0-2][0-9]):(00|15|30|45):([0-5][0-9]\.\d{3}),\d+\.\d{3}$"
            if not re.match(pattern, second_line):
                raise ValueError(f"Second line '{second_line}' does not match the expected pattern")
                sys.exit(1)

        # Read the CSV file
        data = pd.read_csv(input_file)
        print("CSV file read successfully.")

        # Convert the 'date' and 'time' columns to a single datetime column
        data["datetime"] = pd.to_datetime(
            data["date"] + " " + data["time"], format="%Y-%m-%d %H:%M:%S.%f", errors="coerce"
        )
        # Store the initial row count
        initial_row_count = len(data)
        
        # Drop rows where datetime conversion failed
        data = data.dropna(subset=["datetime"])
        
        # Calculate the number of rows dropped
        rows_dropped = initial_row_count - len(data)
        
        # Print the number of rows dropped
        print(f"Number of rows dropped (datetime): {rows_dropped}")
        
        if rows_dropped > 3:
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
                # Print the number of rows dropped
        print(f"Number of rows dropped (KW): {rows_dropped}")
        
        if rows_dropped > 3:
            raise ValueError("Too many rows dropped due to 'kw' conversion failure. Exiting.")
            sys.exit(1)
        
        # Resample to 15-minute intervals and sum the 'kw' values for each interval
        load_profile = data["kw"].resample("15min").sum()

        # Check if load_profile is empty
        if load_profile.empty:
            raise ValueError("Resampling resulted in an empty DataFrame. Check the input data for validity.")
            sys.exit(1)

        # Reset index to get 'datetime' back as a column
        load_profile = load_profile.reset_index()

        # Rename columns for clarity
        load_profile.columns = ["datetime", "total_kw"]

        # Find the datetime for the peak total_kw
        peak_row = load_profile.loc[load_profile["total_kw"].idxmax()]
        peak_datetime = peak_row["datetime"]
        peak_load = peak_row["total_kw"]

        # Create a DataFrame to include the peak information
        peak_info = pd.DataFrame({"datetime": [peak_datetime], "peak_total_kw": [peak_load]})

        # Calculate average load
        average_load = load_profile["total_kw"].mean()
        average_load_per_meter = data.groupby("meter")["kw"].mean()

        # Calculate number of days and number of meters
        num_days = (data.index.max() - data.index.min()).days + 1

        # Calculate number of meters
        num_meters = data["meter"].nunique()
        
        print(f"=" * 80)
        print(f"{'Calculations and Integrity Checks':^80}")
        print(f"=" * 80)
               
        # Coincidence factor
        individual_maximum_demands = data.groupby("meter")["kw"].max()
        sum_individual_maximum_demands = individual_maximum_demands.sum()
        coincidence_factor = peak_load / sum_individual_maximum_demands
        
        # Verify reasonability
        if coincidence_factor >= 1:
            raise ValueError("Coincidence factor exceeds the reasonability limit of 1.")
        else:
            print("Coincidence factor is within the expected range (<= 1).")

        # Demand factor
        demand_factor = peak_load / sum_individual_maximum_demands
        
        # Verify reasonability
        if demand_factor >= 1:
            raise ValueError("Demand factor exceeds the reasonability limit of 1.")
        else:
            print("Demand Factor is within the expected range (<= 1).")

        # Diversity factor
        diversity_factor = sum_individual_maximum_demands / peak_load
        
        # Verify reasonability
        if diversity_factor <= 1:
            raise ValueError("Diversity factor exceeds the reasonability limit of 1.")
        else:
            print("Diversity factor is within the expected range (>= 1).")

        # Load factor
        load_factor = average_load / peak_load
        # Verify reasonability
        if load_factor >= 1:
            raise ValueError("Load factor exceeds the reasonability limit of 1.")
        else:
            print("Load factor is within the expected range (<= 1).")

        # Cross-check that coincidence_factor == 1 / diversity_factor
        if coincidence_factor != 1 / diversity_factor:
            raise ValueError("Inconsistency detected: coincidence factor is not equal to 1 / diversity factor.")
        else:
            print("Cross-check passed: coincidence factor equals 1 / diversity_factor.")

        # Average peak load for each meter
        average_peak_load_per_meter = sum_individual_maximum_demands / num_meters
        
        # Generate output filenames
        base, ext = os.path.splitext(input_file)
        load_profile_file = f"{base}_out.csv"

        # Construct the full output filename
        output_file = f"{base}_all_outputs.txt"

        def print_and_save(summary, filename=output_file):
            with open(filename, "w") as file:
                # Redirect output to both the console and the file
                with redirect_stdout(sys.stdout):  # Send to console
                    print(summary)  # Print to console
                with redirect_stdout(file):  # Send to file
                    print(summary)  # Print to file

        calculation_summary_width = 80
        calculation_summary_lines = [
            "=" * calculation_summary_width,
            f"{'Results':^{calculation_summary_width}}",
            "=" * calculation_summary_width,
            f"{'Average Load: ':<30} {average_load:>20.2f} {'KW':<30}",
            f"{'Average Load per Meter: ':<30} {average_load_per_meter.mean():>20.2f} {'KW':<30}",
            f"{'Peak Load: ':<30} {peak_load:>20.2f} {'KW on ' + str(peak_datetime):<30}",
            f"{'Average Peak per Meter: ':<30} {average_peak_load_per_meter:>20.2f} {'KW':<30}",
            "=" * calculation_summary_width,
            f"{'Calculated Factors':^{calculation_summary_width}}",
            "=" * calculation_summary_width,
            f"{'Load Factor: ':<25} {load_factor:>20.2f}",
            f"{'Diversity Factor: ':<25} {diversity_factor:>20.2f}",
            f"{'Coincidence Factor: ':<25} {coincidence_factor:>20.2f}",
            f"{'Demand Factor: ':<25} {demand_factor:>20.2f}",
            "=" * calculation_summary_width,
            f"{'Interpretation of Results':^{calculation_summary_width}}",
            "=" * calculation_summary_width,
            "Load Factor:",
            f"{'':<5}= average_load / peak_load",
            f"{'':<5}With constant load, LF -> 1",
            f"{'':<5}With variable load, LF -> 0",
            f"{'':<5}With LF -> 1, fixed costs are spread over more kWh of output.",
            f"{'':<5}LF how efficiently the customer is using peak demand.",
            f"{'':<5}Example: Traffic light service LF ~ 1",
            f"{'':<5}         Electric car charging station LF ~ 0",
            f"{'':<5} ",
            "Diversity Factor:",
            f"{'':<5}= sum_individual_maximum_demands / peak_load",
            f"{'':<5}{diversity_factor:.2f}% of meters peaked at {average_peak_load_per_meter:.2f} (average KW)",
            f"{'':<5}at the same time the system peaked at {peak_load:.2f} KW.",
            f"{'':<5}",
            "Coincidence Factor:",
            f"{'':<5}= peak_load / sum_individual_maximum_demands",
            f"{'':<5}1 / coincidence_factor = diversity_factor",
            f"{'':<5}CF will naturally decrease as number of meters increases.",
            f"{'':<5}",
            "Demand Factor:",
            f"{'':<5}= peak_load / sum_individual_maximum_demands",
            f"{'':<5}Low demand factor requires less system capacity to serve total load.",
            f"{'':<5}Example: Branch circuits in panel can exceed main breaker amps.",
            f"{'':<5}",
            "=" * calculation_summary_width,
        ]
        calculation_summary_box = "\n".join(calculation_summary_lines)

        # Call print and save function
        print_and_save(calculation_summary_box)

        # Profile data to CSV
        load_profile.to_csv(load_profile_file, index=False)
        print(f"Load profile saved to:")
        print(f"{load_profile_file}")
        print(f"="*80)
        # Return the load_profile_file path for use outside the function
        return load_profile_file

    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

def transformer_load_analysis(load_profile_file, transformer_kva):
    try:
        print(f"")
        print(f"")
        print(f"Starting transformer load analysis on file:")
        print(f"{load_profile_file}\nusing transformer size {transformer_kva} KVA")

        # Load the load profile data from CSV file
        out_data = pd.read_csv(load_profile_file)

        # Ensure the 'total_kw' column exists in the data
        if "total_kw" not in out_data.columns:
            raise ValueError("The load profile file must contain a 'total_kw' column representing load in KW.")

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

        print(f"")
        print(f"Total time of dataset: {total_days:.2f} days ({total_hours:.2f} hours)")

        # Determine time spent within different load ranges
        # Get time interval in hours
        time_interval = (out_data["datetime"].iloc[1] - out_data["datetime"].iloc[0]).total_seconds() / 3600

        # Calculate time spent in each load range in hours
        below_85 = len(out_data[out_data["load_percentage"] < 85]) * time_interval
        between_85_100 = (
            len(out_data[(out_data["load_percentage"] >= 85) & (out_data["load_percentage"] < 100)]) * time_interval
        )
        between_100_120 = (
            len(out_data[(out_data["load_percentage"] >= 100) & (out_data["load_percentage"] < 120)]) * time_interval
        )
        above_120 = len(out_data[out_data["load_percentage"] >= 120]) * time_interval

        # Calculate percentages based on total hours
        total_hours = (out_data["datetime"].max() - out_data["datetime"].min()).total_seconds() / 3600
        percent_below_85 = (below_85 / total_hours) * 100
        percent_between_85_100 = (between_85_100 / total_hours) * 100
        percent_between_100_120 = (between_100_120 / total_hours) * 100
        percent_above_120 = (above_120 / total_hours) * 100

        # Display results and print to output file
        # Remove the .csv extension
        base_name = os.path.splitext(input_file)[0]
        load_distribution_output_file = f"{base_name}_all_outputs.txt"
        with open(load_distribution_output_file, "a") as f:
            print("=" * 80)
            f.write("" * 80 + "\n")
            f.write("=" * 80 + "\n")
            print(f"{'Transformer Capacity Distribution':^80}")
            f.write(f"{'Transformer Capacity Distribution':^80}\n")
            print("=" * 80)
            f.write("=" * 80 + "\n")
            print(f" {'LOAD RANGE':^30}| {'DAYS':^16}| {'HOURS':^17}| {'%':^10}")
            f.write(f" {'LOAD RANGE':^30}| {'DAYS':^16}| {'HOURS':^17}| {'%':^10}\n")
            print("-" * 80)
            f.write("-" * 80 + "\n")
            print(
                f" {'Below 85%':<30}| {(below_85 / 24):<10.2f} days | {below_85:<10.2f} hours | {percent_below_85:<7.2f} % "
            )
            f.write(
                f" {'Below 85%':<30}| {(below_85 / 24):<10.2f} days | {below_85:<10.2f} hours | {percent_below_85:<7.2f} % \n"
            )
            print(
                f" {'Between 85% and 100%':<30}| {(between_85_100 / 24):<10.2f} days | {between_85_100:<10.2f} hours | {percent_between_85_100:<7.2f} % "
            )
            f.write(
                f" {'Between 85% and 100%':<30}| {(between_85_100 / 24):<10.2f} days | {between_85_100:<10.2f} hours | {percent_between_85_100:<7.2f} % \n"
            )
            print(
                f" {'Between 100% and 120%':<30}| {(between_100_120 / 24):<10.2f} days | {between_100_120:<10.2f} hours | {percent_between_100_120:<7.2f} % "
            )
            f.write(
                f" {'Between 100% and 120%':<30}| {(between_100_120 / 24):<10.2f} days | {between_100_120:<10.2f} hours | {percent_between_100_120:<7.2f} % \n"
            )
            print(
                f" {'Exceeds 120%':<30}| {(above_120 / 24):<10.2f} days | {above_120:<10.2f} hours | {percent_above_120:<7.2f} % "
            )
            f.write(
                f" {'Exceeds 120%':<30}| {(above_120 / 24):<10.2f} days | {above_120:<10.2f} hours | {percent_above_120:<7.2f} % \n"
            )
            print("=" * 80)
            f.write("=" * 80 + "\n")
            # Confirm that the table has been saved
            print(f"Output table appended to '{load_distribution_output_file}'")

    except FileNotFoundError:
        print(f"Error: The file '{load_profile_file}' was not found.")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def visualize_load_profile(load_profile_file, transformer_kva):
    """
    Automatically generates a time-based plot with load thresholds if the file ends with '_out.csv'.
    Saves the plot to a file without user input.
    """
    if load_profile_file.endswith("_out.csv"):
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
                graph_file = load_profile_file.replace("_out.csv", "_visualization.png")
                plt.savefig(graph_file)
                print(f"Graph saved to '{graph_file}'")
            else:
                print("Error: Required columns 'datetime' and 'total_kw' are not present in the file.")
        except Exception as e:
            print(f"An error occurred while generating the visualization: {e}")

if __name__ == "__main__":
    # Assume process_csv, transformer_load_analysis, and visualize_load_profile are defined elsewhere
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process a CSV file with date, time, and kw columns and perform transformer load analysis.")
    parser.add_argument("filename", type=str, help="Path to the input CSV file")
    parser.add_argument("--transformer_kva", type=float, default=0, help="Transformer size in KVA for load analysis (default is 0)")
    args = parser.parse_args()

    # Process the CSV file and capture the output file name
    input_file = args.filename
    transformer_kva = args.transformer_kva
    load_profile_file = process_csv(input_file)

    # Ensure the file was created successfully
    if load_profile_file and os.path.isfile(load_profile_file):
        # Perform transformer load analysis only if transformer_kva is greater than 0
        if transformer_kva > 0:
            transformer_load_analysis(load_profile_file, transformer_kva)
            visualize_load_profile(load_profile_file, transformer_kva)
        else:
            print("Transformer KVA not specified or is zero. Skipping transformer load analysis and visualization.")
    else:
        print(f"Error: The file '{load_profile_file}' was not created or found.")
        sys.exit(1)


