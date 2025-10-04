#!/usr/bin/env python3
"""
Merge weather onto the load profile CSV (…_RESULTS-LP.csv).

Usage:
  python lpd-merge.py path/to/FOO_RESULTS-LP.csv [--weather path/to/FOO_WEATHER.csv] [--keep-weather]

Notes:
- If --weather is omitted, we derive it by replacing _RESULTS-LP.csv -> _WEATHER.csv.
- We perform a nearest-time merge (asof) with 31-minute tolerance to map hourly weather to 15-min points.
- Writes the merged columns back into the same _RESULTS-LP.csv.
"""

import argparse
import os
import sys
import pandas as pd

def read_lp(lp_csv: str) -> pd.DataFrame:
    if not os.path.isfile(lp_csv):
        raise FileNotFoundError(f"Load profile not found: {lp_csv}")
    df = pd.read_csv(lp_csv)
    if "datetime" not in df.columns:
        raise ValueError("Expected 'datetime' column in load profile CSV.")
    # Normalize datetime (naive)
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime"]).sort_values("datetime").reset_index(drop=True)
    return df

def read_weather(weather_csv: str) -> pd.DataFrame:
    if not os.path.isfile(weather_csv):
        raise FileNotFoundError(f"Weather file not found: {weather_csv}")
    wf = pd.read_csv(weather_csv)
    # Open-Meteo exports 'time' column; normalize to 'datetime'
    time_col = "datetime" if "datetime" in wf.columns else ("time" if "time" in wf.columns else None)
    if not time_col:
        raise ValueError("Weather CSV must have 'time' or 'datetime' column.")
    wf["datetime"] = pd.to_datetime(wf[time_col], errors="coerce")
    wf = wf.dropna(subset=["datetime"]).sort_values("datetime").reset_index(drop=True)

    # Standardize column names to what the interactive plot expects
    rename_map = {
        "temperature_2m": "temperature_f",     # already Fahrenheit if you requested units=fahrenheit
        "precipitation": "precipitation_in",   # already inches if units=inch
        "cloudcover": "cloud_cover_percent",
        "sunshine_duration": "sunshine_duration_s",
        # keep 'weathercode' as-is unless you map to text; numeric is fine to carry along:
        # "weathercode": "weather_code",
    }
    wf = wf.rename(columns=rename_map)

    # Keep only columns we want to merge (and 'datetime')
    cols_keep = ["datetime"]
    for c in ("temperature_f", "precipitation_in", "cloud_cover_percent", "sunshine_duration_s", "weathercode"):
        if c in wf.columns:
            cols_keep.append(c)
    wf = wf[cols_keep]
    return wf

def merge_weather(lp: pd.DataFrame, wf: pd.DataFrame) -> pd.DataFrame:
    # Ensure sorted by time for asof merge
    lp = lp.sort_values("datetime").reset_index(drop=True)
    wf = wf.sort_values("datetime").reset_index(drop=True)

    # Use nearest merge with a 31-minute tolerance (covers 15-min bins to hourly weather)
    merged = pd.merge_asof(
        lp, wf,
        on="datetime",
        direction="nearest",
        tolerance=pd.Timedelta(minutes=31),
    )
    return merged

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lp_csv", help="Path to ..._RESULTS-LP.csv")
    ap.add_argument("--weather", help="Path to ..._WEATHER.csv (optional)")
    ap.add_argument("--keep-weather", action="store_true", help="Do not delete weather CSV after merge")
    args = ap.parse_args()

    lp_csv = os.path.abspath(args.lp_csv)
    if not args.weather:
        root, name = os.path.split(lp_csv)
        base = name.replace("_RESULTS-LP.csv", "")
        weather_csv = os.path.join(root, f"{base}_WEATHER.csv")
    else:
        weather_csv = os.path.abspath(args.weather)

    print(f"[INFO] Load profile: {lp_csv}")
    print(f"[INFO] Weather file: {weather_csv if os.path.exists(weather_csv) else '(missing)'}")

    lp = read_lp(lp_csv)
    print(f"[DEBUG] LP rows: {len(lp)}  cols: {len(lp.columns)}")
    print("[DEBUG] LP columns:", list(lp.columns))
    print(lp.head(2).to_string(index=False))

    wf = read_weather(weather_csv)
    print(f"[DEBUG] WX rows: {len(wf)}  cols: {len(wf.columns)}")
    print("[DEBUG] WX columns:", list(wf.columns))
    print(wf.head(2).to_string(index=False))

    merged = merge_weather(lp, wf)

    # Track which new columns were added
    new_cols = [c for c in merged.columns if c not in lp.columns]
    print("[INFO] New weather columns added:", new_cols if new_cols else "(none)")

    # Fail loudly if we added nothing; this helps diagnose key misalignment
    if not new_cols:
        print("[WARN] No weather columns were merged. Check timestamps/units/column names.")
        # Still write back the LP so pipeline doesn't break, but raise exit code 2 for visibility
        merged.to_csv(lp_csv, index=False)
        sys.exit(2)

    merged.to_csv(lp_csv, index=False)
    print(f"[OK] Weather merged into '{lp_csv}'")

    if not args.keep_weather and os.path.exists(weather_csv):
        try:
            os.remove(weather_csv)
            print(f"[INFO] Deleted weather file: {weather_csv}")
        except Exception as e:
            print(f"[WARN] Could not delete weather file: {e}")

    print("[SUCCESS] Merge completed.")

if __name__ == "__main__":
    main()
