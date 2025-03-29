import os
import sys
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import argparse
import json

# Load stylesheet
with open("plotly.json", "r") as f:
    style = json.load(f)

# Load weather codes from JSON file
def load_weather_codes(file_path="weather-codes.json"):
    """Load weather codes and return as a dictionary."""
    try:
        with open(file_path, "r") as file:
            weather_codes = json.load(file)
            # Convert keys to integers since JSON keys are stored as strings
            return {int(k): v for k, v in weather_codes.items()}
    except Exception as e:
        print(f"Error loading weather codes: {e}")
        return {}

# Translate weather codes to descriptions in DataFrame
def translate_weather_codes(df, weather_codes):
    """Map weather_code to human-readable descriptions."""
    if "weather_code" in df.columns:
        df["weather_description"] = df["weather_code"].map(weather_codes).fillna("Unknown")
    else:
        df["weather_description"] = "Unknown"
    return df

# Group consecutive identical weather observations
def group_weather_observations(df):
    """Group consecutive identical weather descriptions to avoid redundancy."""
    if "weather_description" in df.columns:
        df["group"] = (df["weather_description"] != df["weather_description"].shift()).cumsum()
        grouped_df = df.groupby(["datetime", "group"]).first().reset_index()
        df = grouped_df.drop(columns=["group"])
    return df

# Load the merged load profile with weather data (if available)
def process_csv(input_file):
    base, _ = os.path.splitext(input_file)
    load_profile_file = f"{base}_RESULTS-LP.csv"
    data = pd.read_csv(load_profile_file)
    return data, load_profile_file

# Main function to generate interactive load profile visualization
def visualize_load_profile_interactive(load_profile_file, transformer_kva, target_datetime=None):
    try:
        # Load the data
        data = pd.read_csv(load_profile_file)

        # Ensure the necessary columns are present
        if "datetime" not in data.columns or "total_kw" not in data.columns:
            raise ValueError("Required columns 'datetime' and 'total_kw' are not present in the file.")

        # Convert 'datetime' column to datetime type
        data["datetime"] = pd.to_datetime(data["datetime"])

        # Calculate daily peak load
        data["date"] = data["datetime"].dt.date
        daily_peak = data.loc[data.groupby("date")["total_kw"].idxmax()]

        # Initialize the Plotly figure and apply layout from stylesheet
        fig = go.Figure()
        fig.update_layout(**style["layout"])

        # Add the main load trace
        fig.add_trace(go.Scatter(
            x=data["datetime"],
            y=data["total_kw"],
            **style["traces"]["main_load"],
        ))

        # Check if temperature and cloud cover data is available
        has_temperature = "temperature_f" in data.columns
        has_cloud_cover = "cloud_cover_percent" in data.columns

        # Plot temperature if available using styles from plotly.json
        if has_temperature:
            fig.add_trace(go.Scatter(
                x=data["datetime"],
                y=data["temperature_f"],
                **style["traces"]["temperature"],  # Use plotly.json settings
                yaxis="y2"
            ))

        # Plot cloud cover if available using styles from plotly.json
        if has_cloud_cover:
            fig.add_trace(go.Scatter(
                x=data["datetime"],
                y=data["cloud_cover_percent"],
                **style["traces"]["cloud_cover"],  # Use plotly.json settings
                yaxis="y3"
            ))

        # Check if target_datetime is within the dataset range
        min_datetime = data["datetime"].min()
        max_datetime = data["datetime"].max()

        # Handle target_datetime properly
        if target_datetime:
            try:
                target_datetime = pd.to_datetime(target_datetime)
                if target_datetime < min_datetime or target_datetime > max_datetime:
                    print(f"Warning: The provided datetime '{target_datetime}' is outside the dataset range ({min_datetime} to {max_datetime}).")
                    fig.add_annotation(
                        **style["annotations"]["warning"],
                        text=f"Warning: The provided datetime '{target_datetime}' is outside the dataset range."
                    )
                else:
                    # Add a vertical line and annotation for the target datetime
                    closest_row = data.iloc[(data['datetime'] - target_datetime).abs().argmin()]
                    closest_datetime = closest_row['datetime']
                    closest_load = closest_row['total_kw']

                    fig.add_trace(go.Scatter(
                        x=[closest_datetime, closest_datetime],
                        y=[0, max(data["total_kw"])],
                        **style["traces"]["target_datetime"]
                    ))

                    fig.add_annotation(
                        x=closest_datetime,
                        y=closest_load,
                        **style["annotations"]["target"],
                        text=f"Load at target:<br>{closest_datetime.strftime('%Y-%m-%d %H:%M')}<br>{closest_load:.2f} kW"
                    )
            except Exception as e:
                print(f"Error parsing target datetime: {e}")
                target_datetime = None

        # Add transformer threshold traces
        load_85 = transformer_kva * 0.85
        load_100 = transformer_kva
        load_120 = transformer_kva * 1.2

        fig.add_trace(go.Scatter(
            x=[data["datetime"].min(), data["datetime"].max()],
            y=[load_85, load_85],
            **style["traces"]["85_load"]
        ))

        fig.add_trace(go.Scatter(
            x=[data["datetime"].min(), data["datetime"].max()],
            y=[load_100, load_100],
            **style["traces"]["100_load"]
        ))

        fig.add_trace(go.Scatter(
            x=[data["datetime"].min(), data["datetime"].max()],
            y=[load_120, load_120],
            **style["traces"]["120_load"]
        ))

        # Add daily peak line to the visualization using styles from plotly.json
        fig.add_trace(go.Scatter(
            x=daily_peak["datetime"],
            y=daily_peak["total_kw"],
            text=[f"{kw:.2f} kW" for kw in daily_peak["total_kw"]],
            **style["traces"]["daily_peak"]
        ))

        # Annotate the maximum load value
        max_row = data.loc[data["total_kw"].idxmax()]
        max_datetime = max_row["datetime"]
        max_load = max_row["total_kw"]

        fig.add_trace(go.Scatter(
            x=[max_datetime, max_datetime],
            y=[0, max(data["total_kw"])],
            **style["traces"]["peak_load"]
        ))

        fig.add_annotation(
            x=max_datetime,
            y=max_load,
            **style["annotations"]["peak"],
            text=f"Coincidental Peak:<br>{max_datetime.strftime('%Y-%m-%d %H:%M')}<br>{max_load:.2f} kW"
        )

        # Update layout for secondary y-axis if data is available
        yaxis_layout = dict(
            title="Load (kW)",
            side="left",
            showgrid=True
        )
        layout_update = {"yaxis": yaxis_layout}

        # Add secondary y-axis for weather data (temperature or cloud cover)
        if has_temperature or has_cloud_cover:
            layout_update["yaxis2"] = dict(
                title="Weather Data",
                overlaying="y",
                side="right",
                range=[-10, 120],
                showgrid=False,
                zeroline=False
            )

        # Add third y-axis only if cloud cover is available (if separate axis is needed)
        if has_cloud_cover:
            layout_update["yaxis3"] = dict(
                title="Cloud Cover (%)",
                overlaying="y",
                side="right",
                range=[-10, 120],
                showgrid=False,
                zeroline=False
            )

        # Add weather description as text annotations if available
        if "weather_description" in data.columns:
            fig.add_trace(go.Scatter(
                x=data["datetime"],
                y=[120] * len(data),
                text=data["weather_description"],
                mode="text",
                textposition="top right",
                **style["traces"]["weather_description"]
            ))

        fig.update_layout(**layout_update)

        # Show the figure
        fig.show(config={"scrollZoom": True})

    except Exception as e:
        print(f"An error occurred while generating the interactive visualization: {e}")


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process a CSV file for load profile analysis.")
    parser.add_argument("filename", type=str, help="Path to the input CSV file")
    parser.add_argument("--transformer_kva", type=float, default=0, help="Transformer size in kVA")
    parser.add_argument("--datetime", type=str, help="DateTime for total load calculation (format: YYYY-MM-DD HH:MM:SS)")
    args = parser.parse_args()

    # Create variables from arguments
    input_file = args.filename
    transformer_kva = args.transformer_kva
    target_datetime = args.datetime

    # Validate file existence
    if not os.path.isfile(input_file):
        print(f"Error: File '{input_file}' does not exist.")
        sys.exit(1)

    # Validate datetime argument
    if target_datetime:
        try:
            target_datetime = datetime.strptime(target_datetime, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print(f"Error: Invalid datetime format '{args.datetime}'. Use 'YYYY-MM-DD HH:MM:SS'.")
            sys.exit(1)
    else:
        target_datetime = None

    # Process the load profile CSV file
    try:
        data, load_profile_file = process_csv(input_file)
    except Exception as e:
        print(f"Unexpected error processing CSV file '{input_file}': {e}")
        sys.exit(1)

    # Load and process weather codes
    weather_codes = load_weather_codes("weather-codes.json")

    # Translate weather codes and group consecutive observations
    data = translate_weather_codes(data, weather_codes)
    data = group_weather_observations(data)

    # Transformer load analysis and visualization
    if transformer_kva > 0:
        try:
            visualize_load_profile_interactive(load_profile_file, transformer_kva, target_datetime)
        except FileNotFoundError:
            print(f"Error: The file '{load_profile_file}' was not found.")
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error during transformer load analysis or visualization: {e}")
            sys.exit(1)
    else:
        print("Transformer KVA not specified or is zero. Skipping analysis and visualization.")
