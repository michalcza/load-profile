import pandas as pd
import argparse
import os
import json

def process_csv(input_file):
    try:
        # Read the CSV file
        data = pd.read_csv(input_file)

        # Ensure required columns are present
        required_columns = {'date', 'time', 'kw'}
        if not required_columns.issubset(data.columns):
            raise ValueError(f"Input file must contain the following columns: {', '.join(required_columns)}")

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

        # Reset index to get 'datetime' back as a column
        load_profile = load_profile.reset_index()

        # Rename columns for clarity
        load_profile.columns = ['datetime', 'total_kw']

        # Find the datetime for the peak total_kw
        peak_row = load_profile.loc[load_profile['total_kw'].idxmax()]
        peak_datetime = peak_row['datetime']
        peak_load = peak_row['total_kw']

        # Calculate additional factors
        average_load = load_profile['total_kw'].mean()
        
        # Calculate number of days and number of meters
        num_days = (data.index.max() - data.index.min()).days + 1
        num_meters = data.index.get_level_values(0).nunique()

        # Dynamically calculate individual maximum demands
        individual_maximum_demands = data.groupby(data.index.date)['kw'].max().tolist()
        total_connected_load = sum(individual_maximum_demands)

        # Calculate factors
        diversity_factor = sum(individual_maximum_demands) / peak_load
        load_factor = average_load / peak_load
        coincidence_factor = peak_load / sum(individual_maximum_demands)
        demand_factor = peak_load / total_connected_load

        # Print results as JSON
        results = {
            "num_days": num_days,
            "num_meters": num_meters,
            "average_load": average_load,
            "peak_load": peak_load,
            "peak_datetime": peak_datetime,
            "diversity_factor": diversity_factor,
            "load_factor": load_factor,
            "coincidence_factor": coincidence_factor,
            "demand_factor": demand_factor
        }
        print(json.dumps(results))

    except FileNotFoundError:
        print(json.dumps({"error": f"The file '{input_file}' was not found."}))
    except ValueError as e:
        print(json.dumps({"error": str(e)}))
    except Exception as e:
        print(json.dumps({"error": f"An unexpected error occurred: {str(e)}"}))

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Process a CSV file with date, time, and kw columns.')
    parser.add_argument('filename', type=str, help='Path to the input CSV file')

    # Parse command-line arguments
    args = parser.parse_args()
    input_file = args.filename

    process_csv(input_file)
