import requests
import datetime
import pandas as pd
import sys
import os
from config import OPENWEATHER_API_KEY  # Import API key from config.py

# Constants
API_BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
GEOCODING_API_URL = "http://api.openweathermap.org/geo/1.0/zip"

"""test api
https://api.openweathermap.org/geo/1.0/zip?zip=84660,us&appid=API_KEY

84660 = 40.114956,-111.654922
"""

def get_lat_lon_from_zip(zip_code):
    """Get latitude and longitude from ZIP code using OpenWeatherMap API."""
    try:
        response = requests.get(
            GEOCODING_API_URL,
            params={"zip": f"{zip_code},us", "appid": OPENWEATHER_API_KEY},
            timeout=5,  # API timout (sec)
        )
        response.raise_for_status()
        data = response.json()

        if "lat" in data and "lon" in data:
            return data["lat"], data["lon"]
        else:
            print(f"Error: Could not fetch latitude and longitude for ZIP code {zip_code}.")
            return None, None
    except requests.Timeout:
        print("Error: Request timed out while fetching latitude and longitude. Skipping...")
        return None, None
    except requests.RequestException as e:
        print(f"An error occurred while fetching lat/lon: {e}")
        return None, None

def fetch_weather_for_date_range(lat, lon, start_date, end_date):
    """Fetch weather data for a date range using Open-Meteo."""
    try:
        if not lat or not lon:
            print("Error: Latitude and Longitude are required for fetching weather data.")
            return pd.DataFrame()

        if not isinstance(start_date, datetime.date) or not isinstance(end_date, datetime.date):
            print("Error: Start and End dates must be valid date objects.")
            return pd.DataFrame()

        if start_date > end_date:
            print("Error: Start date must be before or equal to the end date.")
            return pd.DataFrame()

        url = (
            f"{API_BASE_URL}?"
            f"latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}"
            f"&hourly=temperature_2m,precipitation,cloudcover,sunshine_duration,weathercode"
            f"&temperature_unit=fahrenheit&precipitation_unit=inch"
        )

        #print(f"Fetching weather data from {start_date} to {end_date}...")
        try:
            response = requests.get(url, timeout=10)  # TIMEOUT
            response.raise_for_status()
        except requests.Timeout:
            print("Error: Request timed out while fetching weather data. Proceeding without data...")
            return pd.DataFrame()

        data = response.json()

        hourly_data = data.get("hourly", {})

        if not hourly_data:
            print("Error: No hourly data available in the response.")
            return pd.DataFrame()

        # Extract hourly data
        times = hourly_data.get("time", [])
        temperatures = hourly_data.get("temperature_2m", [])
        precipitations = hourly_data.get("precipitation", [])
        cloud_covers = hourly_data.get("cloudcover", [])
        sunshine_durations = hourly_data.get("sunshine_duration", [])
        weather_codes = hourly_data.get("weathercode", [])

        # Combine data
        all_weather_data = []
        for hour, temp, precip, cloud, sunshine, weather_code in zip(
            times, temperatures, precipitations, cloud_covers, sunshine_durations, weather_codes
        ):
            all_weather_data.append({
                "datetime": hour,
                "temperature_f": temp,
                "precipitation_in": precip,
                "cloud_cover_percent": cloud,
                "sunshine_duration_sec": sunshine,
                "weather_code": weather_code,
            })

        return pd.DataFrame(all_weather_data)

    except requests.RequestException as e:
        print(f"An error occurred while fetching weather data: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return pd.DataFrame()


def main():
    """Main script to fetch and save weather data."""
    if len(sys.argv) != 4:
        print("Usage: python lpd-weather.py <ZIP code> <start_date: YYYY-MM-DD> <end_date: YYYY-MM-DD>")
        return

    zip_code = sys.argv[1]
    start_date_str = sys.argv[2]
    end_date_str = sys.argv[3]

    try:
        if not zip_code.isdigit():
            print("Error: ZIP code must be a valid 5 digit integer.")
            return

        # Parse dates
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()

        if start_date > end_date:
            print("Error: Start date must be before or equal to end date.")
            return

        # Get latitude and longitude
        lat, lon = get_lat_lon_from_zip(zip_code)
        if lat is None or lon is None:
            print("Unable to fetch weather data without valid latitude and longitude. Check internet connection.")
            return

        # Fetch weather data for the date range
        weather_data = fetch_weather_for_date_range(lat, lon, start_date, end_date)
        if not weather_data.empty:
            # Read the content of arguments.txt
            with open('arguments.txt', 'r') as file:
                # Read the first line, which contains the file path
                #print("DEBUG: Read the first line, which contains the file path")
                line = file.readline().strip()

            # Extract the CSV file path (the part in quotes before any arguments)
            #print("DEBUG: Extract the CSV file path")
            csv_path = line.split('"')[1]

            # Extract the file name and extension
            #print("DEBUG: Extract the file name and extension")
            csv_filename = os.path.basename(csv_path)

            # Split the filename and extension
            #print("DEBUG: Split the filename and extension")
            base_name, ext = os.path.splitext(csv_filename)
            
            # Create the new output file name
            #print("DEBUG: Create the new output file name")
            output_file = f"../sample-data/{base_name}_WEATHER.csv"

            #print(f"Updated output file: {output_file}")

            weather_data.to_csv(output_file, index=False)
            #print(f"Weather data saved to '{output_file}'.")
        else:
            print("No weather data fetched. Check internet connection or API limits.")

    except ValueError as ve:
        print(f"Invalid date format: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
