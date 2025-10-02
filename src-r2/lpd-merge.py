#!/usr/bin/env python3
"""
Merge weather data into the computed load profile result (EXE-friendly)

Behavior:
- Takes an input "base" CSV (the original meter file path the user selected).
- Loads the load profile result at:   {base}_RESULTS-LP.csv
- Loads the weather CSV at:           {base}_WEATHER.csv   (same folder as base)
- Optionally you can override weather path with --weather <file>.
- Resamples weather to 15-minute intervals (bfill then ffill), merges on 'datetime'.
- Writes the merged frame back to      {base}_RESULTS-LP.csv
- Deletes the weather CSV by default after a successful merge (override with --keep-weather).

Why overwrite {base}_RESULTS-LP.csv?
- Your interactive viewer and GUI already expect weather columns to exist in that file.
- Keeping a single canonical file simplifies the downstream pipeline.

Columns expected:
- Load profile file must contain at least: 'datetime' (ISO-like string), 'total_kw' etc.
- Weather file contains: 'datetime', 'temperature_f', 'precipitation_in',
  'cloud_cover_percent', 'sunshine_duration_sec', 'weather_code'
"""

from __future__ import annotations

import os
import sys
import argparse
import pandas as pd


def parse_args() -> argparse.Namespace:
    """
    CLI:
        python lpd-merge.py <input_base_csv> [--weather path] [--keep-weather]

    <input_base_csv> is the ORIGINAL CSV the user selected in the GUI.
    This script will derive:
        load_profile_path = {base}_RESULTS-LP.csv
        default_weather    = {base}_WEATHER.csv   (unless --weather is provided)
    """
    p = argparse.ArgumentParser(description="Merge weather into the computed load profile.")
    p.add_argument(
        "filename",
        help="Path to the ORIGINAL input CSV (not the *_RESULTS-LP.csv). Used to derive sibling files."
    )
    p.add_argument(
        "--weather",
        default=None,
        help="Optional explicit path to a weather CSV to merge instead of the default {base}_WEATHER.csv."
    )
    p.add_argument(
        "--keep-weather",
        action="store_true",
        help="Keep the weather CSV after a successful merge (default is to delete)."
    )
    return p.parse_args()


def derive_paths(input_csv: str, weather_override: str | None) -> tuple[str, str]:
    """
    From the original input CSV, derive:
      - path to the load profile results: {base}_RESULTS-LP.csv
      - path to the weather CSV:          {base}_WEATHER.csv (or override)
    """
    base, _ = os.path.splitext(input_csv)
    folder = os.path.dirname(input_csv)
    # Canonical LP results file:
    lp_path = f"{base}_RESULTS-LP.csv"

    if weather_override:
        weather_path = weather_override
    else:
        weather_path = f"{base}_WEATHER.csv"

    # Normalize to absolute paths to be safe
    lp_path = os.path.abspath(lp_path)
    weather_path = os.path.abspath(weather_path)
    return lp_path, weather_path


def load_load_profile(lp_path: str) -> pd.DataFrame:
    """
    Load the computed load profile results. Must contain a 'datetime' column.
    """
    if not os.path.isfile(lp_path):
        raise FileNotFoundError(f"Load profile results file not found: {lp_path}")
    df = pd.read_csv(lp_path)
    if "datetime" not in df.columns:
        raise ValueError(f"'datetime' column not found in load profile: {lp_path}")
    # Parse to datetime dtype for safe merge
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df


def load_weather(weather_path: str) -> pd.DataFrame:
    """
    Load the weather CSV if available. Return empty DataFrame if missing.
    """
    if not os.path.isfile(weather_path):
        print(f"[WARN] Weather file not found: {weather_path}")
        return pd.DataFrame()

    df = pd.read_csv(weather_path)
    if "datetime" not in df.columns:
        raise ValueError(f"'datetime' column not found in weather file: {weather_path}")
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df


def resample_weather_to_15min(weather: pd.DataFrame) -> pd.DataFrame:
    """
    Resample weather to 15-minute intervals on the 'datetime' column.

    Why bfill then ffill?
    - bfill ensures the very first interval gets a non-null value
      (useful when the first weather datapoint is slightly after the first LP datapoint).
    - ffill ensures gaps afterwards are filled forward.

    Adjust if you have specific rules for precipitation accumulation, etc.
    """
    if weather.empty:
        return weather

    w = weather.copy()
    w = w.sort_values("datetime")
    w = w.set_index("datetime")

    # For numeric weather columns, resampling with bfill() then ffill() is a practical default.
    # If you later add non-numeric columns, pandas will ignore them in these fills.
    w = w.resample("15min").bfill().ffill()

    # Back to a normal column for merging
    w = w.reset_index()
    return w


def merge_frames(load_profile: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    """
    Left-merge weather onto load_profile by exact timestamp match after resampling.
    """
    if weather.empty:
        print("[INFO] No weather data available; returning original load profile unchanged.")
        return load_profile

    # Make sure no duplicate columns sneak in with suffixes;
    # if they do, we'll handle it after merge.
    merged = pd.merge(load_profile, weather, on="datetime", how="left")

    # If any duplicate columns got suffixes (rare with our column names),
    # you could drop them here; for now we trust names are unique.
    return merged


def write_back(lp_path: str, merged: pd.DataFrame) -> None:
    """
    Overwrite the canonical LP results file with the weather-augmented version.
    """
    merged.to_csv(lp_path, index=False)
    print(f"[OK] Weather merged into '{lp_path}'")


def main() -> int:
    args = parse_args()

    try:
        lp_path, weather_path = derive_paths(args.filename, args.weather)
        print(f"[INFO] Load profile: {lp_path}")
        print(f"[INFO] Weather file: {weather_path if args.weather else '(default) ' + weather_path}")

        # Load frames
        load_profile = load_load_profile(lp_path)
        weather = load_weather(weather_path)

        # Resample weather to 15-min, then merge
        weather_15 = resample_weather_to_15min(weather)
        merged = merge_frames(load_profile, weather_15)

        # Write back into {base}_RESULTS-LP.csv for downstream steps
        write_back(lp_path, merged)

        # Optionally delete the weather file
        if not args.keep_weather and os.path.isfile(weather_path) and not weather.empty:
            try:
                os.remove(weather_path)
                print(f"[INFO] Deleted weather file: {weather_path}")
            except Exception as e:
                print(f"[WARN] Failed to delete weather file '{weather_path}': {e}")

        print("[SUCCESS] Merge completed.")
        return 0

    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return 2
    except ValueError as e:
        print(f"[ERROR] {e}")
        return 3
    except Exception as e:
        print(f"[ERROR] Unexpected failure: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
