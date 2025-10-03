import os
import sys
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import argparse
import json

#cd C:\Users\micha\GitHub\load-profile\src
#python lpd-interactive.py ..\sample-data\22meters-736days-1470K_rows.csv --transformer_kva 75 --datetime "2024-10-08 16:45:00"
#python lpd-interactive.py ..\sample-data\OCD226826-700days.csv --transformer_kva 75 --datetime "2024-10-10 16:45:00"

# Load stylesheet
with open("plotly.json", "r") as f:
    style = json.load(f)

def process_csv(input_file):
    base, _ = os.path.splitext(input_file)
    load_profile_file = f"{base}_RESULTS-LP.csv"
    data = pd.read_csv(input_file)
    return data, load_profile_file

def visualize_load_profile_interactive(load_profile_file, transformer_kva, target_datetime):
    try:
        # Load the data
        data = pd.read_csv(load_profile_file)

        # Ensure the necessary columns are present
        if "datetime" not in data.columns or "total_kw" not in data.columns:
            raise ValueError("Required columns 'datetime' and 'total_kw' are not present in the file.")

        # Convert 'datetime' column to datetime type
        data["datetime"] = pd.to_datetime(data["datetime"])

        # Initialize the Plotly figure and apply layout from stylesheet
        fig = go.Figure()
        fig.update_layout(**style["layout"])

        # Add the main load trace
        fig.add_trace(go.Scatter(
            x=data["datetime"],
            y=data["total_kw"],
            **style["traces"]["main_load"]
        ))

        # Check if target_datetime is within the dataset range
        min_datetime = data["datetime"].min()
        max_datetime = data["datetime"].max()

        if target_datetime:
            if target_datetime < min_datetime or target_datetime > max_datetime:
                print(f"Warning: The provided datetime '{target_datetime}' is outside the dataset range ({min_datetime} to {max_datetime}).")
                # Add warning annotation from the stylesheet
                fig.add_annotation(**style["annotations"]["warning"],
                    text=f"Warning: The provided datetime '{target_datetime}' is outside the dataset range ({min_datetime} to {max_datetime})."
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
                    text=f"Target: {closest_datetime.strftime('%Y-%m-%d %H:%M')}<br>{closest_load:.2f} kW"
                )

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
            text=f"Peak: {max_datetime.strftime('%Y-%m-%d %H:%M')}<br>{max_load:.2f} kW"
        )

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
            print(f"Valid datetime provided: {target_datetime}")
        except ValueError:
            print(f"Error: Invalid datetime format '{args.datetime}'. Use 'YYYY-MM-DD HH:MM:SS'.")
            sys.exit(1)

    # Process the load profile CSV file
    try:
        data, load_profile_file = process_csv(input_file)
        print(f"CSV processing complete: {load_profile_file}")
    except Exception as e:
        print(f"Unexpected error processing CSV file '{input_file}': {e}")
        sys.exit(1)

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
