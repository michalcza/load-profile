#!/usr/bin/env python3
"""
Weather Fetcher for Load Profile Suite (EXE-friendly, external config/assets)

Key behaviors:
- Reads OPENWEATHER_API_KEY from config.py located NEXT TO the EXE (or next to this .py in dev).
- Uses OpenWeatherMap (ZIP -> lat/lon) and Open-Meteo (historical hourly weather).
- Reads arguments.txt (written by the GUI) to discover the ORIGINAL input CSV file path.
- Writes the output weather CSV (*_WEATHER.csv) in the SAME FOLDER as the input CSV.

Why this design?
- When distributing a single EXE, we still keep config.py, plotly.json, and weather-codes.json
  on disk for easy editing. This file is robust to both dev and frozen-EXE contexts.
"""

from __future__ import annotations

import os
import sys
import requests
import datetime
import pandas as pd
import importlib.util
from typing import Tuple, Optional

# ──────────────────────────────────────────────────────────────────────────────
# Frozen/dev path helpers and config loader
# ──────────────────────────────────────────────────────────────────────────────
def is_frozen() -> bool:
    """True when running as a PyInstaller-frozen executable."""
    return getattr(sys, "frozen", False) is True

def exe_dir() -> str:
    """
    Directory containing the running EXE (frozen) or this source file (dev).
    Use this for files we ship NEXT TO the EXE: config.py, arguments.txt, etc.
    """
    return os.path.dirname(sys.executable) if is_frozen() else os.path.dirname(__file__)

def load_config():
    """
    Import config.py located NEXT TO the EXE (or next to this .py in dev).
    Returns a loaded module object. Raises explicitly if not found.
    """
    cfg_path = os.path.join(exe_dir(), "config.py")
    if not os.path.isfile(cfg_path):
        raise FileNotFoundError(
            f"Missing config.py at {cfg_path}. "
            f"Place a config.py with OPENWEATHER_API_KEY='...' next to the EXE."
        )
    spec = importlib.util.spec_from_file_location("config", cfg_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod

try:
    cfg = load_config()
    OPENWEATHER_API_KEY = getattr(cfg, "OPENWEATHER_API_KEY", "")
    if not OPENWEATHER_API_KEY:
        print("[WARN] OPENWEATHER_API_KEY is empty in config.py.")
except Exception as e:
    print(f"[ERROR] Could not load config.py: {e}")
    OPENWEATHER_API_KEY = ""

# ──────────────────────────────────────────────────────────────────────────────
# API endpoints/constants
# ──────────────────────────────────────────────────────────────────────────────
API_BASE_URL = "https://archive-api.open-meteo.com/v1/archive"     # historical hourly data
GEOCODING_API_URL = "http://api.openweathermap.org/geo/1.0/zip"    # geocoding by ZIP
GEOCODING_TIMEOUT_SEC = 15
GEOCODING_RETRIES = 2

# ──────────────────────────────────────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────────────────────────────────────
def get_lat_lon_from_zip(zip_code: str):
    """Get latitude and longitude from ZIP code using OpenWeatherMap API (with retry)."""
    if not OPENWEATHER_API_KEY:
        print("[WARN] OPENWEATHER_API_KEY is missing/blank in config.py; geocoding will fail.")
    last_err = None
    for attempt in range(1, GEOCODING_RETRIES + 2):  # e.g., 1 try + 2 retries
        try:
            response = requests.get(
                GEOCODING_API_URL,
                params={"zip": f"{zip_code},us", "appid": OPENWEATHER_API_KEY},
                timeout=GEOCODING_TIMEOUT_SEC,
            )
            response.raise_for_status()
            data = response.json()
            if "lat" in data and "lon" in data:
                return data["lat"], data["lon"]
            print(f"Error: Could not fetch latitude/longitude for ZIP {zip_code}. Response: {data}")
            return None, None
        except requests.Timeout as e:
            last_err = e
            print(f"[WARN] Geocoding timeout (attempt {attempt}/{GEOCODING_RETRIES+1})...")
            continue
        except requests.RequestException as e:
            print(f"[ERROR] Geocoding error: {e}")
            return None, None
    print(f"[ERROR] Geocoding failed after retries: {last_err}")
    return None, None
    
def read_base_csv_from_arguments() -> Optional[str]:
    """
    Read the first line of arguments.txt (written by the GUI).
    The first quoted string is the original CSV path the user selected.

    Example line format (written by GUI):
      "C:\path\to\file.csv" --transformer_kva 75 --datetime "2024-08-10 16:45:00"

    Returns:
        Full path to the CSV string (or None if unable to parse).
    """
    args_path = os.path.join(exe_dir(), "arguments.txt")
    if not os.path.isfile(args_path):
        print(f"[WARN] arguments.txt not found at {args_path}")
        return None

    try:
        with open(args_path, "r", encoding="utf-8") as f:
            line = f.readline().strip()
        # CSV path is the first quoted segment
        if '"' in line:
            first_quote = line.find('"')
            second_quote = line.find('"', first_quote + 1)
            if first_quote != -1 and second_quote != -1:
                return line[first_quote + 1 : second_quote]
        print("[WARN] Could not parse CSV path from arguments.txt line.")
        return None
    except Exception as e:
        print(f"[WARN] Failed reading arguments.txt: {e}")
        return None

def output_path_for_weather(csv_path: Optional[str], zip_code: str, start_date: str, end_date: str) -> str:
    """
    Decide where to write the weather CSV:
      - If we know the original CSV path (from arguments.txt), write the output
        next to that CSV, named {base}_WEATHER.csv.
      - Otherwise, write a generic file in the EXE directory as a fallback.
    """
    if csv_path and os.path.isfile(csv_path):
        folder = os.path.dirname(csv_path)
        base = os.path.splitext(os.path.basename(csv_path))[0]
        return os.path.join(folder, f"{base}_WEATHER.csv")
    else:
        print("[WARN] Using fallback weather filename in EXE directory.")
        return os.path.join(exe_dir(), f"weather_{zip_code}_{start_date}_{end_date}.csv")

# ──────────────────────────────────────────────────────────────────────────────
# API calls
# ──────────────────────────────────────────────────────────────────────────────
def get_lat_lon_from_zip(zip_code: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Get latitude/longitude from a US ZIP code via OpenWeatherMap's ZIP geocoder.
    Returns (lat, lon) or (None, None) on error.
    """
    try:
        resp = requests.get(
            GEOCODING_API_URL,
            params={"zip": f"{zip_code},us", "appid": OPENWEATHER_API_KEY},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()

        if "lat" in data and "lon" in data:
            return float(data["lat"]), float(data["lon"])
        print(f"Error: Could not fetch lat/lon for ZIP {zip_code}. Response did not include coordinates.")
        return None, None

    except requests.Timeout:
        print("Error: Geocoding request timed out.")
        return None, None
    except requests.RequestException as e:
        print(f"Error during geocoding: {e}")
        return None, None
    except Exception as e:
        print(f"Unexpected error during geocoding: {e}")
        return None, None

def fetch_weather_for_date_range(
    lat: float, lon: float, start_date: datetime.date, end_date: datetime.date
) -> pd.DataFrame:
    """
    Fetch hourly weather from Open-Meteo for [start_date, end_date].
    Returns a DataFrame with columns:
      datetime, temperature_f, precipitation_in, cloud_cover_percent, sunshine_duration_sec, weather_code
    """
    try:
        if not (lat and lon):
            print("Error: Latitude and Longitude are required for weather data.")
            return pd.DataFrame()

        if start_date > end_date:
            print("Error: Start date must be before or equal to end date.")
            return pd.DataFrame()

        url = (
            f"{API_BASE_URL}?latitude={lat}&longitude={lon}"
            f"&start_date={start_date}&end_date={end_date}"
            f"&hourly=temperature_2m,precipitation,cloudcover,sunshine_duration,weathercode"
            f"&temperature_unit=fahrenheit&precipitation_unit=inch"
        )

        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
        except requests.Timeout:
            print("Error: Weather request timed out.")
            return pd.DataFrame()

        data = resp.json()
        hourly = data.get("hourly", {})
        if not hourly:
            print("Error: No hourly data in response.")
            return pd.DataFrame()

        rows = []
        for t, temp, precip, cloud, sun, code in zip(
            hourly.get("time", []),
            hourly.get("temperature_2m", []),
            hourly.get("precipitation", []),
            hourly.get("cloudcover", []),
            hourly.get("sunshine_duration", []),
            hourly.get("weathercode", []),
        ):
            rows.append(
                {
                    "datetime": t,
                    "temperature_f": temp,
                    "precipitation_in": precip,
                    "cloud_cover_percent": cloud,
                    "sunshine_duration_sec": sun,
                    "weather_code": code,
                }
            )

        return pd.DataFrame(rows)

    except requests.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Unexpected error fetching weather data: {e}")
        return pd.DataFrame()

# ──────────────────────────────────────────────────────────────────────────────
# CLI entrypoint
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    """
    Expected CLI:
        python lpd-weather.py <ZIP> <start: YYYY-MM-DD> <end: YYYY-MM-DD>

    In the GUI pipeline, this is invoked by lpd-gui (embedded run) with dates
    derived from *_RESULTS-LP.csv. We then locate the original CSV via arguments.txt
    and write the weather CSV next to that input CSV.
    """
    if len(sys.argv) != 4:
        print("Usage: python lpd-weather.py <ZIP> <start_date: YYYY-MM-DD> <end_date: YYYY-MM-DD>")
        return

    zip_code, start_date_str, end_date_str = sys.argv[1:4]

    try:
        # Basic input validation
        if not zip_code.isdigit() or len(zip_code) != 5:
            print("Error: ZIP code must be a 5-digit integer (e.g., 84601).")
            return

        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
        if start_date > end_date:
            print("Error: Start date must be before or equal to end date.")
            return

        # Resolve lat/lon
        lat, lon = get_lat_lon_from_zip(zip_code)
        if lat is None or lon is None:
            print("Unable to fetch weather without valid latitude/longitude.")
            return

        # Fetch weather rows
        df = fetch_weather_for_date_range(lat, lon, start_date, end_date)
        if df.empty:
            print("No weather data fetched (empty result).")
            return

        # Figure out where to write the output
        base_csv_path = read_base_csv_from_arguments()
        out_path = output_path_for_weather(base_csv_path, zip_code, start_date_str, end_date_str)

        # Write CSV
        df.to_csv(out_path, index=False)
        print(f"Weather data saved to '{out_path}'")

    except ValueError as ve:
        print(f"Invalid date format: {ve}")
    except Exception as e:
        print(f"Unexpected error: {e}")

print(f"[args] lpd-weather.py received: {sys.argv}")

if __name__ == "__main__":
    main()
