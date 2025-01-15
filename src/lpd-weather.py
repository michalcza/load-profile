import requests
import datetime
import pandas as pd
import sys
from config import OPENWEATHER_API_KEY #Import API key from config.py

# Usage
"""
Will load weather data 
>python weather.py 84660 2024-01-01 2024-12-31
"""

"""
- Run GUI
- GUI writes to arguments.txt
"C:/Users/micha/GitHub/load-profile/wellsfargo/LP_comma_head_202501091050_TR6919.csv" --transformer_kva 75 --datetime "2024-10-10 16:45:00"
- Read filename [LP_comma_head_202501091050_TR6919_]RESULTS-LP.csv (inside first set of quotes)
- Read min, max datetime of RESULTS-LP.csv (including hours)
    weather_data = fetch_weather_for_date_range(lat, lon, start_date, end_date, start_hour=8, end_hour=18)
    create variables start_date, end_date, start_hour=8, end_hour=18
    

"""

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
        )
        response.raise_for_status()
        data = response.json()

        if "lat" in data and "lon" in data:
            return data["lat"], data["lon"]
        else:
            print(f"Error: Could not fetch latitude and longitude for ZIP code {zip_code}.")
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

        print(f"Fetching weather data from {start_date} to {end_date}...")
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        # Debugging line
        # print("API Response:", data)

        hourly_data = data.get("hourly", {})
        daily_data = data.get("daily", {})

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
        print("Usage: python script.py <ZIP code> <start_date: YYYY-MM-DD> <end_date: YYYY-MM-DD>")
        return

    zip_code = sys.argv[1]
    start_date_str = sys.argv[2]
    end_date_str = sys.argv[3]

    try:
        if not zip_code.isdigit():
            print("Error: ZIP code must be a valid number.")
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
            print("Unable to fetch weather data without valid latitude and longitude.")
            return

        # Fetch weather data for the date range
        weather_data = fetch_weather_for_date_range(lat, lon, start_date, end_date)
        if not weather_data.empty:
            output_file = f"weather-data_{zip_code}_{start_date}_{end_date}.csv"
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

# WMO Weather Codes (ww codes) Reference
# 0 - 3: General cloud conditions
#  0: Clear sky
#  1: Mainly clear (1/8 - 2/8 cloud cover)
#  2: Partly cloudy (3/8 - 4/8 cloud cover)
#  3: Overcast (5/8 - 8/8 cloud cover)

# 45 - 49: Fog or mist
# 45: Fog in patches
# 48: Fog depositing rime; visibility improving
# 49: Fog depositing rime; visibility not changing or deteriorating

# 50 - 59: Drizzle
# 50: Light drizzle, not freezing
# 51: Moderate drizzle, not freezing
# 52: Dense drizzle, not freezing
# 53: Light drizzle, freezing
# 54: Moderate drizzle, freezing
# 55: Dense drizzle, freezing
# 56: Light drizzle and rain, mixed
# 57: Moderate or heavy drizzle and rain, mixed
# 58: Drizzle and snow, light or moderate
# 59: Drizzle and snow, heavy

# 60 - 69: Rain
# 60: Slight rain, intermittent
# 61: Slight rain, continuous
# 62: Moderate rain, intermittent
# 63: Moderate rain, continuous
# 64: Heavy rain, intermittent
# 65: Heavy rain, continuous
# 66: Rain with slight freezing
# 67: Rain with heavy freezing
# 68: Rain and snow mixed, light or moderate
# 69: Rain and snow mixed, heavy

# 70 - 79: Snowfall
# 70: Slight snowfall, intermittent
# 71: Slight snowfall, continuous
# 72: Moderate snowfall, intermittent
# 73: Moderate snowfall, continuous
# 74: Heavy snowfall, intermittent
# 75: Heavy snowfall, continuous
# 76: Ice pellets or snow grains
# 77: Snow showers, light to moderate
# 78: Snow showers, heavy
# 79: Snowfall associated with thunder

# 80 - 84: Showers
# 80: Rain showers, slight
# 81: Rain showers, moderate
# 82: Rain showers, heavy
# 83: Showers of rain and snow, light
# 84: Showers of rain and snow, heavy
# 85 - 86: Snow showers
# 85: Snow showers, slight
# 86: Snow showers, heavy

# 95 - 99: Thunderstorms
# 95: Thunderstorm, slight or moderate
# 96: Thunderstorm with slight hail
# 97: Thunderstorm with heavy hail
# 98: Thunderstorm, severe (possibly with tornado)
# 99: Thunderstorm, violent (with hail or tornado)
