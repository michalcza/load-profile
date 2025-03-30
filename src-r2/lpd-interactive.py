import os
import sys
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import argparse
import json

# Load stylesheet
def load_style(file_path="plotly.json"):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading style: {e}")
        return {}

# Load weather codes from JSON file
def load_weather_codes(file_path="weather-codes.json"):
    try:
        with open(file_path, "r") as file:
            weather_codes = json.load(file)
            return {int(k): v for k, v in weather_codes.items()}
    except Exception as e:
        print(f"Error loading weather codes: {e}")
        return {}

# Translate weather codes to descriptions in DataFrame
def translate_weather_codes(df, weather_codes):
    if "weather_code" in df.columns:
        df["weather_description"] = df["weather_code"].map(weather_codes).fillna("Unknown")
    else:
        df["weather_description"] = "Unknown"
    return df

# Group consecutive identical weather observations
def group_weather_observations(df):
    if "weather_description" in df.columns:
        df["group"] = (df["weather_description"] != df["weather_description"].shift()).cumsum()
        df = df.groupby("group").first().reset_index(drop=True)
    return df

# Load the merged load profile with weather data
def process_csv(input_file):
    base, _ = os.path.splitext(input_file)
    load_profile_file = f"{base}_RESULTS-LP.csv"
    return pd.read_csv(load_profile_file), load_profile_file

# Add traces to the figure
def add_traces(fig, data, style, transformer_kva):
    fig.add_trace(go.Scatter(x=data["datetime"],
    y=data["total_kw"],
    **style["traces"]["main_load"]))
    add_transformer_thresholds(fig, data, transformer_kva, style)
    add_daily_peak_load(fig, data, style)

# Add transformer thresholds
def add_transformer_thresholds(fig, data, transformer_kva, style):
    for pct, key in zip([0.85, 1.0, 1.2], ["85_load", "100_load", "120_load"]):
        load_level = transformer_kva * pct
        fig.add_trace(go.Scatter(x=[data["datetime"].min(),
        data["datetime"].max()],
        y=[load_level, load_level],
        **style["traces"][key]))

# Add daily peak load trace
def add_daily_peak_load(fig, data, style):
    daily_peak = data.loc[data.groupby("date")["total_kw"].idxmax()]
    fig.add_trace(go.Scatter(
        x=daily_peak["datetime"],
        y=daily_peak["total_kw"],
        mode="markers+lines", #mode="markers+lines+text", 
        #text=[f"{kw:.2f} kW" for kw in daily_peak["total_kw"]],
        **{k: v for k, v in style["traces"].get("daily_peak", {}).items() if k != "mode"}
    ))


def add_weather_traces(fig, data, style, show_cloud_cover=True, show_temp_peak=True):
    # Only add cloud cover trace if show_cloud_cover is True
    if show_cloud_cover and "cloud_cover_percent" in data.columns:
        fig.add_trace(go.Scatter(
            x=data["datetime"],
            y=data["cloud_cover_percent"],
            yaxis="y3",
            **style["traces"]["cloud_cover"]
        ))

    # Add temperature peak trace if enabled
    if show_temp_peak and "temperature_f" in data.columns:
        peak_temp_data = data.loc[data.groupby("date")["temperature_f"].idxmax()]
        fig.add_trace(go.Scatter(
            x=peak_temp_data["datetime"],
            y=peak_temp_data["temperature_f"],
            **style["traces"]["temp_peak"]
        ))

# Annotate peak load
def annotate_peak_load(fig, data, style):
    max_row = data.loc[data["total_kw"].idxmax()]
    fig.add_trace(go.Scatter(x=[max_row["datetime"],
    max_row["datetime"]],
    y=[0, max(data["total_kw"])],
    **style["traces"]["peak_load"]))
    fig.add_annotation(x=max_row["datetime"],
    y=max_row["total_kw"],
    **style["annotations"]["peak"],
    text=f"Coincidental Peak:<br>{max_row['datetime'].strftime('%Y-%m-%d %H:%M')}<br>{max_row['total_kw']:.2f} kW")

# Main function to generate interactive load profile visualization
def visualize_load_profile_interactive(load_profile_file, transformer_kva, target_datetime=None):
    try:
        data = pd.read_csv(load_profile_file)
        data["datetime"] = pd.to_datetime(data["datetime"])
        data["date"] = data["datetime"].dt.date
        style = load_style()

        fig = go.Figure()
        fig.update_layout(**style.get("layout", {}))

        add_traces(fig, data, style, transformer_kva)
        add_weather_traces(fig, data, style)
        annotate_peak_load(fig, data, style)
        handle_target_datetime(fig, data, style, target_datetime)

        # Add secondary y-axis for weather data
        fig.update_layout(
            yaxis2=dict(
                title="Temperature (°F)",
                overlaying="y",
                side="right",
                position=1,
                showgrid=False
            ),
            yaxis3=dict(
                title="Cloud Cover (%)",
                overlaying="y",
                side="right",
                position=0.95,
                showgrid=False,
                range=[0, 100]  # Force axis limits between 0 and 100
            )
        )

        fig.show(config={"scrollZoom": True})
    except Exception as e:
        print(f"An error occurred while generating the interactive visualization: {e}")

# Handle target datetime marker
def handle_target_datetime(fig, data, style, target_datetime):
    if target_datetime:
        try:
            target_datetime = pd.to_datetime(target_datetime)
            closest_row = data.iloc[(data['datetime'] - target_datetime).abs().argmin()]
            fig.add_trace(go.Scatter(x=[closest_row['datetime'],
            closest_row['datetime']],
            y=[0, max(data["total_kw"])],
            **style["traces"]["target_datetime"]))
            fig.add_annotation(x=closest_row['datetime'],
            y=closest_row['total_kw'],
            **style["annotations"]["target"],
            text=f"Load at target:<br>{closest_row['datetime'].strftime('%Y-%m-%d %H:%M')}<br>{closest_row['total_kw']:.2f} kW")
        except Exception as e:
            print(f"Error parsing target datetime: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a CSV file for load profile analysis.")
    parser.add_argument("filename", type=str, help="Path to the input CSV file")
    parser.add_argument("--transformer_kva", type=float, default=0, help="Transformer size in kVA")
    parser.add_argument("--datetime", type=str, help="DateTime for total load calculation (format: YYYY-MM-DD HH:MM:SS)")
    args = parser.parse_args()

    input_file = args.filename
    transformer_kva = args.transformer_kva
    target_datetime = args.datetime

    if not os.path.isfile(input_file):
        print(f"Error: File '{input_file}' does not exist.")
        sys.exit(1)

    if target_datetime:
        try:
            target_datetime = datetime.strptime(target_datetime, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print(f"Error: Invalid datetime format '{args.datetime}'. Use 'YYYY-MM-DD HH:MM:SS'.")
            sys.exit(1)

    try:
        data, load_profile_file = process_csv(input_file)
        weather_codes = load_weather_codes("weather-codes.json")
        data = translate_weather_codes(data, weather_codes)
        data = group_weather_observations(data)

        if transformer_kva > 0:
            visualize_load_profile_interactive(load_profile_file, transformer_kva, target_datetime)
        else:
            print("Transformer KVA not specified or is zero. Skipping analysis and visualization.")
    except Exception as e:
        print(f"Unexpected error processing CSV file '{input_file}': {e}")
        sys.exit(1)
