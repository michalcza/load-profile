#!/usr/bin/env python3

import pandas as pd
import subprocess
import sys
import re
import argparse
import os

def clear_screen():
    if os.name == 'nt':
       os.system('cls')
    else:
        os.system('clear')
clear_screen()

while True:
    try:
        # Prompt the user for input
        input_value = input(
            """Please enter the scale factor to use to estimate total system load.
            Commercial load  [1.1 - 1.2]
            Residential load [1.2 - 1.3]
            Lighting load    [1.5 - 2.0]
            (Press Enter to use default value 1.2): """
        )
        # Check if input is empty and assign default value if so
        if input_value.strip() == "":
            scale_factor = 1.2  # Set default value
        else:
            scale_factor = float(input_value)  # Convert to float if input is provided
        if 1.0 <= scale_factor <= 2.0: # Check if the scale factor is within the valid range
            break  # Exit the loop if valid
        else:
            print("Invalid input. Please enter a number between 1.0 and 2.0.")
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        print(f"Scale factor accepted: {scale_factor}")
        
def process_csv(input_file):
    try:
        print(f"Processing file: {input_file}")
        
        # Open the file to check the first two lines
        with open(input_file, 'r') as file:
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
        data['datetime'] = pd.to_datetime(data['date'] + ' ' + data['time'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')

        # Drop rows where datetime conversion failed
        data = data.dropna(subset=['datetime'])

        # Set the 'datetime' column as the index
        data.set_index('datetime', inplace=True)

        # Ensure 'kw' is numeric
        data['kw'] = pd.to_numeric(data['kw'], errors='coerce')

        # Drop rows where 'kw' conversion failed
        data = data.dropna(subset=['kw'])

        # Resample to 15-minute intervals and sum the 'kw' values for each interval
        load_profile = data['kw'].resample('15min').sum()

        # Check if load_profile is empty
        if load_profile.empty:
            raise ValueError("Resampling resulted in an empty DataFrame. Check the input data for validity.")
            sys.exit(1)
            
        # Reset index to get 'datetime' back as a column
        load_profile = load_profile.reset_index()

        # Rename columns for clarity
        load_profile.columns = ['datetime', 'total_kw']

        # Find the datetime for the peak total_kw
        peak_row = load_profile.loc[load_profile['total_kw'].idxmax()]
        peak_datetime = peak_row['datetime']
        peak_load = peak_row['total_kw']

        # Create a DataFrame to include the peak information
        peak_info = pd.DataFrame({
            'datetime': [peak_datetime],
            'peak_total_kw': [peak_load]})
        
        # Calculate average load
        average_load = load_profile['total_kw'].mean()
        average_load_per_meter = data.groupby('meter')['kw'].mean()

        total_connected_load_estimated = peak_load * scale_factor

        # Demand factor
        max_load_per_meter = data.groupby('meter')['kw'].max()
        total_connected_load_corrected = max_load_per_meter.sum()
        demand_factor = peak_load / total_connected_load_corrected

        # Coincidence factor
        individual_maximum_demands = data.groupby('meter')['kw'].max()
        sum_individual_maximum_demands = individual_maximum_demands.sum()
        coincidence_factor = peak_load / total_connected_load_estimated

        # Calculate number of days and number of meters
        num_days = (data.index.max() - data.index.min()).days + 1
        num_meters = data.index.get_level_values(0).nunique()

        # Calculate individual maximum demands
        individual_maximum_demands_array = data.groupby(data.index.date)['kw'].max().tolist()
        total_connected_load = sum(individual_maximum_demands_array)

        # Diversity factor
        diversity_factor = sum(individual_maximum_demands_array) / peak_load
        load_factor = average_load / peak_load

        # Generate output filenames
        base, ext = os.path.splitext(input_file)
        load_profile_file = f"{base}_out.csv"
        peak_info_file = f"{base}_peak.csv"
        factors_file = f"{base}_factors.csv"
        
        # Print calculated variables
        calculation_summary_width = 120
        calculation_summary_lines = [
            "=" * calculation_summary_width,
            f"{'Calculations and Results':^{calculation_summary_width}}",
            "=" * calculation_summary_width,
            f"{'Average Load:':<30} {average_load:>20.2f} {'KW':<30}",
            f"{'Average Load per Meter:':<30} {average_load_per_meter.mean():>20.2f} {'KW':<30}",
            f"{'>>>> Peak Load: <<<<':<30} {peak_load:>20.2f} {'KW on ' + str(peak_datetime):<30}",
            f"{'Estimated Total Connected Load:':<30} {total_connected_load_estimated:>20.2f} {'KW using scale factor: ' + str(scale_factor):<30}",
            "" * calculation_summary_width,
        ]
        calculation_summary_box = "\n".join(calculation_summary_lines)
        print(calculation_summary_box)

        # Print summary of results in a second summary box
        summary_results_width = 120
        summary_results_lines = [
            "=" * summary_results_width,
            f"{'Calculated Factors':^{summary_results_width}}",
            "=" * summary_results_width,
            # DIVERSITY FACTOR >=1 (MORE THAN 1).
            f"{'Diversity Factor:':<20} {diversity_factor:>20.2f} {'= sum(individual_maximum_demands) / peak_load':<30}",
            f"{'':<44}{'Must be >=1 (more than 1)':<30}",
            f"{'':<44}{'Reciprocal if Coincidence Factor':<30}",
            f"{'':<44}{'2.23 means that a meter operates at peak load 2.23% of the time.':<30}",
            f"{''}",
            # LOAD FACTOR <=1 (LESS THAN 1)
            f"{'Load Factor:':<20} {load_factor:>20.2f} {'= average_load / peak_load':<30}",
            f"{'':<44}{'Must be <=1 (less than 1)':<30}",
            f"{'':<44}{'Constant load LF =1':<30}",
            f"{'':<44}{'Varying load LF = 0':<30}",
            f"{'':<44}{'High LF = fixed costs are spread over more kWh of output.':<30}",
            f"{'':<44}{'Indicates how efficiently the customer is using peak demand.':<30}",
            f"{''}",
            # COINCIDENCE FACTOR <=1 (LESS THAN 1)
            # 1/CF = DF 
            f"{'Coincidence Factor:':<20} {coincidence_factor:>20.2f} {'= peak_load / total_connected_load_estimated':<30}",
            f"{'':<44}{'Must be <=1 (less than 1)':<30}",
            f"{'':<44}{'CF will decrease as sample size increases':<30}",
            f"{'':<44}{'Reciprocal of Diversity Factor':<30}",
            f"{''}",
            # DEMAND FACTOR <=1 (LESS THAN 1)            
            f"{'Demand Factor:':<20} {demand_factor:>20.2f} {'= peak_load / total_connected_load':<30}",
            f"{'':<44}{'Must be <=1 (less than 1)':<30}",
            f"{'':<44}{'Low demand factor requires less system capacity to serve total load.':<30}",
            f"{'':<44}{'DF is why sum of branch circuits in panel can exceed main breaker amps':<30}",
            f"{''}",
            "=" * summary_results_width,
        ]
        summary_results_box = "\n".join(summary_results_lines)
        print(summary_results_box)

        # Profile data to CSV
        load_profile.to_csv(load_profile_file, index=False)
        print(f"Load profile saved to '{load_profile_file}'.")

        # Peak info data to CSV
        peak_info.to_csv(peak_info_file, index=False)
        print(f"Peak info saved to '{peak_info_file}'.")

        # Factors to CSV
        factors_data = pd.DataFrame({
            'factor': ['diversity_factor', 'load_factor', 'coincidence_factor', 'demand_factor'],
            'value': [diversity_factor, load_factor, coincidence_factor, demand_factor]
        })
        factors_data.to_csv(factors_file, index=False)
        print(f"Factors saved to '{factors_file}'.")
        
        return load_profile_file # Return the load_profile_file path for use outside the function

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
        print(f"Starting transformer load analysis on file: {load_profile_file} with transformer size {transformer_kva} KVA")

        # Load the load profile data from the specified CSV file
        out_data = pd.read_csv(load_profile_file)
        # Print the first few rows for verification
        # print("Data loaded for analysis:", out_data.head())

        # Ensure the 'total_kw' column exists in the data
        if 'total_kw' not in out_data.columns:
            raise ValueError("The load profile file must contain a 'total_kw' column representing load in KW.")

        # Calculate load as a percentage of transformer capacity
        out_data['load_percentage'] = (out_data['total_kw'] / transformer_kva) * 100

        # Calculate time (count of entries) and percentages for specified ranges
        total_entries = len(out_data)

        # Determine time spent within different load ranges
        above_85_100 = len(out_data[(out_data['load_percentage'] >= 85) & (out_data['load_percentage'] < 100)])
        above_100_120 = len(out_data[(out_data['load_percentage'] >= 100) & (out_data['load_percentage'] < 120)])
        above_120 = len(out_data[out_data['load_percentage'] >= 120])

        # Display results
        print(f"Percentage of time load is between 85% and 100% of transformer capacity: {(above_85_100 / total_entries) * 100:.2f}%")
        print(f"Percentage of time load is between 100% and 120% of transformer capacity: {(above_100_120 / total_entries) * 100:.2f}%")
        print(f"Percentage of time load exceeds 120% of transformer capacity: {(above_120 / total_entries) * 100:.2f}%")

    except FileNotFoundError:
        print(f"Error: The file '{load_profile_file}' was not found.")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Process a CSV file with date, time, and kw columns.')
    parser.add_argument('filename', type=str, help='Path to the input CSV file')
    args = parser.parse_args()
    input_file = args.filename
    # Process the CSV file and capture the output file name
    load_profile_file = process_csv(input_file)

    # Ensure the file was created successfully
    if load_profile_file and os.path.isfile(load_profile_file):
        # Ask if the user wants to continue with transformer load analysis
        while True:
            transformer_choice = input("Would you like to continue with transformer load analysis? (Y/N): ").strip().lower()
            if transformer_choice in ['n', 'no']:
                print("Exiting without transformer load analysis.")
                sys.exit(0)
            elif transformer_choice in ['y', 'yes']:
                # Get transformer KVA from user input
                while True:
                    try:
                        transformer_kva = float(input("Please enter the transformer size in KVA: "))
                        break
                    except ValueError:
                        print("Invalid input. Please enter a numerical value for transformer size.")
                
                # Call the transformer load analysis function
                transformer_load_analysis(load_profile_file, transformer_kva)
                break
            else:
                print("Invalid input. Please type 'Y' or 'N'.")
    else:
        print(f"Error: The file '{load_profile_file}' was not created or found.")
        sys.exit(1)
