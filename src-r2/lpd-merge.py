import os
import sys
import pandas as pd

def process_csv(input_file):
    """Load the load profile CSV file."""
    base, _ = os.path.splitext(input_file)
    load_profile_file = f"{base}_RESULTS-LP.csv"
    data = pd.read_csv(load_profile_file)
    return data, load_profile_file

def process_weather(input_file):
    """Load the weather data CSV file if it exists."""
    base, _ = os.path.splitext(input_file)
    weather_profile_file = f"{base}_WEATHER.csv"

    # Check if the weather file exists before reading
    if not os.path.isfile(weather_profile_file):
        print(f"Warning: Weather data file '{weather_profile_file}' not found. Skipping weather data.")
        return pd.DataFrame(), weather_profile_file

    data = pd.read_csv(weather_profile_file)
    return data, weather_profile_file

if len(sys.argv) < 2:
    print("Usage: python lpd-merge.py <input_csv>")
    sys.exit(1)

# Get input file from arguments
input_file = sys.argv[1]

# Process load profile and weather data
load_profile, load_profile_file = process_csv(input_file)
weather_profile, weather_profile_file = process_weather(input_file)

# Convert 'datetime' to datetime objects for merging
load_profile["datetime"] = pd.to_datetime(load_profile["datetime"])

# Resample weather data to 15-minute intervals using backward fill to preserve initial values
if not weather_profile.empty:
    # Convert 'datetime' column to datetime and set as index
    weather_profile["datetime"] = pd.to_datetime(weather_profile["datetime"], errors="coerce")
    weather_profile.set_index("datetime", inplace=True)

    # Resample to 15-minute intervals and backward fill to avoid losing initial rows
    weather_profile = weather_profile.resample("15min").bfill().ffill().reset_index()

    # Merge load and weather data on 'datetime'
    merged_profile = pd.merge(
        load_profile,
        weather_profile,
        on="datetime",
        how="left"
    )

    # Drop duplicate columns with suffixes
    columns_to_drop = [col for col in merged_profile.columns if col.endswith("_y")]
    merged_profile.drop(columns=columns_to_drop, inplace=True)

    # Rename remaining columns to remove '_x' suffix
    merged_profile.rename(columns=lambda col: col.replace("_x", ""), inplace=True)

    # Save the merged profile by overwriting the original load profile
    merged_profile.to_csv(load_profile_file, index=False)
    print(f"Weather data resampled and merged successfully into '{load_profile_file}'.")

    # Delete the weather file after merging successfully
    try:
        if os.path.exists(weather_profile_file):
            os.remove(weather_profile_file)
            print(f"Deleted temporary weather file: '{weather_profile_file}'")
        else:
            print(f"Warning: Weather file '{weather_profile_file}' not found. Skipping deletion.")
    except Exception as e:
        print(f"Error deleting weather file: {e}")
else:
    # If no weather data, just use the original file
    print(f"No weather data available. Using '{load_profile_file}' as-is for analysis.")
