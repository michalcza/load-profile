import requests
import datetime
import pandas as pd
import argparse
from config import API_KEY  # Import API key from config.py

BASE_URL = "https://www.ncei.noaa.gov/cdo-web/api/v2"
"""Generate API token here:
https://www.ncdc.noaa.gov/cdo-web/token
"""
def get_station_for_zip(zip_code):
    """Find the closest weather station for a given ZIP code."""
    try:
        # Use OpenWeatherMap Geocoding API to convert ZIP to lat/lon
        geocoding_url = f"http://api.openweathermap.org/geo/1.0/zip"
        geocoding_params = {"zip": f"{zip_code},us", "appid": "your_openweather_api_key"}  # Replace with your OpenWeatherMap API key
        geocode_response = requests.get(geocoding_url, params=geocoding_params)
        geocode_data = geocode_response.json()

        lat, lon = geocode_data["lat"], geocode_data["lon"]

        # Use NCEI API to find the closest station
        stations_url = f"{BASE_URL}/stations"
        headers = {"token": API_KEY}
        params = {
            "extent": f"{lat - 0.5},{lon - 0.5},{lat + 0.5},{lon + 0.5}",
            "datasetid": "GHCND",
            "limit": 1,
        }
        response = requests.get(stations_url, headers=headers, params=params)
        stations_data = response.json()

        if "results" in stations_data and len(stations_data["results"]) > 0:
            return stations_data["results"][0]["id"]
        else:
            print("No station found near the provided ZIP code.")
            return None
    except Exception as e:
        print(f"Error finding station: {e}")
        return None

def fetch_historical_weather(station_id, start_date, end_date):
    """Fetch historical weather data for a station and date range."""
    try:
        url = f"{BASE_URL}/data"
        headers = {"token": API_KEY}
        params = {
            "datasetid": "GHCND",
            "stationid": station_id,
            "startdate": start_date,
            "enddate": end_date,
            "limit": 1000,
            "units": "standard",
        }

        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        if "results" in data:
            return pd.DataFrame(data["results"])
        else:
            print("No weather data found.")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return pd.DataFrame()

def main():
    """Main script to fetch historical weather data."""
    parser = argparse.ArgumentParser(description="Fetch historical weather data using NOAA's API.")
    parser.add_argument("zip_code", type=str, help="ZIP code for the location.")
    parser.add_argument("start_date", type=str, help="Start date in YYYY-MM-DD format.")
    parser.add_argument("end_date", type=str, help="End date in YYYY-MM-DD format.")

    args = parser.parse_args()

    zip_code = args.zip_code
    start_date = args.start_date
    end_date = args.end_date

    # Get station ID for the ZIP code
    station_id = get_station_for_zip(zip_code)
    if not station_id:
        print("Error: Unable to find a station near the given ZIP code.")
        return

    # Fetch historical weather data
    weather_data = fetch_historical_weather(station_id, start_date, end_date)
    if not weather_data.empty:
        output_file = f"weather_data_{zip_code}_{start_date}_{end_date}.csv"
        weather_data.to_csv(output_file, index=False)
        print(f"Weather data saved to '{output_file}'.")
    else:
        print("No weather data available for the specified range.")

if __name__ == "__main__":
    main()
