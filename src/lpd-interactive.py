import os
import sys
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import argparse

#cd C:\Users\micha\GitHub\load-profile\src
#python lpd-interactive.py ..\sample-data\22meters-736days-1470K_rows.csv --transformer_kva 75 --datetime "2024-10-08 16:45:00"
#python lpd-interactive.py ..\sample-data\OCD226826-700days.csv --transformer_kva 75 --datetime "2024-10-10 16:45:00"
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

        # Initialize the Plotly figure
        fig = go.Figure()

        # Add the main load trace
        fig.add_trace(go.Scatter(
            x=data["datetime"],
            y=data["total_kw"],
            mode='lines',
            line=dict(color='lightgrey', dash='solid', width=1),
            name='Load (kW)'
        ))

        # Check if target_datetime is within the dataset range
        min_datetime = data["datetime"].min()
        max_datetime = data["datetime"].max()

        if target_datetime:
            if target_datetime < min_datetime or target_datetime > max_datetime:
                print(f"Warning: The provided datetime '{target_datetime}' is outside the dataset range ({min_datetime} to {max_datetime}).")
                # Add warning annotation
                fig.add_annotation(
                    xref="paper", yref="paper",
                    x=0.5, y=1.05,
                    text=f"Warning: The provided datetime '{target_datetime}' is outside the dataset range ({min_datetime} to {max_datetime}).",
                    showarrow=False,
                    font=dict(size=14, color="red"),
                    align="center",
                    bgcolor="yellow",
                    bordercolor="red",
                    borderwidth=2
                )
            else:
                # Add a vertical line and annotation for the target datetime
                closest_row = data.iloc[(data['datetime'] - target_datetime).abs().argmin()]
                closest_datetime = closest_row['datetime']
                closest_load = closest_row['total_kw']

                fig.add_trace(go.Scatter(
                    x=[closest_datetime, closest_datetime],
                    y=[0, max(data["total_kw"])],
                    mode='lines',
                    line=dict(color='blue', dash='solid', width=2),
                    name='Target Datetime'
                ))

                fig.add_annotation(
                    x=closest_datetime,
                    y=closest_load,
                    text=f"Target: {closest_datetime.strftime('%Y-%m-%d %H:%M:%S')}<br>{closest_load:.2f} kW",
                    showarrow=True,
                    arrowhead=5,
                    arrowcolor='blue',
                    font=dict(size=12, color="blue"),
                    bgcolor="lightgray",
                    bordercolor="blue",
                    borderwidth=1
                )

        # Add transformer threshold traces
        load_85 = transformer_kva * 0.85
        load_100 = transformer_kva
        load_120 = transformer_kva * 1.2

        fig.add_trace(go.Scatter(
            x=[data["datetime"].min(), data["datetime"].max()],
            y=[load_85, load_85],
            mode='lines',
            line=dict(color='green', dash='dash', width=2),
            name='85% Load'
        ))

        fig.add_trace(go.Scatter(
            x=[data["datetime"].min(), data["datetime"].max()],
            y=[load_100, load_100],
            mode='lines',
            line=dict(color='orange', dash='dash', width=2),
            name='100% Load'
        ))

        fig.add_trace(go.Scatter(
            x=[data["datetime"].min(), data["datetime"].max()],
            y=[load_120, load_120],
            mode='lines',
            line=dict(color='red', dash='dash', width=2),
            name='120% Load'
        ))

        # Annotate the maximum load value
        max_row = data.loc[data["total_kw"].idxmax()]
        max_datetime = max_row["datetime"]
        max_load = max_row["total_kw"]

        fig.add_trace(go.Scatter(
            x=[max_datetime, max_datetime],
            y=[0, max(data["total_kw"])],
            mode='lines',
            line=dict(color='red', dash='solid', width=2),
            name='Max Load'
        ))

        fig.add_annotation(
            x=max_datetime,
            y=max_load,
            text=f"Peak: {max_datetime.strftime('%Y-%m-%d %H:%M:%S')}<br>{max_load:.2f} kW",
            showarrow=True,
            arrowhead=5,
            arrowcolor='red',
            font=dict(size=12, color="red"),
            bgcolor="lightgray",
            bordercolor="blue",
            borderwidth=1
        )

        # Customize layout and enable scroll zoom
        fig.update_layout(
            title="Time-Based Load Profile Visualization",
            xaxis_title="Time<br>(Roll to zoom)",
            yaxis_title="Load (kW)<br>(Roll to zoom)",
            legend_title=dict(text="Legend<br>Click to toggle traces"),
            hovermode="x",
            template="plotly_white",
            dragmode="pan"
        )

        fig.show(config={"scrollZoom": True})
    except Exception as e:
        print(f"An error occurred while generating the interactive visualization: {e}")

def add_main_traces(fig, data, transformer_kva):
    # Define thresholds
    load_85 = transformer_kva * 0.85
    load_100 = transformer_kva
    load_120 = transformer_kva * 1.2

    # Add the main load trace
    fig.add_trace(go.Scatter(
        x=data["datetime"],
        y=data["total_kw"],
        mode='lines',
        name='Load (kW)',
        line=dict(color='lightgrey', dash='solid', width=1),
    ))

    # Add horizontal threshold traces
    fig.add_trace(go.Scatter(
        x=[data["datetime"].min(), data["datetime"].max()],
        y=[load_85, load_85],
        mode='lines',
        line=dict(color='green', dash='dash', width=2),
        name='85% Load'
    ))
    fig.add_trace(go.Scatter(
        x=[data["datetime"].min(), data["datetime"].max()],
        y=[load_100, load_100],
        mode='lines',
        line=dict(color='orange', dash='dash', width=2),
        name='100% Load'
    ))
    fig.add_trace(go.Scatter(
        x=[data["datetime"].min(), data["datetime"].max()],
        y=[load_120, load_120],
        mode='lines',
        line=dict(color='red', dash='dash', width=2),
        name='120% Load'
    ))

def handle_target_datetime(fig, data, target_datetime):
    min_datetime = data["datetime"].min()
    max_datetime = data["datetime"].max()

    if target_datetime < min_datetime or target_datetime > max_datetime:
        print(f"Warning: The provided datetime '{target_datetime}' is outside the dataset range ({min_datetime} to {max_datetime}).")
        add_warning_annotation(fig, target_datetime, min_datetime, max_datetime)
    else:
        add_target_annotation(fig, data, target_datetime)

def add_warning_annotation(fig, target_datetime, min_datetime, max_datetime):
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.5, y=1.05,
        text=f"Warning: The provided datetime '{target_datetime}' is outside the dataset range ({min_datetime} to {max_datetime}).",
        showarrow=False,
        font=dict(size=14, color="red"),
        align="center",
        bgcolor="yellow",
        bordercolor="red",
        borderwidth=2
    )

def add_target_annotation(fig, data, target_datetime):
    closest_row = data.iloc[(data['datetime'] - target_datetime).abs().argmin()]
    closest_datetime = closest_row['datetime']
    closest_load = closest_row['total_kw']

    # Add a vertical line to target annotation 
    fig.add_trace(go.Scatter(
        x=[closest_datetime, closest_datetime],
        y=[0, max(data['total_kw'])],
        mode='lines',
        line=dict(color='blue', dash='solid', width=2),
        name='Target Datetime'
    ))

    fig.add_annotation(
        x=closest_datetime,
        y=closest_load,
        text=f"Target: {closest_datetime.strftime('%Y-%m-%d %H:%M:%S')}<br>{closest_load:.2f} kW",
        showarrow=True,
        arrowhead=8,
        arrowcolor='blue',
        font=dict(size=12, color="blue"),
        bgcolor="lightgray",
        bordercolor="blue",
        borderwidth=1
    )
    
def add_peak_annotation(fig, data):
    # Find the peak load in the dataset
    max_row = data.loc[data['total_kw'].idxmax()]
    max_datetime = max_row['datetime']
    max_load = max_row['total_kw']

    # Add a vertical line at the peak load datetime
    fig.add_trace(go.Scatter(
        x=[max_datetime, max_datetime],
        y=[0, max(data['total_kw'])],
        mode='lines',
        line=dict(color='purple', dash='dot', width=2),
        name='Peak Load'
    ))

    # Add an annotation for the peak load
    fig.add_annotation(
        x=max_datetime,
        y=max_load,
        text=f"Peak: {max_datetime.strftime('%Y-%m-%d %H:%M:%S')}<br>{max_load:.2f} kW",
        showarrow=True,
        arrowhead=8,
        arrowcolor='purple',
        font=dict(size=12, color="purple"),
        bgcolor="lightgray",
        bordercolor="purple",
        borderwidth=1
    )

def finalize_plot(fig):
    fig.update_layout(
        title="Time-Based Load Profile Visualization",
        xaxis_title="Time",
        yaxis_title="Load (kW)",
        legend_title=dict(
            text="Legend<br>Click to toggle traces"
        ),
        hovermode="x",
        template="plotly_white",
        dragmode="pan",  # Enable panning 'zoom' is also an option.
        meta=dict(locale="en"),  # Set locale explicitly
        margin=dict(l=50, r=50, t=150, b=50),  # Adjust margins for annotations
    )
    print("Final configuration:", {"scrollZoom": True}),
    fig.show(config={"scrollZoom": True})

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