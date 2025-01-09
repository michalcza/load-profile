import requests
import datetime
import pandas as pd
from config import OPENWEATHER_API_KEY #Import API key from config.py

# Constants
API_BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
GEOCODING_API_URL = "http://api.openweathermap.org/geo/1.0/zip"

"""test api
https://api.openweathermap.org/geo/1.0/zip?zip=84660,us&appid=API_KEY
"""
def get_lat_lon_from_zip_census(zip_code):
    """Get latitude and longitude from ZIP code using US Census Geocoding API."""
    try:
        url = f"https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
        response = requests.get(url, params={"address": zip_code, "benchmark": "Public_AR_Current", "format": "json"})
        data = response.json()

        if "result" in data and "addressMatches" in data["result"]:
            matches = data["result"]["addressMatches"]
            if matches:
                coordinates = matches[0]["coordinates"]
                return coordinates["y"], coordinates["x"]  # Latitude, Longitude
        print(f"Error: Could not fetch latitude and longitude for ZIP code {zip_code}.")
        return None, None
    except Exception as e:
        print(f"An error occurred while fetching lat/lon: {e}")
        return None, None

def get_lat_lon_from_zip(zip_code):
    """Get latitude and longitude from ZIP code using OpenWeatherMap API."""
    try:
        response = requests.get(
            GEOCODING_API_URL,
            params={"zip": f"{zip_code},us", "appid": OPENWEATHER_API_KEY},
        )
        data = response.json()

        if "lat" in data and "lon" in data:
            return data["lat"], data["lon"]
        else:
            print(f"Error: Could not fetch latitude and longitude for ZIP code {zip_code}.")
            return None, None
    except Exception as e:
        print(f"An error occurred while fetching lat/lon: {e}")
        return None, None

def fetch_weather_for_date_range(lat, lon, start_date, end_date):
    """Fetch weather data for a date range using Open-Meteo."""
    try:
        current_date = start_date
        all_weather_data = []

        while current_date <= end_date:
            url = (
                f"{API_BASE_URL}?"
                f"latitude={lat}&longitude={lon}&start_date={current_date}&end_date={current_date}&hourly=temperature_2m,relative_humidity_2m"
                f"&temperature_unit=fahrenheit"
            )
            print(f"Fetching weather data for {current_date}...")
            response = requests.get(url)
            data = response.json()

        if "hourly" in data:
            for hour, temp, humidity, wind, pressure, clouds, rain, snow in zip(
                data["hourly"]["time"],
                data["hourly"]["temperature_2m"],
                data["hourly"]["relative_humidity_2m"],
                data["hourly"].get("windspeed_10m", [None] * len(data["hourly"]["time"])),
                data["hourly"].get("surface_pressure", [None] * len(data["hourly"]["time"])),
                data["hourly"].get("cloudcover", [None] * len(data["hourly"]["time"])),
                data["hourly"].get("precipitation", [None] * len(data["hourly"]["time"])),
                data["hourly"].get("snowfall", [None] * len(data["hourly"]["time"])),
            ):
                all_weather_data.append({
                    "datetime": hour,
                    "temperature_f": temp,
                    "humidity_percent": humidity,
                    "wind_speed_mph": wind,
                    "pressure_hpa": pressure,
                    "cloud_cover_percent": clouds,
                    "rain_mm": rain,
                    "snow_mm": snow,
                })
        else:
            print(f"No weather data found for {current_date}.")


            current_date += datetime.timedelta(days=1)

        return pd.DataFrame(all_weather_data)

    except Exception as e:
        print(f"An error occurred while fetching weather data: {e}")
        return pd.DataFrame()

def main():
    """Main script to fetch and save weather data."""
    print("Fetch Weather Data")
    zip_code = input("Enter ZIP code: ")
    start_date_str = input("Enter start date (YYYY-MM-DD): ")
    end_date_str = input("Enter end date (YYYY-MM-DD): ")

    try:
        # Get latitude and longitude
        lat, lon = get_lat_lon_from_zip(zip_code)
        if lat is None or lon is None:
            print("Unable to fetch weather data without valid latitude and longitude.")
            return

        # Parse dates
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()

        if start_date > end_date:
            print("Error: Start date must be before or equal to end date.")
            return

        # Fetch weather data for the date range
        weather_data = fetch_weather_for_date_range(lat, lon, start_date, end_date)
        if not weather_data.empty:
            output_file = f"weather_data_{zip_code}_{start_date}_{end_date}.csv"
            weather_data.to_csv(output_file, index=False)
            print(f"Weather data saved to '{output_file}'.")
        else:
            print("No weather data fetched.")

    except ValueError as ve:
        print(f"Invalid date format: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
