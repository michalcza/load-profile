import os
import sys
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import argparse

# def process_csv(input_file):
    # """
    # Placeholder for CSV processing logic.
    # Returns the processed data and output file name.
    # """
    # base, _ = os.path.splitext(input_file)
    # load_profile_file = f"{base}_RESULTS-LP.csv"
    # Mocking data processing; replace with actual logic.
    # data = pd.read_csv(input_file)
    # data.to_csv(load_profile_file, index=False)
    # return data, load_profile_file

def visualize_load_profile_interactive(load_profile_file, transformer_kva):
    """
    Generates an interactive time-based plot using Plotly with load thresholds.
    """
    try:
        # Load the data
        data = pd.read_csv(load_profile_file)

        # Ensure the necessary columns are present
        if "datetime" in data.columns and "total_kw" in data.columns:
            # Convert 'datetime' column to datetime type
            data["datetime"] = pd.to_datetime(data["datetime"])

            # Define thresholds for 85%, 100%, and 120% of transformer load
            load_85 = transformer_kva * 0.85
            load_100 = transformer_kva
            load_120 = transformer_kva * 1.2

            # Create a Plotly figure
            fig = go.Figure()

            # Add the main load trace
            fig.add_trace(go.Scatter(
                x=data["datetime"],
                y=data["total_kw"],
                mode='lines',
                name='Load (kW)'
            ))

            # Add horizontal threshold traces
            fig.add_trace(go.Scatter(
                x=[data["datetime"].min(), data["datetime"].max()],
                y=[load_85, load_85],
                mode='lines',
                line=dict(color='orange', dash='dash'),
                name='85% Load'
            ))
            fig.add_trace(go.Scatter(
                x=[data["datetime"].min(), data["datetime"].max()],
                y=[load_100, load_100],
                mode='lines',
                line=dict(color='green', dash='dash'),
                name='100% Load'
            ))
            fig.add_trace(go.Scatter(
                x=[data["datetime"].min(), data["datetime"].max()],
                y=[load_120, load_120],
                mode='lines',
                line=dict(color='red', dash='dash'),
                name='120% Load'
            ))

            # Customize layout
            fig.update_layout(
                title="Time-Based Load Profile Visualization",
                xaxis_title="Time",
                yaxis_title="Load (kW)",
                legend_title="Legend",
                hovermode="x",
                template="plotly_white"
            )

            # Show the interactive plot
            fig.show()
        else:
            print("Error: Required columns 'datetime' and 'total_kw' are not present in the file.")
    except Exception as e:
        print(f"An error occurred while generating the interactive visualization: {e}")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process a CSV file for load profile analysis.")
    parser.add_argument("filename", type=str, help="Path to the input CSV file")
    parser.add_argument("--transformer_kva", type=float, default=0, help="Transformer size in kVA")
    parser.add_argument("--datetime", type=str, help="DateTime for total load calculation (format: YYYY-MM-DD HH:MM:SS)")
    args = parser.parse_args()

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

    # Process the CSV file
    try:
        data, load_profile_file = process_csv(input_file)
        print(f"CSV processing complete. Output file: {load_profile_file}")
    except Exception as e:
        print(f"Unexpected error processing CSV file '{input_file}': {e}")
        sys.exit(1)

    # Transformer load analysis and visualization
    if transformer_kva > 0:
        try:
            visualize_load_profile_interactive(load_profile_file, transformer_kva)
        except FileNotFoundError:
            print(f"Error: The file '{load_profile_file}' was not found.")
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error during transformer load analysis or visualization: {e}")
            sys.exit(1)
    else:
        print("Transformer KVA not specified or is zero. Skipping analysis and visualization.")
