#!/usr/bin/env python3

import pandas as pd
import argparse
import os

def clear_screen():
    # Check if the OS is Windows
    if os.name == 'nt':
        os.system('cls')  # Use 'cls' for Windows
    else:
        os.system('clear')  # Use 'clear' for Mac and Linux
clear_screen()

while True:
    try:
        scale_factor = float(input(
    """Please enter the scale factor to use to estimate total system load.
    Commercial load  [1.1 - 1.2]
    Residential load [1.2 - 1.3]
    Lighting load    [1.5 - 2.0]: """
        ))
        # Check if the scale factor is within the valid range
        if 1.0 <= scale_factor <= 2.0:
            break  # Exit the loop if valid
        else:
            print("Invalid input. Please enter a number between 1.0 and 2.0.")
    
    except ValueError:
        print("Invalid input. Please enter a valid number.")

print(f"Scale factor accepted: {scale_factor}")

def process_csv(input_file):
    try:
        print(f"Processing file: {input_file}")
        
        # Read the CSV file
        data = pd.read_csv(input_file)
        print("CSV file read successfully.")

        # Ensure required columns are present
        required_columns = {'date', 'time', 'kw'}
        if not required_columns.issubset(data.columns):
            raise ValueError(f"Input file must contain the following columns: {', '.join(required_columns)}")

        # Convert the 'date' and 'time' columns to a single datetime column
        data['datetime'] = pd.to_datetime(data['date'] + ' ' + data['time'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')
        #print("Datetime conversion completed.")

        # Drop rows where datetime conversion failed
        data = data.dropna(subset=['datetime'])
        #print("Dropped rows with invalid datetime.")

        # Set the 'datetime' column as the index
        data.set_index('datetime', inplace=True)
        #print("Set 'datetime' as index.")

        # Ensure 'kw' is numeric
        data['kw'] = pd.to_numeric(data['kw'], errors='coerce')
        #print("Converted 'kw' to numeric.")

        # Drop rows where 'kw' conversion failed
        data = data.dropna(subset=['kw'])
        #print("Dropped rows with invalid 'kw'.")

        # Resample to 15-minute intervals and sum the 'kw' values for each interval
        load_profile = data['kw'].resample('15min').sum()
        #print("Resampling completed.")

        # Check if load_profile is empty
        if load_profile.empty:
            raise ValueError("Resampling resulted in an empty DataFrame. Check the input data for validity.")

        # Reset index to get 'datetime' back as a column
        load_profile = load_profile.reset_index()
        #print("Reset index on load profile.")

        # Rename columns for clarity
        load_profile.columns = ['datetime', 'total_kw']
        #print("Renamed columns.")

        # Find the datetime for the peak total_kw
        peak_row = load_profile.loc[load_profile['total_kw'].idxmax()]
        peak_datetime = peak_row['datetime']
        peak_load = peak_row['total_kw']

        # Create a DataFrame to include the peak information
        peak_info = pd.DataFrame({
            'datetime': [peak_datetime],
            'peak_total_kw': [peak_load]})
        #print("Created peak info DataFrame.")
        # Calculate average load
        average_load = load_profile['total_kw'].mean()
        average_load_per_meter = data.groupby('meter')['kw'].mean()
        #scale_factor = 1.5
        #total_connected_load_estimated = average_load_per_meter.sum() * scale_factor
        total_connected_load_estimated = peak_load * scale_factor
# <corrected demand factor>
        max_load_per_meter = data.groupby('meter')['kw'].max()
        total_connected_load_corrected = max_load_per_meter.sum()
        demand_factor = peak_load / total_connected_load_corrected
# </corrected demand factor>
# <corrected coincidence factor>
        individual_maximum_demands = data.groupby('meter')['kw'].max()
        sum_individual_maximum_demands = individual_maximum_demands.sum()
        #individual_maximum_demands = data.groupby('meter')['kw'].max()
        coincidence_factor = peak_load / total_connected_load_estimated
# </corrected coincidence factor>
        # Calculate number of days and number of meters
        num_days = (data.index.max() - data.index.min()).days + 1
        num_meters = data.index.get_level_values(0).nunique()

        # Calculate individual maximum demands
        individual_maximum_demands_array = data.groupby(data.index.date)['kw'].max().tolist()
        total_connected_load = sum(individual_maximum_demands_array)
        #print("Calculated individual maximum demands.")

        # Calculate factors
        diversity_factor = sum(individual_maximum_demands_array) / peak_load
        load_factor = average_load / peak_load
        #print("Calculated factors.")

        # Generate output filenames
        base, ext = os.path.splitext(input_file)
        load_profile_file = f"{base}_out.csv"
        peak_info_file = f"{base}_peak.csv"
        factors_file = f"{base}_factors.csv"
        #print(f"Output filename: {load_profile_file}")
        #print(f"Output filename: {peak_info_file}")
        #print(f"Output filename: {factors_file}")
        # Print calculated variables
        calculation_summary_width = 120
        calculation_summary_lines = [
            "=" * calculation_summary_width,
            f"{'Calculations and Results':^{calculation_summary_width}}",
            "=" * calculation_summary_width,
            #f"{'Number of Days:':<30} {num_days:>20}", # NEEDS VALIDATION
            #f"{'Number of Meters:':<30} {num_meters:>20} {'':<30}", # NEEDS VALIDATION
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


        # Save the load profile data to CSV
        load_profile.to_csv(load_profile_file, index=False)
        print(f"Load profile saved to '{load_profile_file}'.")

        # Save the peak info data to CSV
        peak_info.to_csv(peak_info_file, index=False)
        print(f"Peak info saved to '{peak_info_file}'.")

        # Save the factors to CSV
        factors_data = pd.DataFrame({
            'factor': ['diversity_factor', 'load_factor', 'coincidence_factor', 'demand_factor'],
            'value': [diversity_factor, load_factor, coincidence_factor, demand_factor]
        })
        factors_data.to_csv(factors_file, index=False)
        print(f"Factors saved to '{factors_file}'.")

    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Process a CSV file with date, time, and kw columns.')
    parser.add_argument('filename', type=str, help='Path to the input CSV file')

    # Parse command-line arguments
    args = parser.parse_args()
    input_file = args.filename

    process_csv(input_file)