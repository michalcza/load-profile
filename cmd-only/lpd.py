import pandas as pd
import argparse
import os

def process_csv(input_file):
    try:
        print(f"Processing file: {input_file}")
        
        # Read the CSV file
        data = pd.read_csv(input_file)
        print("CSV file read successfully.")
        print(data.head())  # Print the first few rows of the data

        # Ensure required columns are present
        required_columns = {'date', 'time', 'kw'}
        if not required_columns.issubset(data.columns):
            raise ValueError(f"Input file must contain the following columns: {', '.join(required_columns)}")

        # Convert the 'date' and 'time' columns to a single datetime column
        data['datetime'] = pd.to_datetime(data['date'] + ' ' + data['time'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')
        print("Datetime conversion completed.")
        print(data.head())  # Print the first few rows after datetime conversion

        # Drop rows where datetime conversion failed
        data = data.dropna(subset=['datetime'])
        print("Dropped rows with invalid datetime.")
        print(data.head())  # Print the first few rows after dropping invalid datetimes

        # Set the 'datetime' column as the index
        data.set_index('datetime', inplace=True)
        print("Set 'datetime' as index.")
        print(data.head())  # Print the first few rows after setting index

        # Ensure 'kw' is numeric
        data['kw'] = pd.to_numeric(data['kw'], errors='coerce')
        print("Converted 'kw' to numeric.")
        print(data.head())  # Print the first few rows after converting 'kw' to numeric

        # Drop rows where 'kw' conversion failed
        data = data.dropna(subset=['kw'])
        print("Dropped rows with invalid 'kw'.")
        print(data.head())  # Print the first few rows after dropping invalid 'kw'

        # Resample to 15-minute intervals and sum the 'kw' values for each interval
        load_profile = data['kw'].resample('15min').sum()
        print("Resampling completed.")
        print(load_profile.head())  # Print the first few rows of the resampled data

        # Check if load_profile is empty
        if load_profile.empty:
            raise ValueError("Resampling resulted in an empty DataFrame. Check the input data for validity.")

        # Reset index to get 'datetime' back as a column
        load_profile = load_profile.reset_index()
        print("Reset index on load profile.")
        print(load_profile.head())  # Print the first few rows after resetting index

        # Rename columns for clarity
        load_profile.columns = ['datetime', 'total_kw']
        print("Renamed columns.")
        print(load_profile.head())  # Print the first few rows after renaming columns

        # Find the datetime for the peak total_kw
        peak_row = load_profile.loc[load_profile['total_kw'].idxmax()]
        peak_datetime = peak_row['datetime']
        peak_load = peak_row['total_kw']
        print(f"Peak row found: {peak_row}")

        # Create a DataFrame to include the peak information
        peak_info = pd.DataFrame({
            'datetime': [peak_datetime],
            'peak_total_kw': [peak_load]
        })
        print("Created peak info DataFrame.")

        # Calculate additional factors
        average_load = load_profile['total_kw'].mean()
        
        # Calculate number of days and number of meters
        num_days = (data.index.max() - data.index.min()).days + 1
        num_meters = data.index.get_level_values(0).nunique()
        print(f"Number of days: {num_days}")
        print(f"Number of meters: {num_meters}")

        # Dynamically calculate individual maximum demands
        individual_maximum_demands = data.groupby(data.index.date)['kw'].max().tolist()
        total_connected_load = sum(individual_maximum_demands)
        print("Calculated individual maximum demands.")

        # Calculate factors
        diversity_factor = sum(individual_maximum_demands) / peak_load
        load_factor = average_load / peak_load
        coincidence_factor = peak_load / sum(individual_maximum_demands)
        demand_factor = peak_load / total_connected_load
        print("Calculated factors.")

        # Generate output filenames
        base, ext = os.path.splitext(input_file)
        load_profile_file = f"{base}_out.csv"
        peak_info_file = f"{base}_peak.csv"
        factors_file = f"{base}_factors.csv"
        print(f"Output filenames generated: {load_profile_file}, {peak_info_file}, {factors_file}")

        # Print summary of results in a 120 character wide box with placeholders for a third column
        summary_box_width = 120
        summary_lines = [
            f"{'Summary of Results':^{summary_box_width}}",
            "=" * summary_box_width,
            f"{'Number of Days:':<30} {num_days:>20}",
            f"{'Number of Meters:':<30} {num_meters:>20} {'':<30}",
            f"{'Average Load:':<30} {average_load:>20.2f} {'KW':<30}",
            f"{'Peak Load:':<30} {peak_load:>20.2f} {'KW on '}{peak_datetime}",
            f"{'Diversity Factor:':<30} {diversity_factor:>20.2f} {'DF = sum(individual_maximum_demands) / peak_load':<30}",
            f"{'Load Factor:':<30} {load_factor:>20.2f} {'LF = average_load / peak_load':<30}",
            f"{'Coincidence Factor:':<30} {coincidence_factor:>20.2f} {'CF = peak_load / sum(individual_maximum_demands)':<30}",
            f"{'Demand Factor:':<30} {demand_factor:>20.2f} {'DF = peak_load / total_connected_load':<30}",
            "=" * summary_box_width,
        ]
        summary_box = "\n".join(summary_lines)
        print(summary_box)

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
