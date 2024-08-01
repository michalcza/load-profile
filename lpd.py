import pandas as pd
import argparse
import os

def process_csv(input_file):
    try:
        # Read the CSV file
        data = pd.read_csv(input_file)

        # Ensure required columns are present
        required_columns = {'date', 'time', 'kw'}
        if not required_columns.issubset(data.columns):
            raise ValueError(f"Input file must contain the following columns: {', '.join(required_columns)}")

        # Convert the 'date' and 'time' columns to a single datetime column
        data['datetime'] = pd.to_datetime(data['date'] + ' ' + data['time'], errors='coerce')

        # Drop rows where datetime conversion failed
        data = data.dropna(subset=['datetime'])

        # Set the 'datetime' column as the index
        data.set_index('datetime', inplace=True)

        # Ensure 'kw' is numeric
        data['kw'] = pd.to_numeric(data['kw'], errors='coerce')

        # Resample to 15-minute intervals and sum the 'kw' values for each interval
        load_profile = data['kw'].resample('15T').sum()

        # Reset index to get 'datetime' back as a column
        load_profile = load_profile.reset_index()

        # Rename columns for clarity
        load_profile.columns = ['datetime', 'total_kw']

        # Find the datetime for the peak total_kw
        peak_row = load_profile.loc[load_profile['total_kw'].idxmax()]

        # Create a DataFrame to include the peak information
        peak_info = pd.DataFrame({
            'datetime': [peak_row['datetime']],
            'peak_total_kw': [peak_row['total_kw']]
        })

        # Calculate additional factors
        total_kw_sum = load_profile['total_kw'].sum()
        average_load = total_kw_sum / len(load_profile)
        peak_load = peak_row['total_kw']

        # Dynamically calculate individual maximum demands
        individual_maximum_demands = data.groupby(data.index.date)['kw'].max().tolist()
        total_connected_load = sum(individual_maximum_demands)

        # Calculate factors
        diversity_factor = sum(individual_maximum_demands) / peak_load
        load_factor = average_load / peak_load
        coincidence_factor = peak_load / sum(individual_maximum_demands)
        demand_factor = peak_load / total_connected_load

        # Generate output filenames
        base, ext = os.path.splitext(input_file)
        load_profile_file = f"{base}_out.csv"
        peak_info_file = f"{base}_peak.csv"
        factors_file = f"{base}_factors.csv"

        # Save the load profile data to CSV
        load_profile.to_csv(load_profile_file, index=False)

        # Save the peak info data to CSV
        peak_info.to_csv(peak_info_file, index=False)

        # Save the factors to CSV
        factors_data = pd.DataFrame({
            'factor': ['diversity_factor', 'load_factor', 'coincidence_factor', 'demand_factor'],
            'value': [diversity_factor, load_factor, coincidence_factor, demand_factor]
        })
        factors_data.to_csv(factors_file, index=False)

        print(f"Load profile has been created and saved to '{load_profile_file}'.")
        print(f"Peak info has been created and saved to '{peak_info_file}'.")
        print(f"Factors have been calculated and saved to '{factors_file}'.")

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
