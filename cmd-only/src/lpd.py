#!/usr/bin/env python3

import pandas as pd
import subprocess
import sys
import re
import argparse
import os
import matplotlib.pyplot as plt

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
 
        # Construct the full output filename
        output_file = f"{base}_all_outputs.txt"
        with open(output_file, 'w') as out_file:
            out_file.write(f"\n")
            out_file.write("=" * 80 + "\n")
            out_file.write(f"{'Load Summary':^80}\n")
            out_file.write("=" * 80 + "\n")
            out_file.write(f"{'Average Load (meter): ':<35} {average_load_per_meter.mean():>16.2f} {'KW':<30}\n")
            out_file.write(f"{'Average Load (dataset): ':<35} {average_load:>16.2f} {'KW':<20}\n")
            out_file.write(f"\n")
            out_file.write("=" * 80 + "\n")
            out_file.write(f"{'Data Summary':^80}\n")
            out_file.write("=" * 80 + "\n")
#sus        #out_file.write(f"{'Number of Meters in Dataset: ':<25} {num_meters:>20.0f}\n")
            out_file.write(f"{'Number of Days (dataset): ':<25} {num_days:>20.0f}\n")
            out_file.write(f"\n")
            out_file.write("=" * 80 + "\n")
            out_file.write(f"{'Peak Load Summary':^80}\n")
            out_file.write("=" * 80 + "\n")
            out_file.write(f"{'Peak Load: ':<35} {peak_load:>16.2f} {'KW on ' + str(peak_datetime):<20}\n")
            out_file.write(f"{'Total Connected Load (Est.): ':<35} {total_connected_load_estimated:>16.2f} {'KW w/ scale factor ' + str(scale_factor):<20}\n")
            out_file.write(f"{'Sum of individual MAX demand (non-coinc.): ':<25} {sum_individual_maximum_demands:>8.2f} {'KW':<20}\n")
#sus        #why is total_connected_load_corrected =  sum_individual_maximum_demands
            #out_file.write(f"{'Total Connected Load: ':<25} {total_connected_load:>20.2f} {'KW':<30}\n")
            #out_file.write(f"{'Total Connected Load: ':<25} {total_connected_load_corrected:>20.2f} {'KW':<30}\n")
            out_file.write(f"\n")
            out_file.write("=" * 80 + "\n")
            out_file.write(f"{'Factors Summary':^80}\n")
            out_file.write("=" * 80 + "\n")
            out_file.write(f"{'Load Factor*: ':<25} {load_factor:>20.2f}\n")
            out_file.write(f"{'Diversity Factor: ':<25} {diversity_factor:>20.2f}\n")
            out_file.write(f"{'Coincidence Factor: ':<25} {coincidence_factor:>20.2f}\n")
            out_file.write(f"{'Demand Factor: ':<25} {demand_factor:>20.2f}\n")
            out_file.write(f"{'* unverified calculations (see docs)':<25}\n")
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
        print(f"")
        print(summary_results_box)

        # Profile data to CSV
        load_profile.to_csv(load_profile_file, index=False)
        print(f"")
        print(f"Load profile saved to '{load_profile_file}'.")

        # Peak info data to CSV
        #peak_info.to_csv(peak_info_file, index=False)
        #print(f"Peak info saved to '{peak_info_file}'.")

        # Factors to CSV
        #factors_data = pd.DataFrame({
        #    'factor': ['diversity_factor', 'load_factor', 'coincidence_factor', 'demand_factor'],
        #    'value': [diversity_factor, load_factor, coincidence_factor, demand_factor]
        #})
        #factors_data.to_csv(factors_file, index=False)
        #print(f"Factors saved to '{factors_file}'.")
        
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
        print(f"")
        print(f"")
        print(f"Starting transformer load analysis on file: {load_profile_file} with transformer size {transformer_kva} KVA")

        # Load the load profile data from the specified CSV file
        out_data = pd.read_csv(load_profile_file)
        # print("Data loaded for analysis:", out_data.head())  # Print the first few rows for verification

        # Ensure the 'total_kw' column exists in the data
        if 'total_kw' not in out_data.columns:
            raise ValueError("The load profile file must contain a 'total_kw' column representing load in KW.")

        # Calculate load as a percentage of transformer capacity
        out_data['load_percentage'] = (out_data['total_kw'] / transformer_kva) * 100

        # Calculate the total hours and days of the dataset
        out_data['datetime'] = pd.to_datetime(out_data['datetime'])  # Convert to datetime if not already
        total_time = (out_data['datetime'].max() - out_data['datetime'].min()).total_seconds()
        total_hours = total_time / 3600  # Convert seconds to hours
        total_days = total_hours / 24  # Convert hours to days

        print(f"")
        print(f"Total time of dataset: {total_days:.2f} days ({total_hours:.2f} hours)")

        # Determine time spent within different load ranges
        time_interval = (out_data['datetime'].iloc[1] - out_data['datetime'].iloc[0]).total_seconds() / 3600  # Get time interval in hours

        # Determine time spent within different load ranges
        time_interval = (out_data['datetime'].iloc[1] - out_data['datetime'].iloc[0]).total_seconds() / 3600  # Get time interval in hours

        # Calculate time spent in each load range in hours
        below_85 = len(out_data[out_data['load_percentage'] < 85]) * time_interval
        between_85_100 = len(out_data[(out_data['load_percentage'] >= 85) & (out_data['load_percentage'] < 100)]) * time_interval
        between_100_120 = len(out_data[(out_data['load_percentage'] >= 100) & (out_data['load_percentage'] < 120)]) * time_interval
        above_120 = len(out_data[out_data['load_percentage'] >= 120]) * time_interval

        # Calculate percentages based on total hours
        total_hours = (out_data['datetime'].max() - out_data['datetime'].min()).total_seconds() / 3600  # Total dataset hours
        percent_below_85 = (below_85 / total_hours) * 100
        percent_between_85_100 = (between_85_100 / total_hours) * 100
        percent_between_100_120 = (between_100_120 / total_hours) * 100
        percent_above_120 = (above_120 / total_hours) * 100

        # Display results and print to output file
        base_name = os.path.splitext(input_file)[0]  # Removes the .csv extension
        load_distribution_output_file = f"{base_name}_all_outputs.txt"
        with open(load_distribution_output_file, "a") as f:
            print("=" * 80)
            f.write("" * 80 + "\n")
            f.write("=" * 80 + "\n")
            print(f"{'Transformer Capacity Distribution':^80}")
            f.write(f"{'Transformer Capacity Distribution':^80}\n")
            print("=" * 80)
            f.write("=" * 80 + "\n")
            print(f" {'LOAD RANGE':^30}| {'DAYS':^16}| {'HOURS':^17}| {'%':^10}|")
            f.write(f" {'LOAD RANGE':^30}| {'DAYS':^16}| {'HOURS':^17}| {'%':^10}\n")
            print("-" * 80)
            f.write("-" * 80 + "\n")
            print(f" {'Below 85%':<30}| {(below_85 / 24):<10.2f} days | {below_85:<10.2f} hours | {percent_below_85:<7.2f} % ")
            f.write(f" {'Below 85%':<30}| {(below_85 / 24):<10.2f} days | {below_85:<10.2f} hours | {percent_below_85:<7.2f} % \n")
            print(f" {'Between 85% and 100%':<30}| {(between_85_100 / 24):<10.2f} days | {between_85_100:<10.2f} hours | {percent_between_85_100:<7.2f} % ")
            f.write(f" {'Between 85% and 100%':<30}| {(between_85_100 / 24):<10.2f} days | {between_85_100:<10.2f} hours | {percent_between_85_100:<7.2f} % \n")
            print(f" {'Between 100% and 120%':<30}| {(between_100_120 / 24):<10.2f} days | {between_100_120:<10.2f} hours | {percent_between_100_120:<7.2f} % ")
            f.write(f" {'Between 100% and 120%':<30}| {(between_100_120 / 24):<10.2f} days | {between_100_120:<10.2f} hours | {percent_between_100_120:<7.2f} % \n")
            print(f" {'Exceeds 120%':<30}| {(above_120 / 24):<10.2f} days | {above_120:<10.2f} hours | {percent_above_120:<7.2f} % ")
            f.write(f" {'Exceeds 120%':<30}| {(above_120 / 24):<10.2f} days | {above_120:<10.2f} hours | {percent_above_120:<7.2f} % \n")
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
    Prompts the user to visualize the load data in a file ending with '_out.csv'.
    If the user agrees, it generates a time-based plot with load thresholds and saves the plot to a file.
    """
    if load_profile_file.endswith("_out.csv"):
        visualize = input("Would you like to visualize the load profile data? (Y/N): ").strip().lower()
        
        if visualize in ['y', 'yes']:
            try:
                # Load the data
                data = pd.read_csv(load_profile_file)
                
                # Ensure the necessary columns are present
                if 'datetime' in data.columns and 'total_kw' in data.columns:
                    # Convert 'datetime' column to datetime type for plotting
                    data['datetime'] = pd.to_datetime(data['datetime'])
                    data.set_index('datetime', inplace=True)

                    # Define thresholds for 85%, 100%, and 120% of transformer load
                    load_85 = transformer_kva * 0.85
                    load_100 = transformer_kva
                    load_120 = transformer_kva * 1.2

                    # Plotting
                    plt.figure(figsize=(12, 6))
                    plt.plot(data.index, data['total_kw'], label="Load (kW)", color="blue")
                    
                    # Add horizontal lines for load thresholds
                    plt.axhline(y=load_85, color='orange', linestyle='--', label="85% Load")
                    plt.axhline(y=load_100, color='green', linestyle='--', label="100% Load")
                    plt.axhline(y=load_120, color='red', linestyle='--', label="120% Load")

                    # Customize the plot
                    plt.title("Time-Based Load Visualization")
                    plt.xlabel("Time")
                    plt.ylabel("Load (kW)")
                    plt.legend()

                    # Save the plot to a file
                    graph_file = load_profile_file.replace("_out.csv", "_visualization.png")
                    plt.savefig(graph_file)
                    print(f"Graph saved to '{graph_file}'")
                else:
                    print("Error: Required columns 'datetime' and 'total_kw' are not present in the file.")
            except Exception as e:
                print(f"An error occurred while generating the visualization: {e}")
        else:
            print("Exiting without visualization.")
            
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
                # Call the transformer load analysis visualization function
                visualize_load_profile(load_profile_file, transformer_kva)
                break
            else:
                print("Invalid input. Please type 'Y' or 'N'.")
    else:
        print(f"Error: The file '{load_profile_file}' was not created or found.")
        sys.exit(1)




